from flask import Flask, render_template, url_for

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template("index.html")

#@app.route('/annotate')
#def annotate():
    # TODO get server data
#    html_tree = visualizer.visualize_solution(args, 0)
#    return render_template(visualize.py(html_tree))

@app.route('/exit/')
def close_annotator():
    return render_template('exit.html')

@app.route('/loadFile/')
def loadFile():
    pass

@app.route('/saveFile/')
def saveFile():
    pass

@app.route('/endResult/')
def annotation_finished():
    #final = visualizer.visualize_solution(finishedTree, 1)
    return render_template("visualized_tree.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

if __name__ == '__main__':
    app.run()
