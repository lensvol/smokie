#coding: utf-8

import re
import sys
import json
import requests

HTTP_VERBS = {
    'GET': requests.get,
    'POST': requests.post,
    'PUT': requests.put,
    'OPTIONS': requests.options
}


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


def send_request(host, request):
    verb, uri, http_version = request['request'].split(' ')
    method = HTTP_VERBS[verb]
    expected_status = int(request['status'])

    add_kwargs = {
        'proxies': {'http': ''},
        'data': request['body'].encode('utf-8'),
        'stream': False,
        'headers': {}
    }

    if 'headers' in request:
        for header, value in request.iteritems():
            add_kwargs['headers'][header] = value

    resp = method(host + uri, **add_kwargs)

    print u'[%i] %s @ %s' % (num + 1, resp.status_code, uri),
    if resp.status_code != expected_status:
        print u'--> ERR (expected: %s)' % expected_status
    else:
        print u'--> OK'


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: ./smokie <host> <request store>'

    host = sys.argv[1]

    if sys.argv[2] == '-':
        fp = sys.stdin
    else:
        fp = open(sys.argv[2], 'r')

    for num, request in enumerate(load_json_store(fp)):
        send_request(host, request)

    fp.close()
