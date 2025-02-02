#!/usr/bin/env python
# Copyright (c) 2015 Mirantis, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import requests
import socket

from six.moves import http_client
from six.moves.urllib import error

from yretry import decorators
from yretry import defaults


RETRY_SOCKET_EXCEPTIONS = (socket.error, socket.timeout)
RETRY_HTTPLIB_EXCEPTIONS = (http_client.BadStatusLine,
                            http_client.NotConnected,
                            http_client.CannotSendRequest,
                            http_client.CannotSendHeader)
RETRY_URLLIB_EXCEPTIONS = (error.HTTPError, )
RETRY_REQUESTS_EXCEPTIONS = (requests.ConnectionError, requests.Timeout)
RETRY_HTTP_CODES = (http_client.REQUEST_TIMEOUT,
                    http_client.INTERNAL_SERVER_ERROR,
                    http_client.BAD_GATEWAY,
                    http_client.SERVICE_UNAVAILABLE,
                    http_client.GATEWAY_TIMEOUT,)


def is_retriable_requests_httperror(error):
    """Returns true error is retriable requests.exceptions.HTTPError."""
    return (isinstance(error, requests.exceptions.HTTPError) and
            error.response.status_code in RETRY_HTTP_CODES)


def is_network_failure(error):
    """Returns True when error is a network failure."""
    return ((isinstance(error, RETRY_URLLIB_EXCEPTIONS)
             and error.code in RETRY_HTTP_CODES) or
            isinstance(error, RETRY_HTTPLIB_EXCEPTIONS) or
            isinstance(error, RETRY_SOCKET_EXCEPTIONS) or
            isinstance(error, RETRY_REQUESTS_EXCEPTIONS) or
            is_retriable_requests_httperror(error))


def retry(attempts_number=None,
          delay=None,
          step=0,
          retry_on=None,
          retry_except=None,
          logger=None):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            if attempts_number is not None:
                retry_attempts = attempts_number
            else:
                retry_attempts = defaults.HTTP_RETRY_ATTEMPTS

            if delay is not None:
                retry_delay = delay
            else:
                retry_delay = defaults.HTTP_RETRY_DELAY

            if retry_on is None:
                retry_func = is_network_failure
            else:
                retry_func = retry_on

            failover_func = decorators.retry(retry_attempts,
                                             retry_delay,
                                             step,
                                             retry_func,
                                             retry_except,
                                             logger)(func)
            return failover_func(*args, **kwargs)

        return wrapper

    return decorator
