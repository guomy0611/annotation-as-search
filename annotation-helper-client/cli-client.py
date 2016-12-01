#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import socket

from common import unpack_received_data, pack_data_for_sending

def inform(message):
    print(message)

def prompt_for_answer(question):
    print(question['question'])
    answer = input('Correct? (y/n) ')
    return answer.startswith('y')

def display_solution(solution_representation):
    print('Solution:')
    print(solution_representation)

def handle_solution(solution):
    display_solution(solution['nodes'])

def find_response(server_data):
    if server_data['type'] == 'question':
        answer = prompt_for_answer(server_data)
        response = {
                'type': 'answer',
                'answer': answer,
                'question': server_data['question']
                }
        return response
    elif server_data['type'] == 'solution':
        handle_solution(server_data)
        return None
    else:
        inform('Cannot cope with server response: {}'.format(server_data))

def create_request_from_file(conll_file):
    request = {
            'type': 'request',
            'use_forest': open(conll_file).read()
            }
    return request

class AnnotationHelperClientProtocol(asyncio.Protocol):

    def __init__(self, loop, request_creator):
        inform('Initiating protocol instance.')
        self.loop = loop
        self.request = request_creator()

    def connection_made(self, transport):
        self.transport = transport
        self.peername = self.transport.get_extra_info('peername')
        inform('Connected to {}'.format(self.peername))
        self.transport.write(pack_data_for_sending(self.request))

    def data_received(self, data):
        received = unpack_received_data(data)
        inform('Received {}'.format(received))
        response = find_response(received)
        if response:
            self.transport.write(pack_data_for_sending(response))
        else:
            self.end_conversation()

    def connection_lost(self, exc):
        inform('The server closed connection.')
        self.loop.stop()

    def end_conversation(self):
        self.transport.close()
        inform('Closed connection to {}'.format(self.peername))
        self.loop.stop()

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
        inform('Connected to unix socket at {}.'.format(args.unix_socket))
    else:
        socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_to_server.connect((args.host, args.port))
        inform('Connected to tcp socket at {}:{}.'.format(args.host, args.port))

    loop = asyncio.get_event_loop()
    request_creator = lambda : create_request_from_file(args.conll_file)
    coro = loop.create_connection(
            lambda : AnnotationHelperClientProtocol(loop, request_creator),
            sock=socket_to_server
            )
    loop.run_until_complete(coro)
    loop.run_forever()

if __name__ == '__main__':
    main()
