#coding: utf-8

import re
import sys
import json
import time
import datetime
import requests

from pytz import reference
from optparse import OptionParser
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


class RequestRecorder(BaseHTTPRequestHandler):

    def record_request(self, method):
        (client_addr, client_port) = self.client_address

        # Python datetime are "naive", so we have to get our timezone by hand
        tz = reference.LocalTimezone()
        now = datetime.datetime.now(tz)
        content_length = self.headers.getheader('Content-Length')
        body = self.rfile.read(int(content_length)) if content_length else u'-'

        # Prepare request info
        request = {
            'timestamp': now.isoformat(),
            'local_time': now.strftime('%d/%b/%Y:%H:%M:%S%z'),
            'request_method': method,
            'time_msec': time.time(),
            'remote_addr': client_addr,
            'user_agent': self.headers.getheader('User-Agent') or '',
            'x_forwarded_for': self.headers.getheader('X-Forwarded-For') or u'',
            'body': body.decode('utf-8'),
            'headers': {}
        }

        for header_line in self.headers.headers:
            name, value = header_line.split(':', 1)
            request['headers'][name] = value.strip()

        parts = re.match(r'http[s]*://([\w\d\.\:\-]+)/(.+)?', self.path)
        request['request'] = u'%s %s %s' % (method, parts.group(1), self.request_version)
        client_method = getattr(requests, method.lower())
        resp = client_method(self.path, headers=request['headers'])

        request['status'] = resp.status_code

        # We need to return received data to client, as if nothing happened.
        self.send_response(resp.status_code)
        for header, value in resp.headers.items():
            if header == 'content-encoding' or header == 'content-length':
                continue
            self.send_header(header, value)
        self.end_headers()

        # python-requests decompresses content received from server,
        # so to make sense we must send it raw body of the response
        self.wfile.write(resp.content)
        self.wfile.flush()

        sys.stdout.write(json.dumps(request))
        sys.stdout.flush()

    def do_POST(self):
        self.record_request('POST')

    def do_GET(self):
        self.record_request('GET')

    def do_PUT(self):
        self.record_request('PUT')

    def do_OPTIONS(self):
        self.record_request('OPTIONS')


if __name__ == '__main__':
    opt_parser = OptionParser()
    opt_parser.add_option('', '--record-at', dest='recorder_iface', default='localhost:8881',
                          metavar='HOST', help='Specify recorder listening point (default: host=localhost, port=8881)')
    (options, args) = opt_parser.parse_args()

    server_class = HTTPServer
    host, port = options.recorder_iface.split(':')
    httpd = server_class((host, int(port)), RequestRecorder)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print 'Capture ended.'

    httpd.server_close()
