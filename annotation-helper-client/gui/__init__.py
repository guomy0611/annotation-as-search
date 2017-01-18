from flask import Flask, render_template, url_for, request, flash, redirect, send_file
from werkzeug.utils import secure_filename
import sys
import os
import argparse
import socket
import asyncio

from protocoll_gui import (
    unpack_received_data,
    pack_data_for_sending,
    )

from visualizer import visualize_solution
from multiprocessing import Process


app = Flask(__name__)
ALLOWED_EXTENSIONS = set(['conll', 'conll09', 'conll06'])
app.config['SECRET_KEY'] = 'jqUNf8?B\8d&(teVZq,~'
UPLOAD_FOLDER = 'loadedFiles'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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


@app.route('/')
def homepage():
    return render_template("index.html")


@app.route('/exit/', methods = ["POST", "GET"])
def close_annotator():
    if request.method == "POST":
        if request.form["closeApplication"]:
            # ugly, but functional, improve later
            print("Ending Annotation Helper")
            sys.exit()
    return render_template('exit.html')


@app.route('/save_file/', methods = ["POST", "GET"])
def saveFile():
   return render_template("save_file.html")

def allowed_file(filename):
    return '.' in filename and \
            filename.split('.')[-1].lower() in  ALLOWED_EXTENSIONS

@app.route('/choose_input', methods=["GET","POST"])
def choose_input():
    return render_template("choose.html")

@app.route('/input_sentence', methods=["GET", "POST"])
def input_sentence():
    global requests
    # ugly, need to find a way to get rid of it
    if request.method == "POST":
        if request.form["sentence"]:
            requests = request_creator(request.form["sentence"])
            create_connection()
            return redirect(url_for('annotate'))
    return redirect(url_for('choose_input'))

def create_connection():
    global socket_to_server
    socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_to_server.connect((HOST, 8080))

@app.route('/load_file', methods=["GET", "POST"])
def load_file():
    if request.method == "POST":
        if request.files:
            data_file = request.files['file']
            if data_file.filename == '':
                flash('No file selected')
                return redirect(url_for('choose_input'))
            if allowed_file(data_file.filename):
                data = secure_filename(data_file.filename)
                print(data_file)
                data_file.save(os.path.join(app.config['UPLOAD_FOLDER'], data))
                global requests
                requests = data, "file"
                requests = request_creator(requests)
                create_connection()
                return redirect(url_for('annotate'))
    return redirect(url_for('choose_input'))

@app.route('/annotate', methods = ["GET", "POST"])
def annotate():
    global requests, question, socket_to_server
    print(requests)
    socket_to_server.send(pack_data_for_sending(requests))
    data = unpack_received_data(socket_to_server.recv(1024))
    find_response(data)
    if 'question' in data.keys():
        question = data['question']
        return render_template("visualized_tree.html", question = data['question'])
    return redirect(url_for('annotation_finished'))

def find_response(server_data):
    if server_data['type'] == 'question':
        handle_question(server_data)
    elif server_data['type'] == 'solution':
        handle_solution(server_data)
    elif server_data['type'] == 'error':
        handle_error(server_data)
    else:
        handle_default(server_data)

@app.route('/get_answer', methods = ["GET", "POST"])
def get_answer():
    global requests, question
    if request.method == "POST":
        answer = request.form["choice"]
        if answer == "Yes":
            requests = get_yes(question)
        elif answer == "No":
            requests = get_no(question)
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

def handle_solution(data):
    solution = data['tree']['nodes']
    words = ["\t".join(word) for word in solution]
    tree = "\n".join(words)
    visualize_solution(tree, 1)

def handle_question(question):
    q = question['question']
    visualize(question)


@app.route('/endResult/', methods=["GET", "POST"])
def annotation_finished():
    try:
        if request.method == "POST":
            answer = request.form["answer"]
            if answer == "Yes":
                # TODO get conll part, convert to conll09 and save in static
                return redirect(url_for('saveFile'))
            else:
                return render_template("visualized_tree.html",
                                    message="Please correct the tree")

        else:
            return render_template("visualized_tree.html")
    # Debugging, remove later
    except Exception as e:
        return render_template("visualized_tree.html", message=e)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

def visualize(data):
    if data['type'] == 'question':
        q = data['question']
        parts = ["\t".join(word) for word in data['fixed_nodes']['nodes']]
        tree = "\n".join(parts)
        visualize_solution(tree)
    else:
        q = "Final tree"
        parts = ["\t".join(word) for word in data['tree']['nodes']]
        tree = "\n".join(parts)
        visualize_solution(tree, 1)

class Protocol:
    def __init__(self, requests):
        HOST = os.environ.get('SERVER_HOST', 'localhost')
        try:
            PORT = int(os.environ.get('SERVER_PORT', '5000'))
        except ValueError:
            PORT = 5000
        socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_to_server.connect((HOST, 8080))
        socket_to_server.send(requests.encode())
        data = socket_to_server.recv(1024).decode()
        socket_to_server.close()


if __name__ == '__main__':
    app.debug = True
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5000'))
    except ValueError:
        PORT = 5000

    app.run(HOST, PORT)

