#! /usr/bin/env python
import re, ssl
import argparse
# https://docs.python.org/3/library/http.server.html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
# https://websocket-client.readthedocs.io/en/latest/getting_started.html
from websocket import create_connection, WebSocketException


class WSWebServer(BaseHTTPRequestHandler):
    # Handler for POST requests
    def do_POST(self):
        content_len = int(self.headers.get('content-length', 0))
        post_fuzz_body = self.rfile.read(content_len)
        fuzz_result = FuzzWebSocket(post_fuzz_body)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(fuzz_result, 'utf-8'))
        return

    # Handler for the GET requests
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("WebSocket Fuzzing Harness: Please use POST request!")
        return


def FuzzWebSocket(fuzz_payload):
    # send and recieve a request
    try:
        ws.send(fuzz_payload)
        fuzz_result = ws.recv()
        return fuzz_result
    except WebSocketException as e:
        print('Error:', e.args)
        # TODO: reconnect?


parser = argparse.ArgumentParser(description='Web Socket Harness: Use traditional pentest tools to assess web sockets')
parser.add_argument('-u', '--url', help='The remote WebSocket URL to target. Example: ws://127.0.0.1:8000/method-to-fuzz.', required=True)
parser.add_argument('-p', '--port', help='The port to bind to.', required=True, default=8000)
parser.add_argument('-o', '--origin', help='The value for the Origin: header', required=True)
parser.add_argument('-k', '--custom_header', help='Any single custom header to include within the connection request', required=False)
args = parser.parse_args()

headers = {
    'Connection': 'Upgrade',
    'Sec-WebSocket-Version': '13',
    'Upgrade': 'websocket'
}
if args.origin:
    headers['Origin'] = args.origin

if args.custom_header:
    hdr = re.search('(.+): (.+)', args.custom_header)
    headers[hdr.group(1)] = hdr.group(2)

ws = create_connection(
    args.url,
    sslopt={'cert_reqs': ssl.CERT_NONE},
    header=headers,
    http_proxy_host="127.0.0.1",
    http_proxy_port=8080,
    proxy_type="http")

try:
    # Setting up web harness/proxy server
    server = ThreadingHTTPServer(('', int(args.port)), WSWebServer)
    print('WebSocket Harness: Successful bind on port', args.port)

    # Wait forever for incoming http requests
    server.serve_forever()

except KeyboardInterrupt:
    print('WebSocket Harness: Exit command recieved. Shutting down...')
    server.socket.close()
    ws.close()
