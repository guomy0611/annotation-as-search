# -*- coding: utf-8 -*-

"""
This module serves as an interface between the annotation helper server
and the forest the server uses. It primarily provides functions for
creating and interpreting AaSP messages.
"""

import logging
from enum import Enum
from subprocess import call
import tempfile

from tree import Forest


def get_format_from_config(config, format_name):

    """
       check if the format(of input fils) wished is in supported in config, return the format or error accordingly
       input:configfile, format_name
       output:format dict

        @:param config: input config
        ...
        "formats": {
            "conll09_gold":{
                "name": "conll09_predicted",
                "id": 0,
                "form": 1,
                "label": 5,
                "label_type": "pos",
                "head": 9,
                "relation": 11,
                "relation_type": "deprel"
            }
            ...
        }
        ...

        @:param format_name: the format indicated by client

        @:return: dict of wished format

        {
            "name": "conll09_predicted",
            "id": 0,
            "form": 1,
            "label": 5,
            "label_type": "pos",
            "head": 9,
            "relation": 11,
            "relation_type": "deprel"
        }
    """

    formats = config['formats']
    aliases = config['format_aliases']
    if format_name in formats:
        return formats[format_name]
    elif format_name in aliases:
        format_ = formats[aliases[format_name]]
        return format_
    else:
        raise ValueError('Format {} not supported.'.format(format_name))


class Recommendation(Enum):

    """
    A recommendation that the server sends to the client when an error
    is encountered.
    """
    abort = 1
    retry = 2


class SolutionType(Enum):
    """
    A type of solution.
    'real' is an actual solution and is to be used if only one tree
    remains in a forest.
    'fixed' is not an actual solution and is to be used for labeling an
    incomplete tree consisting of nodes appearing in every tree of the
    forest.
    'best' is not an actual solution and is to be used for labeling a
    complete tree that is the guess at the correct tree in the forest.
    """
    real = 1
    fixed = 2
    best = 3


def create_error(error_message, recommendation=Recommendation.abort):
    """
    Format a message of type error.


    @:param error_message: A human-readable error message.
    @:param recommendation: A Recommendation object telling the client what to do.

    @:return: error message
    """
    error = {
        'type': 'error',
        'error_message': error_message,
        'recommendation': recommendation.name
        }
    return error


def find_tree(forest):

    """
    Find the best tree in the given forest and format it as a tree
    object (assuming the best tree is the first tree).


    @:param forest: A Forest object that may or may not be solved.

    @:return: tree object
    @:rtype: json
    """
    return {
        'tree_format': forest.trees[0].format,
        'nodes': forest.trees[0].nodes,
        'overlays': {
            'treated': forest.get_treated_fields(),
            'fixed': forest.get_fixed_fields()
            }
        }


def create_question(forest):
    """
    Format a message of type question.

    Args:
        forest: A Forest object that is not solved.
    """
    question = {
        'type': 'question',
        'remaining_trees': len(forest.trees),
        'question': forest.question(),
        'best_tree': find_tree(forest)
        }
    return question


def create_solution(forest):
    """
    Format a message of type solution.

    Args:
        forest: A Forest object that may or may not be solved.
        solution_type: A SolutionType object specifying what kind of solution
            message it is going to be. If the solution_type is
            SolutionType.real, the forest should be solved.
    """
    return {
        'type': 'solution',
        'remaining_trees': len(forest.trees),
        'tree': find_tree(forest)
        }


def create_question_or_solution(forest):
    """
    Format either a question or a solution message.

    Args:
        forest: A Forest object.
    """
    if forest.solved():
        return create_solution(forest)
    else:
        return create_question(forest)


def create_forest(request, config):
    """
    Create a Forest object from a client request.


    @:param request: A message of type request (json)
    @:param config: The configuration dict needed for preprocessing instructions

    @:return:
        a forest object created from the conll string in the request
        OR
        a forest object processed by processor and created(later)
    """

    if 'use_forest' in request:

        # {
        #    "type": "request",
        #    "use_forest": "1\tMit\tmit\t_\tADP\tAPPR\t_\t_\t3\t_\t...
        #    "forest_format": "conll09"
        # }

        format_ = request['forest_format']
        try:
            info = get_format_from_config(config, format_) #check if config file contains format, return format dict
        except KeyError as e:
            msg = 'Format not supported: %s'
            logging.warning(msg, format_)
            raise ValueError(msg % format_) from e
        return Forest.from_string(request['use_forest'], format_info=info)
                                 #request['use_forest']: conll string e.g."1\tMit\tmit\t_\tADP\tAPPR\t_\t_\t3\t_\t..."
                                 #info: format dict



