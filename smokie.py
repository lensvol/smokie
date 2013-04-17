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


class UnexpectedStatusError(Exception):
    pass


# Ugly hack to get around NGINX encoding of request body
# (http://stackoverflow.com/questions/8011692/valueerror-in-decoding-json)
def load_json_store(fn):
    def asciirepl(match):
        return '\\u00' + match.group()[2:]

    p = re.compile(r'\\x(\w{2})')

    with open(fn, 'r') as fp:
        while True:
            line = fp.readline()
            if not line:
                break
            line = p.sub(asciirepl, line.strip())
            yield json.loads(line)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: ./smokie <host> <request store>'

    host = sys.argv[1]

    for num, request in enumerate(load_json_store(sys.argv[2])):
        verb, uri, http_version = request['request'].split(' ')
        method = HTTP_VERBS[verb]
        body = request['body'].encode('utf8') or None
        expected_status = int(request('status'))

        resp = method(host + uri, proxies={'http': ''}, data=body)
        if resp.status_code != expected_status:
            raise UnexpectedStatusError(u'%s @ %s (expected: %s)' % (resp.status_code, uri, expected_status))