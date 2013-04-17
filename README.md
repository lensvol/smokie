smokie
======

An utility to replay "canned" series of Web requests for fun and testing :)

Requests should be recorded in JSON by nginx using this pattern::

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