import socket
import argparse
import asyncio

def log(message):
    """Supposed to be replaced by an actual logger."""
    print(message)

class AnnotationHelperProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.peername = transport.get_extra_info('peername')
        log('Connection from {}'.format(self.peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        log('Data received: {!r}'.format(message))

        log('Send: {!r}'.format(message))
        self.transport.write(data)
    
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
