#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import argparse
import asyncio
import json

# annotation-helper modules
import tree

# Supposed to be replaced by an actual logger.
def log(message):
    print(message)

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

class AnnotationHelperProtocol(asyncio.Protocol):
    '''
    Serverside asyncio protocol that accepts connections from clients.
    The client will request
    '''

    def connection_made(self, transport):
        self.peername = transport.get_extra_info('peername')
        log('Connection from {}'.format(self.peername))
        self.transport = transport
        self.forest = None

    def data_received(self, data):
        received = unpack_received_data(data)
        log('Data received: {!r}'.format(received))

        to_be_sent = self.interpret_data(received)
        log('Sent: {!r}'.format(message))
        self.transport.write(pack_data_for_sending(to_be_sent))

    def interpret_data(self, data):
        response = {}
        if data['type'] == 'request':
            self.forest = tree.Forest.from_request(data)
            response = self.forest.format_question()
        elif data['type'] == 'answer':
            if not isinstance(self.forest, tree.Forest):
                error_messsage = 'Create a forest before answering questions.'
                response = self.create_error(error_messsage)
            else:
                response = self.forest.format_question()
        return response
    
    def create_error(self, error_messsage):
        return {'type': 'error', 'error_message': error_messsage}

    def connection_lost(self, exc):
        log('Connection to {} lost.'.format(self.peername))

def main():
    desc = 'Start a server that sends questions and accepts answers.'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--port', required=False, type=int,
            default=8080, help='The port that accepts TCP connections.')
    parser.add_argument('-c', '--clients', required=False, type=int,
            default=5, help='Maximum number of allowed clients.')
    args = parser.parse_args()

    incoming_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    incoming_socket.bind(('127.0.0.1', args.port))

    loop = asyncio.get_event_loop()
    # Each client connection will create a new protocol instance
    coro = loop.create_server(AnnotationHelperProtocol, sock=incoming_socket)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

if __name__ == '__main__':
    main()
