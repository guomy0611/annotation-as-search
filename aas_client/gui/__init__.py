from flask import (
    Flask,
    render_template,
    url_for,
    request,
    flash,
    redirect,
    session
    )

from werkzeug.utils import secure_filename
#secure_filename("My cool movie.mov") = 'My_cool_movie.mov'

import sys
import os
import argparse
import socket
from random import shuffle
import json

from aas_client.common import (
    encode_message,
    decode_message,
    pack_message
    )
from aas_client.generate_dot_tree import generate_dot_tree
from helper import generate_sentence, get_subcatframe, save_result



# define global read-only variables to make flask work
# flask typical app variables and definitions
app = Flask(__name__)
ALLOWED_EXTENSIONS = set(['conll', 'conll09', 'conll06', 'conllu'])
app.config['SECRET_KEY'] = 'jqUNf8?B\8d&(teVZq,~'
# folder to save files to be annotated
UPLOAD_FOLDER = 'loadedFiles'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# define socket to send data
socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# taken from server.py
def update_config(config, new_pairs):
    """
    Update the config dict (conll-formats) with the key-value-pairs in new_data.

    Args:
        config: The current configuration dict.
        new_pairs: A dict or an argparse.Namespace containing the
            key-value-pairs that are to be inserted. In the case of a
            namespace, only names not starting with an underscore are added to
            the config. If a vale is None, the pair is ignored.
    """
    if isinstance(new_pairs, dict):
        config.update({k: v for k, v in new_pairs.items() if v is not None})
    elif isinstance(new_pairs, argparse.Namespace):
        for key in dir(new_pairs):
            if not key.startswith('_'):
                value = getattr(new_pairs, key)
                if value is not None:
                    config[key] = value
    else:
        msg = '{} is neither a dict nor an argparse.Namespace.'
        raise TypeError(msg.format(new_pairs))

# taken from server.py
def read_configfile(configfile):
    """
    Read a json-formatted configuration file and return the resulting dict.
    """
    try:
        return json.load(open(configfile))
    except FileNotFoundError as e:
        return dict()

def get_conll_formats(formats, format_aliases):
    """ Save information about conll-formats in a dictionary.

    Store conll-information in a dictionary. Each entry has the form
    conll_formats[format] = all information  in config regarding this format.
    Each format-alias is given the same information as the original as value.
    If this information is not given in the config, the name of the original
    is taken as value.

    Args:
        formats: The formats-dict specified in the config.
        format_aliases: The format_aliases dict specified in the config.
    Returns a dict containing all conll-formats and the specification needed to
    start the AaS-server.
    """
    conll_formats = formats
    for alias in format_aliases.keys():
        if format_aliases[alias] in conll_formats.keys():
            conll_formats[alias] = conll_formats[format_aliases[alias]]
        else:
            conll_formats[alias] = format_aliases[alias]
    return conll_formats

@app.route('/')
def homepage():
    """ render startpage and remove request-information of previous annotation """
    if 'requests' in session.keys():
        session.pop('requests')
    return render_template('index.html')

@app.route('/exit/', methods = ['POST', 'GET'])
def close_annotator():
    """ Render exit page, remove all created files from storage and close server """
    if request.method == 'POST':
        if request.form['closeApplication']:
            if os.path.isfile('static/annotated_sentence.conll09'):
                os.remove('static/annotated_sentence.conll09')
            if os.path.exists(UPLOAD_FOLDER):
                [os.remove(UPLOAD_FOLDER + '/' + f) for f in os.listdir(UPLOAD_FOLDER)]
                os.rmdir(UPLOAD_FOLDER)
            return redirect(url_for('end_server'))
    return render_template('exit.html')

@app.route('/contact/')
def contact():
    """ Render contactpage and randomize order of displayed information"""
    authors = ['Michael Staniek', 'Rebekka Hubert', 'Simon Will']
    shuffle(authors)
    return render_template('contact.html',
                            author1=authors[0],
                            author2=authors[1],
                            author3=authors[2]
                            )

@app.route('/about/')
def about():
    """ Display about-page to show project information"""
    return render_template('about.html')

