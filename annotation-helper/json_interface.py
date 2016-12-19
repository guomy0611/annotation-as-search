# -*- coding: utf-8 -*-

'''
This module serves as an interface between the annotation helper server
and the forest the server uses. It primarily provides functions for
creating and interpreting AaSP messages.
'''

import logging
from enum import Enum
from subprocess import call
import tempfile

class Recommendation(Enum):
    '''
    A recommendation that the server sends to the client when an error
    is encountered.
    '''
    abort = 1
    retry = 2

class SolutionType(Enum):
    '''
    A type of solution.
    'real' is an actual solution and is to be used if only one tree
    remains in a forest.
    'fixed' is not an actual solution and is to be used for labeling an
    incomplete tree consisting of nodes appearing in every tree of the
    forest.
    'best' is not an actual solution and is to be used for labeling a
    complete tree that is the guess at the correct tree in the forest.
    '''
    real = 1
    fixed = 2
    best = 3

def create_error(error_message, recommendation=Recommendation.abort):
    '''
    Format a message of type error.

    Args:
        error_message: A human-readable error message.
        recommendation: A Recommendation object telling the client what to do.
    '''
    error = {
        'type': 'error',
        'error_message': error_message,
        'recommendation': recommendation.name
        }
    return error

def create_question(forest):
    '''
    Format a message of type question.
    
    Args:
        forest: A Forest object that is not solved..
    '''
    question = {
        'type': 'question',
        'remaining_sentences': len(forest.trees),
        'question': forest.question(),
        'fixed_nodes': {
            'tree_format': forest.trees[0].format,
            'nodes': forest.get_fixed_nodes()
        }
    return question

def create_solution(forest, solution_type=SolutionType.real):
    '''
    Format a message of type solution.

    Args:
        forest: A Forest object that may or may not be solved.
        solution_type: A SolutionType object specifying what kind of solution
            message it is going to be. If the solution_type is
            SolutionType.real, the forest should be solved.
    '''
    if solution_type == SolutionType.real:
        nodes = forest.trees[0].nodes
        tree_format = forest.trees[0].format

    elif solution_type == SolutionType.fixed:
        nodes = forest.get_fixed_nodes()
        tree_format = forest.trees[0].format

    elif solution_type == SolutionType.best:
        best_tree = forest.get_best_tree()
        nodes = best_tree.nodes
        tree_format = best_tree.format

    else:
        # This should never happen.
        logging.error('Unknown SolutionType %s', solution_type)
        return create_error(
            'Internal Error: Unknown SolutionType {}'.format(solution_type),
            Recommendation.abort
            )

    solution = {
        'type': 'solution',
        'solution_type': solution_type.name,
        'tree': {
            'tree_format': tree_format,
            'nodes': nodes
            }
        }

def create_question_or_solution(forest):
    '''
    Format either a question or a solution message.

    Args:
        forest: A Forest object.
    '''
    if forest.solved():
        return create_solution(forest)
    else:
        return create_question(forest)

def create_forest(request, config):
    '''
    Create a Forest object from a client request.

    Args:
        request: A message of type request.
        config: The configuration dict needed for preprocessing instructions.
    '''
    if 'use_forest' in request:
        return Forest.from_string(request['use_forest'])
    elif 'process_sentence' in request:
        forest_string = process_sentence(request, config)
        return Forest.from_string(forest_string)

def choose_processor(processors, source_format, target_format):
    '''
    Choose a processor that can transduce text in a source_format into the
    target_format.

    Args:
        processors: A list of dicts containing at least the keys
            'source_format' and 'target_format'. They should also contain
            the keys 'name', 'command' and 'type'.
        source_format: A string specifying the source format.
        target_format: A string specifying the target format.
    '''
    for p in processors:
        if (p['source_format'] == source_format
                and p['target_format'] == target_format):
            return p
    else:
        (msg =
            'Cannot find processor for source_format %s and target_format %s.')
        logging.error(msg, source_format, target_format)

def call_processor(processor, infile):
    '''
    Call a processor that processes the infile and writes to an outfile.

    Args:
        processor: A dict containing the key 'command' with an args list
            as value. A proper processor also contains the keys 'name', 'type',
            'source_format' and 'target_format'.
        infile: A filename that is to be used as the input to the processor
            command.

    Returns:
        outfile: The name of the file the output of the processor is written to.
    '''
    outfile = tempfile.mkstemp()
    cmd_args = [
        arg.format(infile=infile, outfile=outfile)
        for arg in processor['command']
        ]
    call(cmd_args)
    return outfile

def process_sentence(request, config):
    '''
    Process a sentence using the processors described in the config.

    Args:
        request: A message of type request requesting to process a sentence.
        config: The configuration dict needed for preprocessing instructions.
    '''
    try:
        target_format = (
            request['wanted_format']
            if 'wanted_format' in request
            else config['default_format']
            )
    except KeyError as e:
        msg = 'Cannot determine target format for parsing.'
        msg += ' Specify a default_format in the configuration file.'
        logging.error(msg)
    
    processor = choose_processor(
        config['processors'],
        source_format,
        target_format
        )

    infile = tempfile.mkstemp()
    open(infile, 'w').write(request['process_sentence'])
    outfile = call_processor(processor, infile)

    forest = Forest.from_string(open(outfile).read())
    return forest
