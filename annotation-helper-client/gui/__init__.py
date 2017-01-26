from flask import (
    Flask,
    render_template,
    url_for,
    request,
    flash,
    redirect,
    )
from werkzeug.utils import secure_filename
import sys
import os
import argparse
import socket

from common import (
    encode_message,
    decode_message,
    pack_message
    )
from conll_convert import conll06_to_conll09
from get_sentence_from_conll import generate_sentence
from generate_dot_tree import generate_dot_tree

# app variables and definitions
app = Flask(__name__)
# basic check if file is valid
ALLOWED_EXTENSIONS = set(['conll', 'conll09', 'conll06'])
app.config['SECRET_KEY'] = 'jqUNf8?B\8d&(teVZq,~'
# folder to save files to be annotated
UPLOAD_FOLDER = 'loadedFiles'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
conll09 = eval(open('conll09_gold.format').read())


@app.route('/')
def homepage():
    ''' render startpage '''
    return render_template('index.html')

@app.route('/exit/', methods = ['POST', 'GET'])
def close_annotator():
    global socket_to_server
    if request.method == 'POST':
        if request.form['closeApplication']:
            # ugly, but functional, improve later
            if os.path.isfile('static/annotated_sentence.conll09'):
                os.remove('static/annotated_sentence.conll09')
            sys.exit()
    return render_template('exit.html')

@app.route('/save_file/', methods = ['POST', 'GET'])
def saveFile():
   return render_template('save_file.html')

@app.route('/choose_input', methods=['GET','POST'])
def choose_input():
    return render_template('choose.html')

@app.route('/input_sentence', methods=['GET', 'POST'])
def input_sentence():
    global requests, sentence
    if request.method == 'POST':
        if request.form['sentence']:
            requests = request_creator(request.form['sentence'])
            sentence = request.form['sentence']
            create_connection()
            return redirect(url_for('annotate'))
    return render_template('input.html')

@app.route('/load_file', methods=['GET', 'POST'])
def load_file():
    global sentence
    if request.method == 'POST':
        if request.files:
            data_file = request.files['file']
            if data_file.filename == '':
                flash('No file selected')
                return redirect(url_for('choose_input'))
            if allowed_file(data_file.filename):
                data = secure_filename(data_file.filename)
                data_file.save(os.path.join(app.config['UPLOAD_FOLDER'], data))
                if data_file.filename.endswith('conll06'):
                    conll06_to_conll09(os.path.join(app.config['UPLOAD_FOLDER'], data))
                    data = data[:-8] + '_converted.conll09'
                global requests
                requests = data, 'file'
                sentence = generate_sentence(
                            open(UPLOAD_FOLDER +'/' + data).read()
                            )
                requests = request_creator(requests)
                create_connection()
                return redirect(url_for('annotate'))
    return render_template('load_file.html')

@app.route('/annotate', methods = ['GET', 'POST'])
def annotate():
    global requests, question, socket_to_server, sentence, message
    socket_to_server.send(pack_message(encode_message(requests)))
    received_message = decode_message(receive_message(socket_to_server))
    find_response(received_message)
    if 'question' in received_message:
        question = received_message['question']
        return render_template('visualized_tree_dot.html',
                                question=received_message['question'],
                                sentence=sentence,
                                sentence_visual=visualize(received_message)
                                )
    message = received_message
    return render_template('visualized_tree_final.html',
                            sentence_visual=visualize(received_message),
                            sentence_conll = handle_solution(received_message)
                        )



@app.route('/contact/')
def contact():
    return render_template('contact.html')

@app.route('/endResult', methods=['GET', 'POST'])
def annotation_finished():
    global received_message
    if request.method == 'POST':
        answer = request.form['answer']
        if answer == 'Save':
            sentence = request.form['sentence']
            sentence_file = open('static/annotated_sentence.conll09', 'a')
            sentence_file.write(sentence+'\n\n')
            print(sentence)
            sentence_file.close()
            return redirect(url_for('homepage'))
        elif answer == 'Visualise':
            tree_sentence = request.form['sentence']
            message['tree']['nodes'] = [tree.split("\t") for tree in tree_sentence.split("\n")]
            return render_template('visualized_tree_final.html',
                                    sentence_visual = visualize(message),
                                    sentence_conll = tree_sentence
                                    )
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


def request_creator(requests):
    if type(requests) == tuple:
        return {
            'type': 'request',
            'use_forest': open(UPLOAD_FOLDER +'/' + requests[0]).read(),
            'forest_format': 'conll09'
            }

    else:
        return {
            'type': 'request',
            'process': requests,
            'source_format': 'raw',
            'target_format': 'conll09'
            }

def allowed_file(filename):
    return '.' in filename and \
            filename.split('.')[-1].lower() in  ALLOWED_EXTENSIONS


def create_connection():
    global socket_to_server
    socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_to_server.connect((HOST, 8080))

def inspect_message_buffer(message_buffer):
    '''
    Check if a message buffer contains a complete prefix indicating
    the length of the message. If so, return the index of the null byte
    separating the length indication from the payload and return the
    indicated length of the message.
    '''
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
    '''
    Read data from the given socket until a full message is received.
    Return the message as a bytestring.
    If there is more than one message in the message buffer the global
    message_buffer will hold the rest.
    '''
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


def find_response(server_data):
    if server_data['type'] == 'error':
        handle_error(server_data)
    else:
        return

@app.route('/get_answer', methods = ['GET', 'POST'])
def get_answer():
    global requests, question
    if request.method == 'POST':
        answer = request.form['choice']
        if answer == 'Yes':
            requests = get_yes(question)
        elif answer == 'No':
            requests = get_no(question)
        elif answer == 'Undo':
            requests = get_undo()
        elif answer == 'Abort':
            requests = get_abort()
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

def handle_solution(data):
    solution = data['tree']['nodes']
    words = ['\t'.join(word) for word in solution]
    tree = '\n'.join(words)
    return tree

def handle_question(question):
    visualize(question)

def visualize(data):
    if data['type'] == 'question':
        return generate_dot_tree(data['best_tree'], conll09).pipe().decode('utf-8')
    return generate_dot_tree(data['tree'], conll09).pipe().decode('utf-8')



if __name__ == '__main__':
    app.debug = True
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5000'))
    except ValueError:
        PORT = 5000
    app.run(HOST, PORT)
