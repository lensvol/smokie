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

HOST = None

def load_json_store(fp):
    def asciirepl(match):
        return '\\u00' + match.group()[2:]

    p = re.compile(r'\\x(\w{2})')

    while True:
        line = fp.readline()
        if not line:
            break

        # Ugly hack to get around NGINX encoding of request body
        # (http://stackoverflow.com/questions/8011692/valueerror-in-decoding-json)
        line = p.sub(asciirepl, line.strip())
        yield json.loads(line)


def send_request(host, request, proxies=None, no_proxy=False):
    verb, uri, http_version = request['request'].split(' ')
    add_kwargs = {
        'data': request['body'].encode('utf-8'),
        'stream': False,
        'headers': {}
    }

    if 'headers' in request:
        for header, value in request['headers'].iteritems():
            add_kwargs['headers'][header] = value

    sess = requests.Session()
    if no_proxy:
        add_kwargs['proxies'] = dict(http='', https='')
        sess.trust_env = False

    method = getattr(sess, verb.lower())
    resp = method(host + uri, **add_kwargs)
    return resp.status_code, resp.content


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
            'request': u'%s %s %s' % (method, self.path, self.request_version),
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

        status, content = send_request(HOST, request)
        request['status'] = status

        print json.dumps(request)

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

    opt_parser.add_option('', '--proxy', dest='proxy', help='Proxy server (e.g. "http://user@passlocalhost:81/")')
    opt_parser.add_option('', '--no-proxy', dest='no_proxy',
                          action='store_true', default=False,
                          help='Don\'t use proxies')
    opt_parser.add_option('', '--recorder', dest='use_recorder', default='False',
                          action='store_true', help='Start proxy (outputs to stdin)')
    opt_parser.add_option('', '--record-at', dest='recorder_iface', default='localhost:8881',
                          metavar='HOST', help='Specify recorder listening point (default: host=localhost, port=8881)')

    (options, args) = opt_parser.parse_args()

    HOST = args[0]

    if options.use_recorder:
        server_class = HTTPServer
        host, port = options.recorder_iface.split(':')
        httpd = server_class((host, int(port)), RequestRecorder)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print 'Capture ended.'

        httpd.server_close()
    else:
        if args[1] == '-':
            fp = sys.stdin
        else:
            fp = open(args[1], 'r')

        for num, request in enumerate(load_json_store(fp)):
            expected_status = request['status']

            resp_status, content = send_request(HOST, request,
                                                no_proxy=options.no_proxy, proxies={
                                                    'http': options.proxy
                                                })

            print u'[%i] %s @ %s' % (num + 1, resp_status, expected_status),
            if resp_status != expected_status:
                print u'--> ERR (expected: %s)' % expected_status
            else:
                print u'--> OK'

        fp.close()
