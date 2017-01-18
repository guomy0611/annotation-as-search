# -*- coding: utf-8 -*-

import asyncio
import json
import types

def pack_data_for_sending(string):
    '''
    Prepare a string for being sent. This includes converting to json.
    '''
    return json.dumps(string).encode()

def unpack_received_data(bytestring):
    '''
    Read a sent bytestring in as a json object.
    '''
    return json.loads(bytestring.decode())

def inform(self, message):
    '''
    Inform the user of what is happening.
    '''
    print(message)

def handle_question(self, question):
    '''
    Generate a response from a question and return it or return None.
    '''
    self.inform('Received question: {}'.format(question))

def handle_solution(self, solution):
    '''
    Generate a response from a solution and return it or return None.
    '''
    self.inform('Received solution: {}'.format(solution))

def handle_error(self, error):
    '''
    Generate a response from an error and return it or return None.
    '''
    self.inform('Received error: {}'.format(error))

def handle_default(self, server_data):
    '''
    Generate a response from a server message that is neither question nor
    solution nor error and return it or return None.
    '''
    self.inform('Cannot cope with server response: {}'.format(server_data))

def find_response(self, server_data):
    '''
    Generate a response from any server message and return it or return None.
    '''
    response = None
    if server_data['type'] == 'question':
        response = self.handle_question(server_data)
    elif server_data['type'] == 'solution':
        response = self.handle_solution(server_data)
    elif server_data['type'] == 'error':
        response = self.handle_error(server_data)
    else:
        response = self.handle_default(server_data)
    return response

class AnnotationHelperClientProtocol(asyncio.Protocol):

    def __init__(
            self,
            loop,
            request_creator,
            inform=inform,
            handle_question=handle_question,
            handle_solution=handle_solution,
            handle_error=handle_error,
            handle_default=handle_default,
            find_response=find_response
            ):
        self.loop = loop
        self.request = request_creator()
        self.inform = types.MethodType(inform, self)
        self.handle_question = types.MethodType(handle_question, self)
        self.handle_solution = types.MethodType(handle_solution, self)
        self.handle_error = types.MethodType(handle_error, self)
        self.handle_default = types.MethodType(handle_default, self)
        self.find_response = types.MethodType(find_response, self)
        self.inform('Initiated protocol instance.')

    def connection_made(self, transport):
        self.transport = transport
        self.peername = self.transport.get_extra_info('peername')
        self.inform('Connected to {}'.format(self.peername))
        self.transport.write(pack_data_for_sending(self.request))
        self.inform('Sent request {}'.format(self.request))

    def data_received(self, data):
        received = unpack_received_data(data)
        self.inform('Received data {}'.format(received))
        response = self.find_response(received)
        if response:
            self.transport.write(pack_data_for_sending(response))
        else:
            self.end_conversation()

    def connection_lost(self, exc):
        self.inform('The connection was closed.')
        self.loop.stop()

    def end_conversation(self):
        self.transport.close()
        self.inform('Closed connection to {}'.format(self.peername))
        self.loop.stop()

def format_tree(tree):
    '''
    Format a tree object as described in the AaSP specification.
    '''
    if tree['tree_format'] in ('conll09', 'conllu'):
        return '\n'.join(
            '\t'.join(elm for elm in node)
            for node
            in tree['nodes']
            ) + '\n'
    else:
        msg_template = 'Cannot format tree with unknown tree_format: {}.'
        raise ValueError(msg_template.format(tree['tree_format']))
