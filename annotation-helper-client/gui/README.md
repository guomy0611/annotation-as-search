# AaS-Webclient

## Requirements
  * Python >= 3.4, including the following modules:
    * Flask
    * graphviz
    * json
  * a html5-capable browser
  * graphviz

## Starting the webclient

Before you start the webclient you have to start the AaS-Server. Otherwise the 
the webclient will automatically end itself.

Once you have started the server, the webclient can be started using a command 
such as the following:

    $ python3 __init__.py -p 8080 --host_to_connect localhost -c config.json

All options can be omitted except the -c. TThe programm will then proceed using the
default option. The specification of the config file can only be omitted, if the 
default config-file 'config.json' is in the current folder.
In this case the default conll-formats will be used as specified in 'config.json'.

Use the following command to remind yourself of the options:

    $ python3 __init__.py -h

After you have started the webclient it will connect to the AaS-Server automatically.

### Using the webclient

Once you have started the weblcient via the command line, you can work with your
browser only.
Open your favourite browser and visit the url shown on the command line.
You have various options now. Firstly, focus on the title bar. There you have four buttons: 
`Home`, `Contact`, `About` and `Options`. 

`Home` always takes you back to the page you are viewing at the moment. 

`About` links to a page containing links to both READMEs and project-specifications.
View those, if you have trouble using the AaS.

`Contact` links to a page containing information on how to contact the creators of AaS.

Clicking on `Options` opens a drop-down menu with all possible options:
  * `Annotate a new sentence`: Start annotation process and redirect to a page where you can enter the sentence you want to annotate.
  * `Load a new forest`: Start the annotation process by uploading a file containing a parse forest. Keep in mind to only use formats known to the AaS-server
  * `Download annotations`: Downlad your annotated sentences in one file.
  * `End Annotation Helper`: End the webclient. All your annotated sentences and uploaded files will be deleted.

You start the actual annotation process by clicking on `Start Annotation Helper` in the middle of the screen.
Next either enter a sentence you want to annotate and choose the target format (remember: this requires a parser on the host of the  server) or upload a file containing a parse forest (if there is no upload folder yet, the client creates one).
If you upload a file, you must specify the file format. At this moment only the formats conll, conll09, conllu and conll06 are allowed.

Now the real annotation process starts. You are asked a question about the sentence and have the following options:
  * `Yes`: Answer the displayed question with `yes`.
  * `No`: Answer the displayed question with `no`.
  * `Undo`: Return to the previous question.
  * `Abort`: End the annotation process. The current best tree is used for further steps.

On top of the page is always an graphical representation of the current best tree on the server side. 
Each edge of the tree has one of the following colours:
  * Black: All trees on the server contain this edge.
  * Red: An edge exists in the tree, but there are other trees on the server that do not have this edge
  * Green: The edge is fixed. One of the answers you have given confirmed the existence of this edge.

The annotation process ends when you click on `abort` or when there is only one tree left.

The last step in the process is an display of the chosen tree. 
Here you can correct any error in the tree and visualise your new annotation if you want to.
Click on save to store your tree in the client.

You are now redirected to the startpage and can start the entire process again.

Remember to download your annotated sentences when you are done.

### Configuring the webclient

If you want to change the webclients configuration, you need to create your own config file.
The webclient uses the same serialization format as the AaS-server [JSON] and its configuration file is very similar.
The following keys will be recognized:
  * `host_to_connect`: The host the webclient will connect to using a TCP connections. 
      Thus the specified host has to accept TCP connections
  * `port`: The port of the server to connect to
  * `formats`: The formats the server recognizes. For more details see AaS-Server-README
  * `format_aliases`: Experimantal feature to ease format description for the user
  * `unix-socket`: The unix socket file to use instead of host and port

### Security

The Flask webclient should only be used locally. If you want to use it on a server,
you have to use another server to host the webclient (e.g. uWSGI).
Otherwise you will have almost no security.

### Adapted Code
All code in the static/css and static/js folders is taken from bootstrap:
https://getbootstrap.com/getting-started/#download (retrieved in December 2016)

Flask documentation and tutorial inspired parts of the code:
http://flask.pocoo.org/docs/0.12/