@app.route('/save_file/', methods = ['POST', 'GET'])
def saveFile():
   """ Show option to download the annotated sentences """
   return render_template('save_file.html')

# only use this when running with Flasks default server
def end_application():
    """ create a request to shut werkzeug-server down and send it """
    app_end = request.environ.get('werkzeug.server.shutdown')
    app_end()

@app.route('/end_server', methods = ['GET'])
def end_server():
    """ Shutdown Flask-server by sending a shutdown request to the Flask-sever """
    end_application()
    socket_to_server.close()
    return 'Ending AaS-GUI...'

@app.route('/choose_input', methods=['GET','POST'])
def choose_input():
    """ Show input page """
    return render_template('choose.html')

@app.route('/input_sentence', methods=['GET', 'POST'])
def input_sentence():
    """ Get a raw sentence and create a question process """
    if request.method == 'POST':
        if request.form['sentence']:
            requests = request_creator((request.form['sentence'],
                                        request.form['format_sentence'],
                                        'sentence')
                                        )
            session['requests'] = requests
            sentence = request.form['sentence']
            session['sentence'] = sentence
            session['sentence_format'] = request.form['format_sentence']
            return redirect(url_for('annotate'))
    return render_template('input.html')

@app.route('/load_file', methods=['GET', 'POST'])
def load_file():
    """
        load the given forest file and create a forest-request

    """
    if request.method == 'POST':
        if request.files:
            data_file = request.files['file']
            if data_file.filename == '':
                flash('No file selected')
                return redirect(url_for('choose_input'))

            if allowed_file(data_file.filename):
                data = secure_filename(data_file.filename) # ->the file name saved on the server
                session['input_file'] = data
                # create folder for uploaded files if one does not exist yet
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
                data_file.save(os.path.join(app.config['UPLOAD_FOLDER'], data)) #->save the file on server


                # session['requests'] = data, request.form['forest_format'], 'forest'
                #                     #('input.conll09', 'conll09_gold','forest')

                # sentence = generate_sentence(
                #             open(UPLOAD_FOLDER +'/' + data).read()
                #             )

                session['format_name'] = request.form['forest_format']
                session['sentence_format'] = conll_formats[request.form['forest_format']] #(format_name,format_json)
                session['conll_strings'] = [conll_str for conll_str in open(UPLOAD_FOLDER + '/' + data).read().split('\n\n\n')]
                session['sentences'] = [generate_sentence(conll_str) for conll_str in session['conll_strings']]  # ->list of raw sentence
                session['subcats'] = [get_subcatframe(conll_str) for conll_str in session['conll_strings']] # ->list of subcatframes

                return redirect(url_for('check_subcat'))

            else:
                flash('File format is not allowed')
                return redirect(url_for('choose_input'))
    return render_template('load_file.html')


@app.route('/subcatframe')
def check_subcat():
    sentence = session['sentences'][0]
    print(sentence)
    print(session['subcats'])
    subcat = session['subcats'][0] #e.g.('badet', '(subj,obj)')
    subcat = '{}{}'.format(subcat[1],subcat[2])
    return render_template('subcat.html',
                           sentence=sentence,
                           subcat=subcat
                           )

@app.route('/annotate', methods = ['GET', 'POST'])
def annotate():
    """ Start and continue annotation loop.

    Send current question to the AaS-Server, then receive and visualise the
    answer of the server. Display best tree and the received question.

    Returns a html-page containing the best tree, current question and optional answers
    if server sent an error:
        Returns error-html-page
    """

    print('anno')
    print(session['subcats'])
    if len(session.keys()) == 0:
        return redirect(url_for('no_cookies_set'))

    if 'requests' not in session.keys():
        requests = request_creator2()  # the start of a sentence annotation

    else:
        requests = session['requests']



    socket_to_server.send(pack_message(encode_message(requests)))
    received_message = decode_message(receive_message(socket_to_server))
    sentence_visual = visualise(received_message)

    if sentence_visual == 'Parser was not found.':
        return render_template('parser_not_found.html')

    if 'question' in received_message:

        session['question'] = received_message['question']
        question = "Does " + session['question']['dependent'] + " depend on " \
                    + session['question']['head'] + " (relationtype: "  \
                    + session['question']['relation_type'] + ", relation: " \
                    + session['question']['relation'] + ")?"

        sentence = session['sentences'][0]

        return render_template('visualised_tree_dot.html',
                                question=question,
                                sentence=sentence,
                                sentence_visual=sentence_visual
                                )


    elif 'error' in received_message:
        return render_template('error.html')

    session.pop('requests') #clear the request for the next sentence to annotate
    session['conll_strings'].pop(0)
    session["sentences"].pop(0)

    #the right tree nodes
    session['solution'] = received_message['tree']['nodes']
    return render_template('visualised_tree_final.html',
                            sentence_visual = sentence_visual,
                            sentence_conll = handle_solution(received_message),
                            message = received_message
                            )


