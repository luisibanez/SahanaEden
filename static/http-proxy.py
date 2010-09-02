#!/usr/bin/python

# 
# Copyright (C) 2007  Camptocamp
#  
# This file is part of MapFish
#  
# MapFish is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# MapFish is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#  
# You should have received a copy of the GNU Lesser General Public License
# along with MapFish.  If not, see <http://www.gnu.org/licenses/>.
#

"""

HTTP proxy that can be used to get around browser restrictions that prevent
cross-domain Ajax requests. It supports GET, POST, PUT, DELETE, and probably
any HTTP method.

That script works as a Apache mod_python handler. Example of Apache config
(assuming this script is place in the directory /var/www/proxy/):

Alias /proxy/ /var/www/proxy
<Directory "/var/www/proxy">
    AddHandler python-program .py
    PythonHandler http-proxy
</Directory>

The target URL is specified in the URL path. Example:

GET /proxy/http-proxy.py/http,host.domain,81/dir/file?key=value

In this example, the request will be forwared to this URL:
http://host.domain:81/dir/file?key=value

"""


from mod_python import apache, util

import httplib2

allowed_hosts = ['localhost:5000']

def error(req, status):
    req.send_http_header()
    raise apache.SERVER_RETURN, status

def handler(req):
    try:
        #
        # Build target URL
        #
        path_info = req.path_info.split('/')
        target_host_info = path_info[1].split(',')
        target_host_info_len = len(target_host_info)
        if target_host_info_len < 2 or target_host_info_len > 3:
            error(req, apache.HTTP_BAD_REQUEST)

        protocol = target_host_info[0]
        if protocol != "http" and protocol != "https":
            error(req, apache.HTTP_BAD_REQUEST)

        host = target_host_info[1]
        if target_host_info_len > 2:
            host += ':' + target_host_info[2]
        if host not in allowed_hosts:
            error(req, apache.HTTP_FORBIDDEN)

        url = protocol + '://' + host

        target_path_info = '/'.join(path_info[2:])
        if len(target_path_info) > 0:
            url += '/' + target_path_info

        method = req.method

        params = ''
        if method == "GET":
            fs = util.FieldStorage(req)
            if len(fs):
                params_list = [k + "=" + fs[k] for k in fs.keys()] 
                params = '&'.join(params_list)
        if len(params) > 0:
            url += '?' + params

        #
        # Get body (POST, PUT)
        #
        body = None
        if method == "POST" or method == "PUT":
            body = req.read()

        #
        # Forward request to target
        #
        http = httplib2.Http()
        req.headers_in['Host'] = host # or it won't work with multi-host web servers
        resp, content = http.request(url, method=method, body=body, headers=req.headers_in)
        if resp.has_key('content-type'):
            req.content_type = resp['content-type']
        else:
            req.content_type = 'text/plain'

        #
        # Send response to client
        #
        req.status = resp.status
        req.send_http_header()
        req.write(content)
        return apache.OK

    except Exception, e:
        error(req, apache.HTTP_INTERNAL_SERVER_ERROR)
