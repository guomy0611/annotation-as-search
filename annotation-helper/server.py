#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
This module provides a stream based server that interfaces between the tree
module and a client wishing to use the tree module for help with annotating.
'''

import argparse
import asyncio
import json
import logging
import socket

# annotation-helper modules
import tree

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
        '''
        Initialize the protocol object when a connection is made and log
        connection information.
        '''
        self.peername = transport.get_extra_info('peername')
        logging.info('Connection from %s', self.peername)
        self.transport = transport
        self.forest = None

    def data_received(self, data):
        '''
        Use received data to update the forest object and send a response to
        the client to prompt them for further action.
        '''
        received = unpack_received_data(data)
        logging.debug('Received %s from %s.', data, self.peername)

        to_be_sent = pack_data_for_sending(self.interpret_data(received))
        self.transport.write(to_be_sent)
        logging.debug('Sent %s to %s.', to_be_sent, self.peername)

    def interpret_data(self, data):
        '''
        Helper function used to decide what to with received data and to
        interface with the forest.
        '''
        response = {}
        if data['type'] == 'request':
            self.forest = tree.Forest.from_request(data)
            response = self.forest.next_response()
        elif data['type'] == 'answer':
            if not isinstance(self.forest, tree.Forest):
                error_messsage = 'Create a forest before answering questions.'
                response = self.create_error(error_messsage)
                logging.info('No-forest error with %s.', self.peername)
            else:
                self.forest.filter(tuple(data['question']), data['answer'])
                response = self.forest.next_response()
        return response

    def create_error(self, error_messsage):
        '''
        Create an error object to be sent to the client.
        '''
        # TODO: Maybe this function should not live in this class.
        error = {
            'type': 'error',
            'error_message': error_messsage,
            'recommendation': 'abort'
            }
        return error

    def connection_lost(self, exc):
        '''
        Log when a connection is terminated.
        '''
        logging.info('Connection to %s lost.', self.peername)

def setup_logging(logfile, loglevel):
    '''
    Set up logging for the server application.

    Args:
        logfile: The name of the logfile.
        loglevel: String representation of one of the default loglevels:
                DEBUG, INFO, WARNING, ERROR or CRITICAL.
    '''
    logging.basicConfig(
        filename=logfile,
        format='%(asctime)s|%(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=getattr(logging, loglevel.upper(), logging.INFO))

def main():
    desc = 'Start a server that sends questions and accepts answers.'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-H',
        '--host',
        required=False,
        type=str,
        default='127.0.0.1',
        help='The host that accepts TCP connections.')
    parser.add_argument(
        '-p',
        '--port',
        required=False,
        type=int,
        default=8080,
        help='The port that accepts TCP connections.')
    parser.add_argument(
        '-s',
        '--unix_socket',
        required=False,
        type=str,
        help='Unix socket file to use instead of host and port.')
    parser.add_argument(
        '-l',
        '--logfile',
        required=False,
        type=str,
        default='',
        help='Name of the log file.')
    parser.add_argument(
        '--loglevel',
        required=False,
        type=str,
        default='INFO',
        help='Log level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    args = parser.parse_args()

    setup_logging(args.logfile, args.loglevel)

    if args.unix_socket:
        incoming_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        incoming_socket.bind(args.unix_socket)
        logging.debug(
            'Bound incoming unix socket to %s.', args.unix_socket)
    else:
        incoming_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        incoming_socket.bind((args.host, args.port))
        logging.debug(
            'Bound incoming tcp socket to %s:%s.', args.host, args.port)

    loop = asyncio.get_event_loop()
    coro = loop.create_server(AnnotationHelperProtocol, sock=incoming_socket)
    server = loop.run_until_complete(coro)
    logging.debug('Started event loop.')

    # Serve requests until Ctrl+C is pressed
    logging.info('Serving on %s.', server.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    logging.info('Closed server.')
    loop.run_until_complete(server.wait_closed())
    loop.close()
    logging.debug('Terminating application.')

if __name__ == '__main__':
    main()
