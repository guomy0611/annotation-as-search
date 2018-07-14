#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module provides a stream based server that interfaces between the tree
module and a client wishing to use the tree module for help with annotating.
"""

import argparse
import asyncio
import json
import logging
import socket
import os

# aas_server modules
import tree
from json_interface import (
    create_error,
    create_question_or_solution,
    create_solution,
    create_forest,
    subcat_tree,
    Recommendation,
    SolutionType
    )

def encode_message(message):
    """
    Prepare a message for being sent. This includes converting to json.
    """
    return json.dumps(message).encode()

def decode_message(bytestring):
    """
    Read a sent bytestring in as a json object.
    """
    return json.loads(bytestring.decode())

def pack_message(bytestring):
    """
    Prefix a bytestring by its length and a null byte. This prefix is
    used after sending to extract the message at the receiving side.
    """
    return str(len(bytestring)).encode() + b'\0' + bytestring

class AnnotationHelperProtocol(asyncio.Protocol):
    """
    Serverside asyncio protocol that accepts connections from clients.
    The client will request
    """

    def __init__(self, config, forest=None):
        """
        Initialize the protocol object with the config dict.
        """
        self.config = config
        self.forest = forest
        self.message_buffer = b''

    def get_message(self):
        """
        Read a complete binary message from a message buffer. The
        message is stripped of its length indicator and only the 'payload'
        is returned.
        """
        separator_index = self.message_buffer.index(0)
        message_length_part = self.message_buffer[0:separator_index]
        try:
            message_length = int(message_length_part.decode())
        except ValueError as e:
            logging.warning('Invalid message length: %s', message_length_part)
            return None

        if len(self.message_buffer) > message_length + separator_index:
            # Entire message is in buffer and ready to be read.
            inclusive_start = separator_index + 1
            exclusive_end = separator_index + 1 + message_length
            binary_message = self.message_buffer[inclusive_start:exclusive_end]
            self.message_buffer = self.message_buffer[exclusive_end:]
            return binary_message
        else:
            # Message is not ready to be read. We cannot return a message.
            return None

    def connection_made(self, transport):
        """
        Initialize the protocol object when a connection is made and log
        connection information.
        """
        self.peername = transport.get_extra_info('peername')
        logging.info('Connection from %s', self.peername)  #Connection from ('127.0.0.1', 51884)
        self.transport = transport

    def data_received(self, data):
        """
        Use received data to update the forest object and send a response to
        the client to prompt them for further action.
        """
        self.message_buffer += data
        logging.debug('Received %s from %s.', data, self.peername)
        binary_message = self.get_message()
        if binary_message:
            message = decode_message(binary_message)
            logging.info('Read message %s from %s.', message, self.peername)
            binary_response = encode_message(self.interpret_message(message))
            self.transport.write(pack_message(binary_response))
            logging.debug('Sent %s to %s.', binary_response, self.peername)

    def interpret_message(self, data):
        """
        Helper function used to decide what to with decoded message and to
        interface with the forest.

        @:param data: message received from client

        # {
        #     "type": "answer",
        #     "question": {
        #         "head" : "badet-3",
        #         "dependent": "Lurch-6",
        #         "relation": "SB",
        #         "relation_type": "deprel"
        #     },
        #     "answer": true
        # }
        """

        response = {}
        if 'type' not in data:
            response = create_error('No message type') #-> sends response back to client
            logging.info('No-message-type error with %s.', self.peername) #-> logging

        elif data['type'] == 'subcat':
            try:
                self.forest = create_forest(data, self.config)
            except ValueError as e:
                msg = 'Cannot create forest. ({})'.format(e)
                response = create_error(msg)
                logging.info('Cannot-create-forest error with %s.', self.peername)
                return response
            except Exception as e:
                msg = 'Cannot create forest. ({})'.format(e)
                response = create_error(msg)
                msg = 'Unexpected exception: {} with %s'.format(e)
                logging.error(msg, self.peername)
                return response

            response = subcat_tree(self.forest, data['subcat'])
            print("server", data["subcat"])

        #1
        elif data['type'] == 'request':
            try:
                self.forest = create_forest(data, self.config)
            except ValueError as e:
                msg = 'Cannot create forest. ({})'.format(e)
                response = create_error(msg)
                logging.info('Cannot-create-forest error with %s.', self.peername)
                return response
            except Exception as e:
                msg = 'Cannot create forest. ({})'.format(e)
                response = create_error(msg)
                msg = 'Unexpected exception: {} with %s'.format(e)
                logging.error(msg, self.peername)
                return response

            response = create_question_or_solution(self.forest)    #start asking questions

        #2
        elif data['type'] == 'answer':
            if not isinstance(self.forest, tree.Forest):
                error_messsage = 'Create a forest before answering questions.'
                response = create_error(error_messsage)
                logging.info('No-forest error with %s.', self.peername)
            else:
                self.forest.filter(data['question'], data['answer']) #filter???
                response = create_question_or_solution(self.forest)    #keep asking questions

        #3
        elif data['type'] == 'undo':
            self.forest.undo(data['answers'] if 'answers' in data else 1)
            response = create_question_or_solution(self.forest)

        #4
        elif data['type'] == 'abort':
            response = create_solution(self.forest)

        #5
        else:
            response = create_error(
                'Unknown message type: {}'.format(data['type'])
                )
            logging.info('Unknown-message-type error with %s.', self.peername)

        return response

    def connection_lost(self, exc):
        """
        Log when a connection is terminated.
        """
        logging.info('Connection to %s lost.', self.peername)


def setup_logging(logfile, loglevel):
    """
    Set up logging for the server application.

    Args:
        logfile: The name of the logfile.
        loglevel: String representation of one of the default loglevels:
                DEBUG, INFO, WARNING, ERROR or CRITICAL.
    """
    logging.basicConfig(
        filename=logfile,
        format='%(asctime)s|%(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=getattr(logging, loglevel.upper(), logging.INFO))

def read_configfile(configfile):
    """
    Read a json-formatted configuration file and return the resulting dict.
    """
    try:
        return json.load(open(configfile))
    except FileNotFoundError as e:
        return dict()

def update_config(config, new_pairs):
    """
    Update the config dict with the key-value-pairs in new_data.

    Args:
        config: The current configuration dict.
        new_pairs: A dict or an argparse.Namespace containing the
            key-value-pairs that are to be inserted. In the case of a
            namespace, only names not starting with an underscore are added to
            the config. If a vale is None, the pair is ignored.
    """
    if isinstance(new_pairs, dict):
        config.update({k: v for k, v in new_pairs.items() if v is not None})
    elif isinstance(new_pairs, argparse.Namespace):
        for key in dir(new_pairs):
            if not key.startswith('_'):
                value = getattr(new_pairs, key)
                if value is not None:
                    config[key] = value
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
        help='The host that accepts TCP connections.')
    parser.add_argument(
        '-p',
        '--port',
        required=False,
        type=int,
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
        help='Name of the log file.')
    parser.add_argument(
        '--loglevel',
        required=False,
        type=str,
        help='Log level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    parser.add_argument(
        '-c',
        '--configfile',
        required=False,
        type=str,
        help='Name of the config file.')
    args = parser.parse_args()

    # Default configuration
    config = {
        'host': '0.0.0.0',
        'port': 8000,
        'logfile': '',
        'loglevel': 'INFO',
        'formats': {},
        'format_aliases': {},
        'configfile': os.path.join(os.environ['HOME'], '.aas-server.json')
        }

    configfile = (args.configfile if 'configfile' in args
        else config['configfile'])
    if os.path.isfile(configfile):
        config_from_file = read_configfile(configfile)
        update_config(config, config_from_file)

    update_config(config, args)
    setup_logging(config['logfile'], config['loglevel'])

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
