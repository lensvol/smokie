#coding: utf-8

import re
import json
import requests


def send_request(host, request, proxies=None, no_proxy=False):
    verb, uri, http_version = request['request'].split(' ')
    add_kwargs = {
        'data': request['body'].encode('utf-8'),
        'stream': True,
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
    return resp


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
