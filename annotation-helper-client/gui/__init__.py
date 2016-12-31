from flask import Flask, render_template, url_for, request, flash, redirect, send_file
from werkzeug.utils import secure_filename
import sys
import os
import argparse
import socket
import asyncio

from common import AnnotationHelperClientProtocol
from visualizer import visualize_solution



app = Flask(__name__)
ALLOWED_EXTENSIONS = set(['conll', 'conll09', 'conll06'])
app.config['SECRET_KEY'] = 'jqUNf8?B\8d&(teVZq,~'


def parse_sentence(sentence):
    return sentence

def request_creator(requests):
    if type(requests) == tuple:
        return {
            'type': 'request',
            'use_forest': open(requests[0]).read(),
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

@app.route('/choose_input')
def choose_input():
    return render_template("choose.html")

@app.route('/input_sentence', methods=["GET", "POST"])
def input_sentence():
    # ugly, need to find a way to get rid of it
    if request.method == "POST":
        if request.form["sentence"]:
            #sentence = parse_sentence(request.form["sentence"])
            requests = request.form["sentence"]
           #    return redirect(url_for('annotate'))
    return render_template("input.html")

@app.route('/load_file', methods=["GET", "POST"])
def load_file():
    if request.method == "POST":
        if request.files:
            print(request.files)
            if 'file' not in request.files:
                flash('No file')
                return redirect(url_for('input_sentence'))
            data_file = request.files['file']
            if data_file.filename == '':
                flash('No file selected')
                return redirect(url_for('input_sentence'))
            if allowed_file(data_file.filename):
                data = secure_filename(data_file.filename)
                FILENAME = os.path.join(app.config['UPLOAD_FOLDER'], data)
                requests = FILENAME, "file"
    return render_template("load_file.html")


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

if __name__ == '__main__':
    desc = '''Start a client that connects with the annotation-helper server
    and helps with annotating sentences.'''
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-H', '--host', required=False, type=str,
        default='127.0.0.1', help='The host that accepts TCP connections.')
    parser.add_argument('-p', '--port', required=False, type=int,
        default=8080, help='The port that accepts TCP connections.')
    parser.add_argument('-s', '--unix_socket', required=False, type=str,
        help='Unix socket file to use instead of host and port.')
    parser.add_argument('-f', '--conll_file', required=False, default=None,
        help='Path of a file containing a forest.')

    args = parser.parse_args()

    if args.unix_socket:
        socket_to_server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        socket_to_server.connect(args.unix_socket)
    else:
        socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_to_server.connect((args.host, args.port))

    app.run()