@app.route('/endResult', methods=['GET', 'POST'])
def annotation_finished():
    """ Display final tree and optional user actions

    Visualize remaining tree or in case of previous aborting best tree and show it.
    Display tree (conll-format) in a textbox with the option to change it. Display
    possilble user actions 'Save' and 'Visualize'.

    Returns html-page containig visualised tree, question and user options
    """
    try:
        if request.method == 'POST':
            answer = request.form['answer']
            if answer == 'Save':
                file_ = 'annotated_' + session['input_file']
                file = os.path.join(os.path.dirname(__file__), file_) #@TODO decide where to save the files,  and download files and don't remove the file? + stylesheet
                save_result(session['solution'], session['subcat_archive'], file)

            # elif answer == 'Visualise':
            #     tree_sentence = request.form['sentence']
            #     message = session['message']
            #     message['tree']['nodes'] = [tree.split('\t')    \
            #                                 for tree in tree_sentence.split('\n')]
            #     return render_template('visualised_tree_final.html',
            #                             sentence_visual = visualise(message),
            #                             sentence_conll = tree_sentence
            #                             )
    except KeyError:
        return redirect(url_for('no_cookies_set'))
    except FileNotFoundError:
        return redirect(url_for('wrong_folder'))

    if len(session["conll_strings"]) > 0:
        return redirect(url_for('check_subcat'))
    else:
        return redirect(url_for('homepage'))





@app.route('/wrong_folder')
def wrong_folder():
    """ Display this page if current working directory is not aas_client """
    return render_template('folder.html')

@app.errorhandler(404)
def page_not_found(e):
    """ Catch 404 error and render costumized template"""
    return render_template('404.html')

@app.route('/noCookies')
def no_cookies_set():
    """ Catch session[key] error and render costumized, helpful template """
    return render_template('cookies.html')

@app.route('/follow_instructions')
def follow_instructions():
    """ Catch NameError if user tries to skip annotationprocess """
    return render_template('instructions.html')

def request_creator(requests):
    """ Create first request to start annotation-loop
    Creates either a forest or a sentence request
    Arguments:
        requests: tuple consisting of:
                    sentence or filename,
                    conll-format,
                    nothing or key-word forest to choose correct request

                    looks like: session['requests'] = data, request.form['forest_format'], 'forest'
    Returns a json-like dictionary
    """
    #a forest request
    if requests[2] == 'forest':
        #data = open(UPLOAD_FOLDER +'/' + requests[0]).read()
        data = session['conll_strings'][0]
        session['conll_strings'].pop(0)
        session["sentences"].pop(0)

        session['sentence_format'] = conll_formats[requests[1]]   #the format json        ?????
                                                                  # {
                                                                  #   "name": "conll09_gold",
                                                                  #   "id": 0,
                                                                  #   "form": 1,
                                                                  #   "label": 4,
                                                                  #   "label_type": "pos",
                                                                  #   "head": 8,
                                                                  #   "relation": 10,
                                                                  #   "relation_type": "deprel"}
        return {
            'type': 'request',
            'use_forest': data, #the raw conll forest string
            'forest_format': requests[1]
            }

    #a sentence request (ignore for now)
    else:
        return {
            'type': 'request',
            'process': requests[0],
            'source_format': 'raw',
            'target_format': requests[1]
            }

