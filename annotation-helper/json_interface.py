# -*- coding: utf-8 -*-

import logging
from enum import Enum
from subprocess import call
import tempfile

class Recommendation(Enum):
    abort = 1,
    retry = 2

class SolutionType(Enum):
    real = 1,
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
        best_tree = forest.best_tree()
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
    for p in processcors:
        if (p['source_format'] == source_format
                and p['target_format'] == target_format):
            return p
    else:
        msg = 'Cannot find processor for source_format %s and target_format %s.'
        logging.error(msg, source_format, target_format)

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
    outfile = tempfile.mkstemp()

    cmd_args = [
        arg.format(infile=infile, outfile=outfile)
        for arg in processor['command']
        ]
    call(cmd_args)

    forest = Forest.from_string(open(outfile).read())
    return forest
