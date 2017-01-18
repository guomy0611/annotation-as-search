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
import os

# annotation-helper modules
import tree
from json_interface import (
    create_error,
    create_question_or_solution,
    create_solution,
    create_forest,
    Recommendation,
    SolutionType
    )

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

    def __init__(self, config, forest=None):
        '''
        Initialize the protocol object with the config dict.
        '''
        self.config = config
        self.forest = forest

    def connection_made(self, transport):
        '''
        Initialize the protocol object when a connection is made and log
        connection information.
        '''
        self.peername = transport.get_extra_info('peername')
        logging.info('Connection from %s', self.peername)
        self.transport = transport

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
        if 'type' not in data:
            reponse = create_error('No message type')
            logging.info('No-message-type error with %s.', self.peername)

        elif data['type'] == 'request':
            self.forest = create_forest(data, self.config)
            response = create_question_or_solution(self.forest)

        elif data['type'] == 'answer':
            if not isinstance(self.forest, tree.Forest):
                error_messsage = 'Create a forest before answering questions.'
                response = create_error(error_messsage)
                logging.info('No-forest error with %s.', self.peername)
            else:
                self.forest.filter(tuple(data['question']), data['answer'])
                response = create_question_or_solution(self.forest)

        elif data['type'] == 'undo':
            self.forest.undo(data['answers'] if 'answers' in data else 1)
            response = create_question_or_solution(self.forest)

        elif data['type'] == 'abort':
            response = create_solution(
                    self.forest,
                    SolutionType[data['wanted']]
                    )

        else:
            reponse = create_error(
                'Unknown message type: {}'.format(data['type'])
                )
            logging.info('Unknown-message-type error with %s.', self.peername)

        return response

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

def read_configfile(configfile):
    '''
    Read a json-formatted configuration file and return the resulting dict.
    '''
    return json.load(open(configfile))

def update_config(config, new_pairs):
    '''
    Update the config dict with the key-value-pairs in new_data.

    Args:
        config: The current configuration dict.
        new_pairs: A dict or an argparse.Namespace containing the
            key-value-pairs that are to be inserted. In the case of a
            namespace, only names not starting with an underscore are added to
            the config.
    '''
    if isinstance(new_pairs, dict):
        config.update(new_pairs)
    elif isinstance(new_pairs, argparse.Namespace):
        for key in dir(new_pairs):
            if not key.startswith('_'):
                config[key] = getattr(new_pairs, key)
    else:
        msg = '{} is neither a dict nor an argparse.Namespace.'
        raise TypeError(msg.format(new_pairs))

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
        '--unixsocket',
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
    parser.add_argument(
        '-c',
        '--configfile',
        required=False,
        type=str,
        default=os.path.join(os.environ['HOME'], '.aas-server.json'),
        help='Name of the config file.')
    args = parser.parse_args()

    config = read_configfile(args.configfile)
    update_config(config, args)
    setup_logging(args.logfile, args.loglevel)
    logging.debug('Read configuration from %s', args.configfile)

    # Determine socket to bind to.
    # TODO: Don't use unixsocket from configfile, if host and port were
    # specified using commandline options.
    if 'unixsocket' in config and config['unixsocket']:
        incoming_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        incoming_socket.bind(config['unixsocket'])
        logging.debug(
            'Bound incoming unix socket to %s.', config['unixsocket'])
    else:
        incoming_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        incoming_socket.bind((config['host'], config['port']))
        logging.debug(
            'Bound incoming tcp socket to %s:%s.', config['host'], config['port'])

    loop = asyncio.get_event_loop()
    coro = loop.create_server(
        lambda : AnnotationHelperProtocol(config),
        sock=incoming_socket
        )
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
