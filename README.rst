smokie
======

An utility to replay "canned" series of Web requests for fun and testing :)

Usage
=====
$ python ./smokie.py --help
Usage: smokie.py [options]

Options:
  -h, --help        show this help message and exit
  --proxy=PROXY     Proxy server (e.g. "http://user@passlocalhost:81/")
  --no-proxy        Don't use proxies
  --delay=DELAY     Delay between between attempts to send requests (in seconds)
  --recorder        Start proxy (outputs to stdin)
  --record-at=HOST  Specify recorder listening point (default: host=localhost,
                    port=8881)

Recording requests
==================

1) `nginx access_log <http://nginx.org/en/docs/http/ngx_http_log_module.html>`_:

::

    log_format request_data '{"timestamp": "$time_iso8601", '
                           '"time_local": "$time_local", '
                           '"remote_addr": "$remote_addr", '
                           '"x_forwarded_for": "$http_x_forwarded_for",'
                           '"request": "$request", '
                           '"user_agent": "$http_user_agent", '
                           '"status": "$status", '
                           '"request_method": "$request_method", '
                           '"body": "$request_body", '
                           '"headers": {}, '
                           '"time_msec": "$msec" '
                           '}';

    access_log /var/log/nginx_requests.log request_data;

2) Using internal request recorder as a proxy:

::

$ ./recorder.py --record-at=localhost:7777

It will listen for requests at specified port and interface (localhost:8888 by default)
and forward them to specified host, while proxying it answers back to you. Formatted
JSON dictionary with parsed data will be printed to stdout.

Playing back
============
::

$ ./smokie.py http://google.com google_requests.log

or, if you want to read requests from stdin

::

$ ./smokie.py http://google.com -