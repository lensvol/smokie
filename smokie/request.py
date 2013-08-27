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
    return resp.status_code, resp.headers, resp.raw.read(resp.headers['content-length'])


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


def request_loop(sender_func, request_source, exception_cls):
    for num, request in enumerate(request_source):
        expected_status = int(request['status'])

        code, headers, content = sender_func(request)

        print u'[%i] %s @ %s\n' % (num + 1, code, expected_status)
        if code != expected_status:
            raise exception_cls('[%s] expected %i, but received %i' % (request['request'], expected_status, code))