def request_creator2():

    # session['conll_strings'].pop(0)
    # session["sentences"].pop(0)

    request = {
        'type': 'request',
        'use_forest': session['conll_strings'][0],  # the raw conll forest string
        'forest_format': session['format_name']
    }
    return request


def allowed_file(filename):
    """ Check if file has an extension specified in global allowed extensions """
    return '.' in filename and \
            filename.split('.')[-1].lower() in  ALLOWED_EXTENSIONS


def inspect_message_buffer(message_buffer):
    """
    Check if a message buffer contains a complete prefix indicating
    the length of the message. If so, return the index of the null byte
    separating the length indication from the payload and return the
    indicated length of the message.
    """
    try:
        separator_index = message_buffer.index(0)
    except ValueError as e:
        # No null byte in message. Wait for more data in buffer.
        return None, None

    message_length_part = message_buffer[0:separator_index]

    try:
        message_length = int(message_length_part.decode())
    except ValueError as e:
        # Message length cannot be converted to int.
        raise ValueError('Message buffer does not start with a message length.')

    return separator_index, message_length

def receive_message(socket, buffersize=1024):
    """
    Read data from the given socket until a full message is received.
    Return the message as a bytestring.
    If there is more than one message in the message buffer the global
    message_buffer will hold the rest.
    """
    global message_buffer
    if 'message_buffer' not in globals():
        message_buffer = b''

    binary_message = b''
    while not binary_message:
        # Loop until a full message is in the message buffer.
        separator_index, message_length = inspect_message_buffer(message_buffer)
        if (separator_index is not None
            and len(message_buffer) > message_length + separator_index):
            # Entire message is in buffer and ready to be read.
            inclusive_start = separator_index + 1
            exclusive_end = separator_index + 1 + message_length
            binary_message = message_buffer[inclusive_start:exclusive_end]
            message_buffer = message_buffer[exclusive_end:]
        else:
            message_buffer += socket.recv(buffersize)

    return binary_message

#----------------------get and handle answer for subcatframe checking-----------------------------
@app.route('/get_answer_subcat', methods = ['GET', 'POST'])
def get_answer_subcat():
    """
    get and handle answer for subcatframe checking
    """
    if request.method == 'POST':
        #the subcat chosen by the annotator
        if request.form['subcat'] != 'correct' and request.form['subcat'] != 'don\'t care':
            session['subcats'][0][2] = request.form['subcat']
            #list of index,verb,subcat string  #only subcat string

        answer = request.form['annotate']
        if answer == 'Yes':  # go to annotate the sentence
            session['subcat_archive'] = session['subcats'].pop(0)
            print(session['subcats'])
            session.modified = True
            return redirect(url_for('annotate'))

        elif answer == 'No':  # load a new next sentence
            print('!!!!')
            session['subcat_archive'] = session['subcats'].pop(0)
            session['conll_strings'].pop(0)
            session["sentences"].pop(0)
            session.modified = True
            print(session["sentences"])
            return redirect(url_for('check_subcat'))

# @app.route('/save_subcat', methods = ['GET', 'POST'])
# def save_subcat():
#     """
#     let the annotator choose to save the subcat or not:
#     """
#     if request.method == 'POST':
#         if request.form['save'] == 'Yes':
#             session['subcats'][0][2] = session['subcat_anno']
#             print(session['subcats'][0])
#     return redirect(url_for('check_subcat'))
#
# @app.route('/annotate_or_not', methods = ['GET', 'POST'])
# def annotate_or_not():
#     """
#     let the annotator choose to annotate the sentence or not
#     """
#     # if don't annotate, but saved subcatframe, how to save the subcat? all forest or just sentence @TODO
#     print(session['subcats'][0])
#     print(session['subcat_anno'])
#     if request.method == 'POST':
#         answer = request.form['annotate']
#         if answer == 'Yes': #go to annotate the sentence
#             #session['subcats'].pop(0)
#             print(session['subcats'][0])
#
#         elif answer == 'No': #load a new next sentence
#             session['subcats'].pop(0)
#             session['conll_strings'].pop(0)
#             session["sentences"].pop(0)
#     return redirect(url_for('annotate'))

