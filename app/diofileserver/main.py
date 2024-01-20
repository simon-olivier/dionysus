import contextlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import socket
import os

PORT:int = os.environ.get('PORT', 6776)
DIRECTORY:str = os.environ.get('DIR', '')

class DioFileServer(ThreadingHTTPServer):

    def server_bind(self):
        # suppress exception when protocol is IPv4
        with contextlib.suppress(Exception):
            self.socket.setsockopt(
                socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        return super().server_bind()

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, directory=DIRECTORY)

if __name__ == '__main__':
    with DioFileServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
        print("Diofileserver listening on: 0.0.0.0:", PORT)
        httpd.serve_forever()
        
