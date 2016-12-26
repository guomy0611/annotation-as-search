from flask import Flask, render_template, url_for, request, flash, redirect, send_file
from werkzeug.utils import secure_filename
import sys
import os
from conll_convert import conll06_to_conll09

app = Flask(__name__)
ALLOWED_EXTENSIONS = set(['conll', 'conll09', 'conll06', 'txt'])
UPLOAD_FOLDER = 'loadedFiles'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'jqUNf8?B\8d&(teVZq,~'

@app.route('/')
def homepage():
    return render_template("index.html")

@app.route('/annotate')
def annotate():
   # TODO get server data
   render_template("annotate.html")

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

@app.route('/load_file/', methods = ["POST", "GET"])
def loadFile():
    if request.method == "POST":
        if 'file' not in request.files:
            flash('No file')
            return redirect(url_for('homepage'))
        data_file = request.files['file']
        if data_file.filename == '':
            flash('No file selected')
            return redirect(url_for('loadFile'))

        print(data_file.filename)
        if allowed_file(data_file.filename):
            data = secure_filename(data_file.filename)
            data_file.save(os.path.join(app.config['UPLOAD_FOLDER'], data))
            return redirect(url_for('annotate', filename=data))

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
    app.run()