#----------------------get and handle answer for forest annotation-----------------------------
@app.route('/get_answer', methods = ['GET', 'POST'])
def get_answer():
    """ Return request for annotation-loop according to user answer"""
    if request.method == 'POST':
        answer = request.form['choice']
        if answer == 'Yes':
            session['requests'] = get_yes(session['question'])
        elif answer == 'No':
            session['requests'] = get_no(session['question'])
        elif answer == 'Undo':
            session['requests'] = get_undo()
        elif answer == 'Abort':
            session['requests'] = get_abort()
    return redirect(url_for('annotate'))



def get_yes(question):
    return {
        'answer': True,
        'question': question,
        'type': 'answer'
        }

def get_no(question):
    return {
        'answer': False,
        'question': question,
        'type': 'answer',
        }

def get_undo():
    return {
        'type' : 'undo',
        'answers' : 1
    }

def get_abort():
    return {
        'type' : 'abort',
        'wanted' : 'best'
    }
#--------------------------------------------------------------------------------------------------------


def handle_solution(data):
    """ Return conll representation of annotated tree """
    solution = data['tree']['nodes']
    words = ['\t'.join(word) for word in solution]
    tree = '\n'.join(words)
    return tree

def handle_question(question):
    visualise(question)

def visualise(data):
    """ Visualize given tree

    Vizualize the given tree: Color fixed edges green, uncertain edges red, all
    others black

    Arguments:
        data: message sent by the AnnotationHelper-server
    Returns a svg-image of the best tree (first tree in the list of trees) or
    a svg-image of the last given tree (solution case)
    """
    try:
        if data['type'] == 'question':
            return generate_dot_tree(data['best_tree'], session['sentence_format']).pipe().decode('utf-8')
        visual = generate_dot_tree(data['tree'], session['sentence_format'])
        if type(visual) == str:
            return visual
        return visual.pipe().decode('utf-8')
    # catch eventual parser not found error thrown by the AaS-server
    except KeyError:
        return 'Parser was not found.'



if __name__ == '__main__':
    desc = """Start a client that connects with the AaS server
    and helps with annotating sentences."""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-H',
        '--host_to_connect',
        required=False,
        type=str,
        default='localhost',
        help='The host that accepts TCP connections.'
        )
    parser.add_argument(
        '-p',
        '--port',
        required=False,
        type=int,
        default=8080,
        help='The port that accepts TCP connections.'
        )
    parser.add_argument(
        '-s',
        '--unix_socket',
        required=False,
        type=str,
        help='Unix socket file to use instead of host and port.'
        )
    parser.add_argument(
        '-c',
        '--configfile',
        required=False,
        type=str,
        help='Name of the config file.',
        default='config.json'
        )

    HOST = os.environ.get('SERVER_HOST', 'localhost')
    arg = parser.parse_args()
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5000'))
    except ValueError:
        PORT = 5000
    config = {
        'host_to_connect': 'localhost',
        'port': 8080,
        'formats': {
            'conll09_gold': {
            'name': 'conll09_gold',
            'id': 0,
            'form': 1,
            'label': 4,
            'label_type': 'pos',
            'head': 8,
            'relation': 10,
            'relation_type': 'deprel'
        }, 'conll09_predicted': {
           'name': 'conll09_predicted',
            'id': 0,
            'form': 1,
            'label': 4,
            'label_type': 'pos',
            'head': 9,
            'relation': 11,
            'relation_type': 'deprel'
        },
    },
    'format_aliases': {
        'conll09': 'conll09_predicted'
    },

        'configfile' : 'config.json'
    }
    config_from_file = read_configfile(
        arg.configfile if 'configfile' in arg else [])
    update_config(config, config_from_file)
    conll_formats = get_conll_formats(config['formats'], config['format_aliases'])
    try:
        socket_to_server.connect((config['host_to_connect'], config['port']))
    except ConnectionRefusedError:
        print('The connection was refused. Did you start the AaS-server?')
        sys.exit()

    app.debug = True
    app.run(HOST, PORT) #web client runs on localhost and port
