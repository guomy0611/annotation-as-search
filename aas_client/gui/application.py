import ast

from flask import (
    Flask,
    render_template,
    url_for,
    request,
    flash,
    redirect,
    session,
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

from helper import (
    generate_sentence,
    get_subcatframe,
    save_result,
    update_config,
    read_configfile,
    get_conll_formats,
    visualise,
    handle_solution,
    handle_question
    )

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker


app = Flask(__name__)
ALLOWED_EXTENSIONS = {'conll', 'conll09', 'conll06', 'conllu'}
app.config['SECRET_KEY'] = 'jqUNf8?B\8d&(teVZq,~'

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://localhost/demo3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Session = sessionmaker(bind=db)
db_session = Session()
socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#socket_to_server.connect(('localhost', 5678))

#TODO:use config class and file for the flask application

#-------------------------------------------------------------------------------
class Sentence(db.Model):
    __tablename__ = 'sentences'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    sentence = db.Column(db.String(1000), unique=False, nullable=False)
    conll_forest = db.Column(db.String(10000), unique=False, nullable=True)
    subcat_suggested = db.Column(db.String(100),unique=False, nullable=True)
    tree_correct = db.Column(db.String(1000), unique=False, nullable=True)
    subcat_correct = db.Column(db.String(100),unique=False, nullable=True)
    subcat_edited = db.Column(db.Boolean, unique=False, nullable=True, server_default="false")
    tree_annotated = db.Column(db.Boolean, unique=False, nullable=True, server_default="false")
    last_modified = db.Column(db.Boolean, unique=False, nullable=True, server_default="false")

    def __repr__(self):
        return '<Sentence %r>' % self.sentence
#-------------------------------------------------------------------------------
#format_info = {"name": "conll09_gold", "id": 0,"form": 1,"label": 4,"label_type": "pos","head": 8,"relation": 10,"relation_type": "deprel"}
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

def current_sent(sid):
    """
    get the sentence entry from db by id

    :param sid: id of the sentence in the database
    :return: sentence entry (of class Sentence
    """
    sent = Sentence.query.get(sid)
    return sent

def get_subcat_tree(subcat, conll_forest):
    """
    ask the server to return the best tree containing the given subcat frame
    """

    request = {"type": "subcat", "subcat": subcat, "use_forest": conll_forest, "forest_format": "conll09_gold"}  # the start of a sentence annotation
    socket_to_server.send(pack_message(encode_message(request)))
    received_message = decode_message(receive_message(socket_to_server))
    tree = received_message
    tree_img = generate_dot_tree(tree, conll_format).pipe().decode('utf-8')

    return tree_img

def get_tokens(conll_forest):
    sentence_annotated = conll_forest.split("\n\n")[0]
    tokens = [(line.split("\t")[1],line.split("\t")[0]) for line in sentence_annotated.split("\n")]
    return tokens
#---------------------------------------------------------------


@app.route('/')
def homepage():
    """ render startpage and remove request-information of previous annotation """
    if 'requests' in session.keys():
        session.pop('requests')
    return render_template('index.html')

@app.route('/init_annotation')
def init_annotation():
    return redirect(url_for('overview', id=LAST_MODIFIED+1))

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


@app.route('/overview/<id>')
def overview(id=1):
    """
    1. initialize session vaialbles
    2. overview: sentence, suggested subcat and best tree in the forest containing the subcat
    let annotator choose whether or not he/she wants to edit the sentence
    """
    #@TODO no more sentence in db: pop up a window
    session['id'] = int(id)
    cur_sent = current_sent(session['id']) #type Sentence not json serializable
    session['sentence'] = cur_sent.sentence
    session['tokens'] = get_tokens(cur_sent.conll_forest)
    session['subcat_suggested'] = ast.literal_eval(cur_sent.subcat_suggested)
    session['conll_forest'] = cur_sent.conll_forest
    session['subcat_tree'] = get_subcat_tree(session['subcat_suggested'], session['conll_forest'])

    return render_template('overview.html',
                           sentence=session['tokens'],
                           subcat=session['subcat_suggested'],
                           sentence_visual=session['subcat_tree']
                           )

@app.route('/edit',methods = ['GET', 'POST'])
def edit():
    """
    let annotator choose whether or not he/she wants to edit the sentence
    """

    answer = request.form['edit']
    if answer == 'Yes':
        cur_sent = current_sent(session['id'])
        cur_sent.last_modified = True
        db.session.add(cur_sent)
        db.session.commit()
        return redirect(url_for('subcat'))

    elif answer == 'No':
        cur_sent = current_sent(session['id'])
        cur_sent.last_modified = True
        db.session.add(cur_sent)
        db.session.commit()
        return redirect(url_for('overview', id=session['id']+1))


@app.route('/subcat')
def subcat():
    """
    let the annotator edit the subcat frame
    """

    return render_template('subcat.html',
                           sentence=session['sentence'],
                           subcat=session['subcat_suggested'],
                           sentence_visual=session['subcat_tree']
                           )

@app.route('/get_answer_subcat', methods=['GET', 'POST'])
def get_answer_subcat():
    """
    get and handle answer for subcatframe editing
    """

    if request.method == 'POST':
        #the subcat corrected by the annotator, demonstrate the best tree containing the corrected subcat
        if request.form['subcat'] != 'correct':
            session['subcat_correct'] = request.form['subcat']

            m1="below is the best tree in the forest containing the subcat frame you just corrected, if there is one, else the first tree of the forest is shown"
            m2="you've corrected the subcat frame, do you want to annotate the dependency trees?"
            img=get_subcat_tree(session['subcat_correct'], session['conll_forest'])

        else:
            #TODO save if the subcat is correct in a boolean col in the database
            session['subcat_correct'] = session['subcat_suggested']

            m1="below is the best tree in the forest containing the suggested subcat frame, if there is one, else the first tree of the forest is shown"
            m2 = "the given subcate frame is right, do you want to annotate the dependency trees?"
            img= session['subcat_tree']

        if request.form['submit'] == 'Submit':
            #update database
            cur_sent = current_sent(session['id'])
            cur_sent.subcat_correct = session['subcat_correct']
            cur_sent.subcat_edited = True


            #current_db_session = db_session.object_session(cur_sent)
            db.session.add(cur_sent)
            db.session.commit()
            return render_template('subcat_result.html',
                            sentence=session['sentence'],
                            subcat=session['subcat_correct'],
                            message1=m1,
                            message2=m2,
                            sentence_visual=img
                            )

@app.route('/annotate_or_not',methods = ['GET', 'POST'])
def annotate_or_not():
    """
    let annotator choose whether or not he/she wants to annotate the dependency trees
    """

    answer = request.form['annotate']
    if answer == 'Annotate':
        return redirect(url_for('annotate'))

    elif answer == 'Skip':
        return redirect(url_for('overview', id=session['id']+1))#-->next


@app.route('/annotate', methods = ['GET', 'POST'])
def annotate():
    """ Start and continue annotation loop.

    Send current question to the AaS-Server, then receive and visualise the
    answer of the server. Display best tree and the received question.

    Returns a html-page containing the best tree, current question and optional answers
    if server sent an error:
        Returns error-html-page
    """

    # print('anno')
    # if len(session.keys()) == 0:
    #     return redirect(url_for('no_cookies_set'))

    if 'requests' not in session.keys():
        requests = request_creater()  # the start of a sentence annotation

    else:
        requests = session['requests']


    socket_to_server.send(pack_message(encode_message(requests)))
    received_message = decode_message(receive_message(socket_to_server))
    sentence_visual = visualise(received_message,conll_format)

    if 'question' in received_message:

        session['question'] = received_message['question']
        question = "Does " + session['question']['dependent'] + " depend on " \
                    + session['question']['head'] + " (relationtype: "  \
                    + session['question']['relation_type'] + ", relation: " \
                    + session['question']['relation'] + ")?"

        return render_template('visualised_tree_dot.html',
                                question=question,
                                sentence=session['sentence'],
                                sentence_visual=sentence_visual
                                )

    elif 'error' in received_message:
        return render_template('error.html')

    session.pop('requests')

    #no more question, final solution
    session['solution'] = received_message['tree']['nodes']
    session['message'] = received_message
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

            if answer == 'Visualise':
                tree_sentence = request.form['sentence']
                message = session['message']
                message['tree']['nodes'] = [tree.split('\t')    \
                                            for tree in tree_sentence.split('\n')]
                return render_template('visualised_tree_final.html',
                                        sentence_visual = visualise(message,conll_format),
                                        sentence_conll = tree_sentence
                                        )
            if answer == 'Save':
                #save the final tree in the database
                tree_correct = session['message']['tree']['nodes']
                subcat_correct = session['subcat_correct']

                cur_sent = current_sent(session['id'])
                cur_sent.tree_correct = session['message']['tree']['nodes']
                cur_sent.tree_annotated = True
                db.session.add(cur_sent)
                db.session.commit()

                return redirect(url_for('overview', id=session['id']+1))

            if answer == 'End Annotation':
                return redirect(url_for('homepage'))

    except KeyError:
        return redirect(url_for('no_cookies_set'))

@app.route('/noCookies')
def no_cookies_set():
    """ Catch session[key] error and render costumized, helpful template """
    return render_template('cookies.html')

def request_creater():

    request = {
        'type': 'request',
        'use_forest': session['conll_forest'],  # the raw conll forest string
        'forest_format': 'conll09_gold'
    }
    return request

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

if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=1234)
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
            '-f',
            '--conll_format',
            required=False,
            type=str,
            help='conll format used in the database ',
        )
        parser.add_argument(
            '-c',
            '--configfile',
            required=False,
            type=str,
            help='Name of the config file.',
            default='config.json'
        )
        #web client's host and port
        HOST = os.environ.get('SERVER_HOST', 'localhost')
        arg = parser.parse_args()
        try:
            PORT = int(os.environ.get('SERVER_PORT', '5000'))
        except ValueError:
            PORT = 5000
        config = {
            'host_to_connect': 'localhost',
            'port': 5678,
            'format': {
                    'name': 'conll09_gold',
                    'id': 0,
                    'form': 1,
                    'label': 4,
                    'label_type': 'pos',
                    'head': 8,
                    'relation': 10,
                    'relation_type': 'deprel'
            }
        }
        config_from_file = read_configfile(
            arg.configfile if 'configfile' in arg else [])
        update_config(config, config_from_file)
        conll_format = config['format']
        try:
            socket_to_server.connect((config['host_to_connect'], config['port']))
        except ConnectionRefusedError:
            print('The connection was refused. Did you start the AaS-server?')
            sys.exit()

        app.debug = True
        if Sentence.query.filter_by(last_modified=True).first() is not None:
            LAST_MODIFIED = 1
        else:
            LAST_MODIFIED = Sentence.query.filter_by(last_modified=True).first().id
        app.run(HOST, PORT)

