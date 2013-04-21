#coding: utf-8

import re
import sys
import json
import time
import requests

from optparse import OptionParser


# Ugly hack to get around NGINX encoding of request body
# (http://stackoverflow.com/questions/8011692/valueerror-in-decoding-json)
def load_json_store(fp):
    def asciirepl(match):
        return '\\u00' + match.group()[2:]

    p = re.compile(r'\\x(\w{2})')

    while True:
        line = fp.readline()
        if not line:
            break
        line = p.sub(asciirepl, line.strip())
        yield json.loads(line)


def send_request(host, request, proxies=None, no_proxy=False):
    verb, uri, http_version = request['request'].split(' ')
    expected_status = int(request['status'])

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

    print u'[%i] %s @ %s' % (num + 1, resp.status_code, uri),
    if resp.status_code != expected_status:
        print u'--> ERR (expected: %s)' % expected_status
    else:
        print u'--> OK'


if __name__ == '__main__':
    opt_parser = OptionParser()

    opt_parser.add_option('', '--proxy', dest='proxy', help='Proxy server (e.g. "http://user@passlocalhost:81/")')
    opt_parser.add_option('', '--no-proxy', dest='no_proxy',
                          action='store_true', default=False,
                          help='Don\'t use proxies')
    opt_parser.add_option('', '--delay', dest='delay', default=0.0,
                          help='Delay between between attempts to send requests')
    (options, args) = opt_parser.parse_args()

    if len(args) < 2:
        print 'Usage: ./smokie <host> <request store>'

    host = args[0]

    if args[1] == '-':
        fp = sys.stdin
    else:
        fp = open(args[1], 'r')

    for num, request in enumerate(load_json_store(fp)):
        send_request(host, request,
                     no_proxy=options.no_proxy, proxies={
                         'http': options.proxy
                     })
        time.sleep(float(options.delay))

    fp.close()