#-----------------ignore for now, come back later------------------------------------------
    elif 'process' in request:

        # {
        #     "type": "request",
        #     "process": "Mit Bedacht badet heute ein Lurch in einem See.",
        #     "source_format": "raw",
        #     "target_format": "conll09"
        # }

        try:
            forest_string = process(request, config)
        except ValueError as e:
            msg = 'Cannot convert from source_format %s to target_format %s.'
            logging.warning(msg,
                request['source_format'], request['target_format'])
            raise ValueError(msg % (request['source_format'],
                request['target_format'])) from e
        try:
            info = get_format_from_config(config, request['target_format'])
        except KeyError as e:
            msg = 'target_format %s not supported.'
            logging.warning(msg, request['target_format'])
            raise ValueError(msg % (request['target_format'])) from e
        return Forest.from_string(forest_string, format_info=info)


def choose_processors(available_processors, source_format, target_format):
    """
    Choose a list of processors that can transduce text in a
    source_format into the target_format.

    Args:
        available_processors: A list or tuple of dicts containing at least
        the keys 'source_format' and 'target_format'. They should also contain
        the keys 'name' and 'command'.

        source_format: A string specifying the source format.
        target_format: A string specifying the target format.
    """
    # TODO: This can be made more efficient by saving the possible conversions
    # in the config. The way it is now, we have to iterate over the processor
    # list over and over again.
    # Modifying the config, however, also means that we have to use a lock
    # when accessing the config for writing. Alternatively, all possible
    # conversion could be calculated when the server is started.
    #
    # Also, tree recursion is really cumbersome in Python:
    for p in available_processors:
        if (p['source_format'] == source_format
                and p['target_format'] == target_format):
            return (p,)
    else:
        for p_i, p in enumerate(available_processors):
            if source_format != p['source_format']:
                continue
            remaining_processors = [
                available_processors[i]
                for i in range(len(available_processors))
                if i != p_i
                ]
            additional_processors = choose_processors(remaining_processors,
                p['target_format'], target_format)
            if additional_processors is None:
                return None
            else:
                return (p,) + additional_processors


def call_processor(processor, infile):
    """
    Call a processor that processes the infile and writes to an outfile.

    Args:
        processor: A dict containing the key 'command' with an args list
            as value. A proper processor also contains the keys 'name', 'type',
            'source_format' and 'target_format'.
        infile: A filename that is to be used as the input to the processor
            command.

    Returns:
        outfile: The name of the file the output of the processor is written to.
    """
    # XXX: The whole server process is waiting for the subprocess to return.
    # This kind of defeats the purpose of using asyncio. The subprocess has
    # to be executed asynchronously.
    outfile = tempfile.mktemp()
    cmd_args = [
        arg.format(infile=infile, outfile=outfile)
        for arg in processor['command']
        ]
    call(cmd_args)
    return outfile


def process(request, config):
    """
    Process a sentence using the processors described in the config.

    Args:
        request: A message of type request requesting to process a sentence.
        config: The configuration dict needed for preprocessing instructions.
    """
    try:
        target_format = (
            request['target_format']
            if 'target_format' in request
            else config['default_format']
            )
    except KeyError as e:
        msg = 'Cannot determine target format for parsing.'
        msg += ' Specify a default_format in the configuration file.'
        raise ValueError(msg)

    processors = choose_processors(
        config['processors'],
        request['source_format'],
        target_format
        )

    infile = tempfile.mktemp()
    open(infile, 'w').write(request['process'])
    for processor in processors:
        infile = call_processor(processor, infile)
    outfile = infile

    forest_string = open(outfile).read()
    return forest_string
#------------------------------------------------------------------------------------------------------
