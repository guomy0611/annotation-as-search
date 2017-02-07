#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
The cli-client module serves as a simple commandline client conforming
to the Annotation as Search Protocol.
'''

import argparse
import asyncio
from enum import Enum
import socket
import sys

from common import (
    AnnotationHelperClientProtocol,
    format_tree
    )

class UserAction(Enum):
    '''
    Possible actions the user can take.
    '''
    yes = 1
    no = 2
    undo = 3
    abort = 4
    save = 5
    exit = 6
    process_request = 7
    forest_request = 8

ARGUMENT_OBLIGATORY_ACTIONS = (
    UserAction.save,
    UserAction.process_request,
    UserAction.forest_request
    )

def perform_yes(question):
    '''
    Return a yes AaSP message.
    '''
    return {
        'type': 'answer',
        'answer': True,
        'question': question
        }

def perform_no(question):
    '''
    Return a yes AaSP message.
    '''
    return {
        'type': 'answer',
        'answer': False,
        'question': question
        }

def perform_undo(answers):
    '''
    Return an undo AaSP message.
    '''
    return {
        'type': 'undo',
        'answers': int(answers.split()[0])
        }

def perform_save(filename, tree):
    '''
    Save a tree in a file.
    '''
    open(filename, 'w').write(format_tree(tree))
    print('Saved tree to {}'.format(filename))

def perform_exit(exit_code=0):
    '''
    Terminate the program with the given exit_code.
    '''
    sys.exit(exit_code)

def perform_abort():
    '''
    Return an abort AaSP message.
    '''
    return {
        'type': 'abort'
        }

def perform_process_request(sentence, default_target='conll09',
        default_source='raw'):
    '''
    Ask the user for source and target format and return a process AaSP
    message.
    '''
    prompt = "What format have you provided? (Default: {}) "
    user_provided = input(prompt.format(default_source))
    source_format = user_provided or default_source
    prompt = "What format do you want? (Default: {}) "
    user_provided = input(prompt.format(default_target))
    target_format = user_provided or default_target
    return {
        'type': 'request',
        'process': sentence,
        'source_format': source_format,
        'target_format': target_format
        }

def perform_forest_request(forest_filename, default_format='conll09'):
    '''
    Ask the user for the foreset format and return a use_forest AaSP
    message.
    '''
    prompt = "What's the given forest's format? (Default: {}) "
    user_provided = input(prompt.format(default_format))
    forest_format = user_provided or default_format
    return {
        'type': 'request',
        'use_forest': open(forest_filename).read(),
        'forest_format': forest_format
        }

def perform_user_action(user_action, argument=None, **message_properties):
    '''
    Given a UserAction object and an argument, perform the UserAction
    using the argument.
    '''
    if user_action is UserAction.yes:
        return perform_yes(message_properties['question'])
    elif user_action is UserAction.no:
        return perform_no(message_properties['question'])
    elif user_action is UserAction.undo:
        return perform_undo(argument or '1')
    elif user_action is UserAction.abort:
        return perform_abort()
    elif user_action is UserAction.save:
        return perform_save(argument, message_properties['tree'])
    elif user_action is UserAction.process_request:
        return perform_process_request(argument)
    elif user_action is UserAction.forest_request:
        return perform_forest_request(argument)
    elif user_action is UserAction.exit:
        return perform_exit()
    else:
        raise ValueError('{} is not a valid UserAction.'.format(user_action))

def format_user_action_hint(user_action):
    '''
    Given a UserAction object, return a string describing the user
    action and possible arguments.
    '''
    first_letter = user_action.name[0]
    rest = user_action.name[1:]

    if user_action is UserAction.undo:
        description = 'undo n answers'
        argument = ' [n]'
    elif user_action is UserAction.save:
        description = 'save to file'
        argument = ' file'
    elif user_action is UserAction.process_request:
        description = 'send process request'
        argument = ' sentence'
    elif user_action is UserAction.forest_request:
        description = 'send use_forest request'
        argument = ' forest_file'
    else:
        description = user_action.name
        argument = ''

    formatted = '{first_letter}[{rest}]{argument} = {description}'.format(
        first_letter=first_letter,
        rest=rest,
        argument=argument,
        description=description
        )
    return formatted

def prompt_for_user_action(*user_actions):
    '''
    Prompt the user for an action. Only actions in user_actions are accepted.
    '''
    assert(all(isinstance(ua, UserAction) for ua in user_actions))
    hints = ', '.join(format_user_action_hint(ua) for ua in user_actions)
    prompt = '({})\n> '.format(hints)
    action = None
    while action is None:
        user_input = input(prompt).strip()

        user_input_parts = user_input.split(maxsplit=1)
        action_string = user_input_parts[0]
        argument = user_input_parts[1] if len(user_input_parts) > 1 else None
        for ua in user_actions:
            if ua.name.startswith(action_string):
                action = ua
                if action in ARGUMENT_OBLIGATORY_ACTIONS and argument is None:
                    action = None
                else:
                    return action, argument
        else:
            print('Invalid input.')

def display_solution(tree):
    '''
    Display a tree to the user.
    '''
    print('Solution:')
    print(format_tree(tree))

def handle_solution(self, solution):
    '''
    Ask the user what to do with a solution message.
    '''
    display_solution(solution['tree'])

    action, argument = prompt_for_user_action(
        UserAction.undo,
        UserAction.save,
        UserAction.exit
        )
    response = perform_user_action(
        action,
        argument,
        tree=solution['tree']
        )

    if response:
        return response
    else:
        self.end_conversation()

def display_question(question):
    '''
    Display a question to the user.
    '''
    sent = ' '.join([n[1] for n in question['best_tree']['nodes']])
    print('\n{}'.format(sent))
    qo = question['question']
    s = '{head} ---{relation}---> {dependent}\n'
    s = s.format(head=qo['head'], relation=qo['relation'],
        dependent=qo['dependent'])
    print(s)

def handle_question(self, question):
    '''
    Put a question to the user and collect their response.
    '''
    display_question(question)

    action, argument = prompt_for_user_action(
        UserAction.yes,
        UserAction.no,
        UserAction.undo,
        UserAction.abort,
        UserAction.save,
        UserAction.exit
        )
    response = perform_user_action(
        action,
        argument,
        question=question['question'],
        tree=question['best_tree']
        )

    if response:
        return response
    else:
        self.end_conversation()

def display_error(error):
    '''
    Display an error to the user.
    '''
    msg = 'Error: {}'
    print(msg.format(error['error_message']))

def handle_error(self, error):
    '''
    'Handle' an error message. This is actually just displaying it and
    exiting.
    '''
    display_error(error)
    sys.exit(1)

def create_request(forest_file=None):
    '''
    Generate a request either from a given file or by asking the user.
    '''
    if forest_file:
        request = perform_forest_request(forest_file)
    else:
        action, argument = prompt_for_user_action(
            UserAction.forest_request,
            UserAction.process_request,
            UserAction.exit
            )
        request = perform_user_action(action, argument)
    return request

def main():
    '''
    The main function is used to start the connection to the AaS server
    and create the asyncio event loop.
    '''
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

    loop = asyncio.get_event_loop()
    request_creator = lambda : create_request(args.conll_file)
    coro = loop.create_connection(
        lambda : AnnotationHelperClientProtocol(
            loop,
            request_creator,
            # Don't inform the user about boring client-server-communication.
            inform=lambda self, message: 0,
            handle_question=handle_question,
            handle_error=handle_error,
            handle_solution=handle_solution
            ),
        sock=socket_to_server
        )
    loop.run_until_complete(coro)
    loop.run_forever()

if __name__ == '__main__':
    main()
