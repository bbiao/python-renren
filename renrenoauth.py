#!/usr/bin/env python
#coding=utf-8
# 
# Copyright 2010 RenRen
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A barebones AppEngine application that uses RenRen for login.

This application uses OAuth 2.0 directly rather than relying on renren's
JavaScript SDK for login. It also accesses the RenRen API directly
using the Python SDK. It is designed to illustrate how easy
it is to use the renren Platform without any third party code.

Befor runing the demo, you have to register a RenRen Application and modify the root domain.
e.g. If you specify the redirect_rui as "http://www.example.com/example_uri". The root domain must be "example.com"

@Author Xun Dai<xun.dai@qq.com>

"""

RENREN_APP_API_KEY = "149b13a1d3ca42e4b4fd62548e34dbb2"
RENREN_APP_SECRET_KEY = "c0a2d6b8af354b308c2fe94036883566"


RENREN_AUTHORIZATION_URI = "http://graph.renren.com/oauth/authorize"
RENREN_ACCESS_TOKEN_URI = "http://graph.renren.com/oauth/token"
RENREN_SESSION_KEY_URI = "http://graph.renren.com/renren_api/session_key"
RENREN_API_SERVER = "http://api.renren.com/restserver.do"



import base64
import Cookie
import email.utils
import hashlib
import hmac
import logging
import os.path
import time
import urllib

# Find a JSON parser
try:
    import json
    _parse_json = lambda s: json.loads(s)
except ImportError:
    try:
        import simplejson
        _parse_json = lambda s: simplejson.loads(s)
    except ImportError:
        # For Google AppEngine
        from django.utils import simplejson
        _parse_json = lambda s: simplejson.loads(s)


class RenrenAPIClient(object):
    def __init__(self, session_key = None, api_key = None, secret_key = None):
        self.session_key = session_key
        self.api_key = api_key
        self.secret_key = secret_key
    
    def auth(self):
        args = {
            'client_id': self.api_key,
            'response_type': 'code',
            'redirect_uri': 'http://graph.renren.com/oauth/login_success.html'
        }
        url = RENREN_AUTHORIZATION_URI + "?" + urllib.urlencode(args)
        print 'Please authorize: ' + url
        verification_code = raw_input('PIN: ')

        args = {
            'client_id': self.api_key,
            'client_secret': self.secret_key,
            'code': verification_code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'http://graph.renren.com/oauth/login_success.html'
        }
        response = urllib.urlopen(RENREN_ACCESS_TOKEN_URI + "?" + urllib.urlencode(args)).read()
        access_token = _parse_json(response)["access_token"]

        '''Obtain session key from the Resource Service.'''
        session_key_request_args = {"oauth_token": access_token}
        response = urllib.urlopen(RENREN_SESSION_KEY_URI + "?" + urllib.urlencode(session_key_request_args)).read()
        self.session_key = str(_parse_json(response)["renren_token"]["session_key"])
        print 'Session key: ' + self.session_key

    def request(self, params = None):
        """Fetches the given method's response returning from RenRen API.

        Send a POST request to the given method with the given params.
        """
        params["api_key"] = self.api_key
        params["call_id"] = str(int(time.time() * 1000))
        params["format"] = "json"
        params["session_key"] = self.session_key
        params["v"] = '1.0'
        sig = self.hash_params(params);
        params["sig"] = sig
        
        post_data = None if params is None else urllib.urlencode(params)
        
        #logging.info("request params are: " + str(post_data))
        
        file = urllib.urlopen(RENREN_API_SERVER, post_data)
        
        try:
            s = file.read()
            logging.info("api response is: " + s)
            response = _parse_json(s)
        finally:
            file.close()
        if type(response) is not list and response["error_code"]:
            logging.info(response["error_msg"])
            raise RenRenAPIError(response["error_code"], response["error_msg"])
        return response
    def hash_params(self, params = None):
        hasher = hashlib.md5("".join(["%s=%s" % (self.unicode_encode(x), self.unicode_encode(params[x])) for x in sorted(params.keys())]))
        hasher.update(self.secret_key)
        return hasher.hexdigest()
    def unicode_encode(self, str):
        """
        Detect if a string is unicode and encode as utf-8 if necessary
        """
        return isinstance(str, unicode) and str.encode('utf-8') or str
    def update(message):
        params = {
                    
        }
class RenRenAPIError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code

if __name__ == "__main__":
    rr_client = RenrenAPIClient(None, RENREN_APP_API_KEY, RENREN_APP_SECRET_KEY)
    rr_client.auth()
