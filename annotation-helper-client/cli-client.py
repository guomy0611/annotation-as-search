#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import socket

from common import (
    unpack_received_data,
    pack_data_for_sending,
    AnnotationHelperClientProtocol
    )

def prompt_for_answer(question):
    print(question['question'])
    answer = input('Correct? (y/n) ')
    return answer.startswith('y')

def display_solution(tree):
    print('Solution:')
    print(tree)

def handle_solution(self, solution):
    display_solution(solution['nodes'])

def handle_question(self, question):
    answer = prompt_for_answer(question)
    response = {
        'type': 'answer',
        'answer': answer,
        'question': question['question']
        }
    return response

def create_request_from_file(conll_file):
    request = {
        'type': 'request',
        'use_forest': open(conll_file).read()
        }
    return request

def main():
    desc = '''Start a client that connects with the annotation-helper server
    and helps with annotating sentences.'''
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-H', '--host', required=False, type=str,
        default='127.0.0.1', help='The host that accepts TCP connections.')
    parser.add_argument('-p', '--port', required=False, type=int,
        default=8080, help='The port that accepts TCP connections.')
    parser.add_argument('-s', '--unix_socket', required=False, type=str,
        help='Unix socket file to use instead of host and port.')
    parser.add_argument('-f', '--conll_file', required=True, type=str,
        help='Path of a file containing a forest.')
    args = parser.parse_args()

    if args.unix_socket:
        socket_to_server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        socket_to_server.connect(args.unix_socket)
    else:
        socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_to_server.connect((args.host, args.port))

    loop = asyncio.get_event_loop()
    request_creator = lambda : create_request_from_file(args.conll_file)
    coro = loop.create_connection(
        lambda : AnnotationHelperClientProtocol(
            loop,
            request_creator,
            handle_question=handle_question,
            handle_solution=handle_solution
            ),
        sock=socket_to_server
        )
    loop.run_until_complete(coro)
    loop.run_forever()

if __name__ == '__main__':
    main()
