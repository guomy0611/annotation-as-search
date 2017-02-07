# Annotation as Search (AaS)

The AaS framework attempts to ease the manual annotation of CoNLL treebanks by letting an already existent parser do all the grunt work with the human annotator only annotating the difficult parts.
This is done by first parsing a sentence into a forest of possible trees and then generating questions based on the differences of the trees in the forest.
The user then answers the questions and the forest is trimmed until only one tree remains.
For more detailed information see our documentation at `doc/system-spec`.

## Infrastructure

An AaS setup consists of a server and a client.
For setting up the server, refer to the section [AaS-Server](#AaS-Server)

As for the client, we provide two solutions:
  * A minimal CLI client documented at `annotation-helper-client/README.md`
  * A more involved Web Client documented at `annotation-helper-client/gui/README.md`.

## AaS-Server

### Requirements

  * Python version >= 3.4

### Starting the server

The server can be started using the following commandline:

    $ python3 server.py --host 0.0.0.0 --port 8080 --logfile ~/.aas-server.log --configfile ~/.aas-server.json --loglevel INFO

All of the options can be omitted, in which case their values are looked up in the config file.
If they are not present in the config file either, the default values will be used.

You can remind yourself of the options and view their short variants with

    $ python3 server.py --help

### Configuring the server

The configuration file for the server uses the serialization format [JSON](https://tools.ietf.org/html/rfc7159) and should contain exactly one JSON object.
The following keys are recognized:

  * `host`: The host that accepts TCP connections.
  * `port`: The port that accepts TCP connections.
  * `logfile`: The server's logfile.
  * `loglevel`: Level of detail the server employs to log events.
  * `formats`: The formats the server recognizes. Described below in more detail.
  * `format_aliases`: Experimental feature attempting to ease format description at the client side.
  * `default_format`: Format to default to if the client does not specify a format.
  * `processors`: Processors the server can use to process data (usually a sentence) given by the client to produce a forest. Described below in more detail.

#### Formats

The value of the formats key should be another JSON object each key of which corresponding to a single format.
(Note that only CoNLL style formats, i. e. tab-separated tables, are supported by our server.)
The value of a CoNLL format should again be a JSON object and should contain the following keys:

  * `name`: The name of the format. Should match the key the format is filed under.
  * `id`: The CoNLL column containing the id of the word. Should always be 0.
  * `form`: The CoNLL column containing the form of the word. Should probably be 1.
  * `label`: The CoNLL column containing the label for which questions should be generated. This might be the POS column or the morph column. Note that our server does not yet use this information.
  * `label_type`: The type of label indicated by the `label` column. For instance "pos" for POS tags.
  * `relation`: The CoNLL column containing the relation for which questions should be generated. This might be the dependency relation column for CoNLL09 and CoNLL-X/CoNLL-U/CoNLL06 formats.
  * `head`: The CoNLL column containing the head belonging to the specified relation.
  * `relation_type`: The type of relation indicated by the `relation` column. For instance "deprel" for dependency relations.

The following is an example for two variants of a CoNLL09 format:

```json
"formats": {
  "conll09_gold": {
    "name": "conll09_gold",
    "id": 0,
    "form": 1,
    "label": 4,
    "label_type": "pos",
    "head": 8,
    "relation": 10,
    "relation_type": "deprel"
  }, "conll09_predicted": {
    "name": "conll09_predicted",
    "id": 0,
    "form": 1,
    "label": 5,
    "label_type": "pos",
    "head": 9,
    "relation": 11,
    "relation_type": "deprel"
  }
}
```

#### Processors

If the server specifies processors, the client can use those processors to transform data client-supplied data into a forest.
The most useful example of this is to enter a sentence at the client side and let the server parse it into a forest.
For this to work, a processor has to specify three key-value pairs:

  * `source_format`: The format of the data the processors receives as input.
  * `target_format`: The format of the data the processor produces as output.
  * `command`: The command that is used to transform data of `source_format` into data of `target_format`. This should be a list with the first element being the program name and the remaining elements being the arguments for the program.

The user input is written to a temporary file that is passed to a processors's `command` and the processor is supposed to create a new file containing its output.
To use infile and outfile in the command's argument, use '{infile}' and '{outfile}'.

`source_format` and `target_format` need not be specified in the formats section of the server configuration.
If they aren't, they are only used for finding a pipeline of multiple processors to transform the `source_format` into the `target_format`.
Format aliases are not yet supported for finding a processor pipeline.

Please note that processors bear an inherent security risk, as a client can start processes on the server.
To minimize this risk, the processors that are made available should carefully check their input.
Also be wary of passing unchecked user input to a shell to avoid shell injection attacks.

The following is an example of some processors.
The keys `name` and `type` are not currently used by the server, though.

```json
"processors": [{
  "name": "UCTO",
  "type": "tokenizer",
  "command": ["/usr/bin/ucto", "{infile}", "{outfile}"],
  "source_format": "raw",
  "target_format": "newline_separated"
}, {
  "name": "LEMMING",
  "type": "lemmatizer",
  "command": ["/usr/bin/lemming", "{infile}", "-o", "{outfile}"],
  "source_format": "newline_separated",
  "target_format": "conll09_lemmatized"
}, {
  "name": "RBG",
  "type": "parser",
  "command": ["/usr/bin/rbg", "{infile}", "{outfile}"],
  "source_format": "conll09_lemmatized",
  "target_format": "conll09"
}, {
  "name": "Θεός",
  "type": "parser",
  "command": ["/home/me/bin/parse", "{infile}", "{outfile}"],
  "source_format": "raw",
  "target_format": "conll09"
}]
```

#### Example use case for processors: Reading forests stored on the server.

Since parsing a sentence into a forest can take quite a while, a mechanism to use forests already stored on the server is paramount.
One approach is to create a directoy on the server containing pre-parsed forests (say `/media/forest_dir`) and use a processor to link the forest files to files the server has access to.
The processor has to check if the input is valid and then link the file.
Depending on the way the processor uses the input, validating is very important.
One possible way to implement this processor is the following bash script, which assumes that the forest files have names consisting of digits only:

```bash
#!/usr/bin/env bash

FOREST_DIR='/media/forest_dir'
INFILE="$1"
OUTFILE="$2"

# Test if input consists of digits only.
input_valid() {
    local INPUT="$1"
    [[ "$INPUT" =~ ^[[:digit:]]+$ ]]
}

if input_valid "$INFILE"; then
    ln -sf "$FOREST_DIR/$INFILE" "$OUTFILE"
fi
```

This processor could then be configured for the server by specifying the following processor object in the `processors` list of the server’s configuration file.
Here, we assume that the forest’s format is `conll09_predicted` and the script is located at `/path/to/script`.

```json
{
  "name": "Forest Linker",
  "type": "linker",
  "command": ["/path/to/script", "{infile}", "{outfile}"],
  "source_format": "filename",
  "target_format": "conll09_predicted"
}
```

### Extending AaS server and client

#### Changing the question generation algorithm.

The file `annotation-helper/tree.py` contains the complete code for the question generation algorithm.

The code for the classes forest and tree are defined in it.

The tree class treats all functions that a single parse should be able to handle, like checking if a certain tuple is contained in the tree (`contains`).
The forest class treats all functions that a whole forest should be able to handle, like filtering all trees if they contain a certain tuple (`filter`) or calculating the best question to ask (`get_best_tuple`).

Currently the implementation only supports question generation for dependency tuples. The filter and `get_best_tuple` methods have to be changed if any other algorithm is to be implemented.
For example, to create questions based on labels instead of relations only.

#### Authentication

In order to continue working over various sessions (e.g. stop the annotation of a sentence and continue it the next day) a data-base is needed.
This data-base should be located on the host providing the AaS-server and be handled by the AaS-server.
In order to keep user data secure and separated from one another an authentication method would be needed (e.g. username, password, etc.)

There are various ways to realize this, depending on your desired level of security and the amount of users you expect.
For instance, if you only expect a few users, you could use the following setup:
Create a psotgres-database on the server and store each user's annotated sentences and prefered tree-format in it.
Of course you would also need to store each user's name and password in the data-base.
Keep in mind to chose a secure authentification method (not `trust`!). For more information on authentification methods in postgresql, visit https://www.postgresql.org/docs/9.6/static/auth-methods.html.

If you expect many users and you may want to install the database on yet more servers or split up the users data, you may want to take a look at LDAP.
For more information on LDAP: "http://www.openldap.org/doc/admin24/"
And for more information on authentication with a database using LDAP, visit "http://httpd.apache.org/docs/current/mod/mod_authnz_ldap.html".


We urge you to use a safe authentication method! 

#### Automatically loading forests

#### Enabling save option after every question in the web client.

The `abort-option` during the annotation process is no longer needed.
You may change it to a `save-option`. If a user clicked on it, the process would be stopped and the best tree would be saved.

### Load a forest file which contains more than one sentence

You may find it  tedios to upload a new file each time you want to annotate a sentence. You could enable the webclient to handle more than one sentence per forest file.
Simply separate two forests by two blank lines and change the `load-file`-funtion accordingly.

## Appendix

### Training the Parser

Here the commands with which to train the parser:
```bash
java -cp anna-3.3-d8.jar is2.parser.Parser -train train.conll -model models/de3.anna.mdl
java -cp anna-3.3-d8.jar is2.lemmatizer.Lemmatizer -train train.conll  -model models/de3.lemma.mdl
java -cp anna-3.3-d8.jar is2.tag.Tagger -train train.conll  -model models/de3.tag.mdl
java -cp anna-3.3-d8.jar is2.mtag.Tagger -train train.conll  -model models/de3.mtag.mdl
```

The Parser, train.conll and the trained models can be found here: /mnt/proj/staniek/NBest/NBestParsers

### Using the Parser

Here a small script that makes use of the parser:

```bash
java -cp anna-3.61.jar is2.util.Split "$1" > one-word-per-line.txt
java -Xmx2G -cp anna-3.3-d8.jar is2.lemmatizer.Lemmatizer -model  de3.lemma.mdl -test one-word-per-line.txt -out  lemmatized.txt
java -Xmx2G -cp anna-3.3-d8.jar is2.tag.Tagger  -model  de3.tag.mdl -test lemmatized.txt -out  tagged.txt
java -Xmx2G -cp anna-3.3-d8.jar is2.mtag.Tagger  -model  de3.mtag.mdl -test tagged.txt -out  morph-tagged.txt
java -cp anna-3.3-d8.jar:lib/trove-2.0.4.jar is2.parser.ParserNBest -model de3.anna.mdl -test morph-tagged.txt -out n-best.out -nbest 1000
python nbest_to_conll.py n-best.out "$2"
```

Alternatively, normally trained models (except for the ParserNBest part) could be used.

```bash
java -cp anna-3.61.jar is2.util.Split "$1" > one-word-per-line.txt
java -Xmx2G -cp anna-3.3-d8.jar is2.lemmatizer.Lemmatizer -model  lemma-ger-3.6.model -test one-word-per-line.txt -out  lemmatized.txt
java -Xmx2G -cp anna-3.3-d8.jar is2.tag.Tagger  -model  tag-ger-3.6.model -test lemmatized.txt -out  tagged.txt
java -Xmx2G -cp anna-3.3-d8.jar is2.mtag.Tagger  -model  morphology-ger-3.6.model -test tagged.txt -out  morph-tagged.txt
java -cp anna-3.3-d8.jar:lib/trove-2.0.4.jar is2.parser.ParserNBest -model de3.anna.mdl -test morph-tagged.txt -out n-best.out -nbest 1000
python nbest_to_conll.py n-best.out "$2"
```

The `nbest_to_conll.py` script can be found here: `/home/students/staniek/Public/Parser/`

Already generated parseddata can be found here: `/mnt/proj/staniek/NBest/CreateTestdata/`
