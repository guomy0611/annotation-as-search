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
    AnnotationHelperClientProtocol,
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
            requests = request.form["sentence"]
            return redirect(url_for('annotate'))
    return redirect(url_for('choose_input'))

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
                data_file.save(os.path.join(app.config['UPLOAD_FOLDER'], data))
                global requests
                requests = data, "file"
                return redirect(url_for('annotate'))
    return redirect(url_for('choose_input'))

@app.route('/annotate', methods = ["GET", "POST"])
def annotate():
    global requests
    create_requests = lambda : request_creator(requests)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    coro = loop.create_connection(
    lambda : AnnotationHelperClientProtocol(
        loop,
        create_requests,
        handle_question=handle_question,
        handle_solution=handle_solution
        ),
        sock=socket_to_server
        )
    loop.run_until_complete(coro)

    return render_template("visualized_tree.html")

def find_response(self, server_data):
    if server_data['type'] == 'question':
        return redirect(url_for('handle_question', question=server_data))
    elif server_data['type'] == 'solution':
        return redirect(url_for('handle_solution', data=server_data))
    elif server_data['type'] == 'error':
        return redirect(url_for('handle_error', data=server_data))
    else:
        return url_for('handle_default', data=server_data)




def get_yes(question):
    return {
        'type': 'answer',
        'answer': True,
        'question': question
        }

def get_no(question):
    return {
        'type': 'answer',
        'answer': False,
        'question': question
        }

def handle_solution(self, solution):
    visualize_solution(solution, 1)
    try:
        if request.method == "POST":
            answer = request.form["answer"]
            if answer == "Yes":
                return redirect(url_for("saveFile"))
            else:
                return render_template("visualized_tree.html",
                                        message="Please correct the tree")
        else:
            return render_template("visualized_tree.html")
    # Debugging, remove later
    except Exception as e:
        return render_template("visualized_tree.html", message=e)

@app.route('/handle_question', methods = ["GET", "POST"])
def handle_question(self, question):
    q = question['question']
    if request.method == "POST":
        answer = request.form["choice"]
        if answer == "Yes":
            self.response = get_yes(q)
        elif answer == "No":
            self.response = get_no(q)
    else:
        self.end_conversation()

    self.send_response()


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

def visualize(self, data):
    if server_data['type'] == 'question':
        q = data['question']['question']
        parts = ["\t".join(word) for word in data['question']['fixed_nodes']['nodes']]
        tree = "\n".join(parts)
        visualize_solution(tree)
    else:
        q = "Final tree"
        parts = ["\t".join(word) for word in data['tree']['nodes']]
        tree = "\n".join(parts)
        visualize_solution(tree, 1)

if __name__ == '__main__':
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5000'))
    except ValueError:
        PORT = 5000

    socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_to_server.connect((HOST, 8080))
    app.debug = True
    start_server = app.run(HOST, PORT)
    eventloop = asyncio.new_event_loop()
    asyncio.set_event_loop(eventloop)
    eventloop.run_until_complete(start_server)
    eventloop.run_forever()

