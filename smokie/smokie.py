#coding: utf-8

import sys
from optparse import OptionParser

from request import send_request, load_json_store, request_loop


if __name__ == '__main__':
    opt_parser = OptionParser()
    opt_parser.add_option('', '--proxy', dest='proxy', help='Proxy server (e.g. "http://user@passlocalhost:81/")')
    opt_parser.add_option('', '--no-proxy', dest='no_proxy',
                          action='store_true', default=False,
                          help='Don\'t use proxies')
    opt_parser.add_option('', '--delay', dest='delay', default=0.0,
                          help='Delay between between attempts to send requests (in seconds, floats allowed)')
    (options, args) = opt_parser.parse_args()

    if len(args) == 0:
        opt_parser.print_help()
        exit(-1)

    if args[1] == '-':
        fp = sys.stdin
    else:
        fp = open(args[1], 'r')

    kw = {
        'no_proxy': options.no_proxy,
        'proxies': {
            'http': options.proxy,
            'https': options.proxy
        }
    }

    request_loop(lambda x: send_request(args[0], x, **kw), load_json_store(fp), AssertionError)

    fp.close()
