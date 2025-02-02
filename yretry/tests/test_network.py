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

import socket

import mock
from six.moves import http_client
from six.moves.urllib import error

from yretry import network
from yretry.tests import base


RETRY_ATTEMPTS = 3


class FakeClass(mock.Mock):

    @network.retry(RETRY_ATTEMPTS, delay=0)
    def retry_method_works_incorrect(self):
        self.retry_count()
        raise socket.timeout()

    @network.retry(RETRY_ATTEMPTS, delay=0)
    def retry_method_works_incorrect_http_exception(self):
        self.retry_count()
        raise error.HTTPError(
            "FakeUrl", http_client.REQUEST_TIMEOUT,
            "FakeMessage", None, None)

    @network.retry(RETRY_ATTEMPTS, delay=0)
    def retry_method_works_correct(self):
        self.retry_count()


class RetryTestCase(base.TestCase):

    def setUp(self):
        self._target = FakeClass()

    def test_must_retry_three_time_and_raise_exception(self):
        self.assertRaises(
            socket.timeout,
            self._target.retry_method_works_incorrect)
        self.assertEqual(self._target.retry_count.call_count, 3)

    def test_must_retry_three_time_and_raise_http_exception(self):
        self.assertRaises(
            error.HTTPError,
            self._target.retry_method_works_incorrect_http_exception)
        self.assertEqual(self._target.retry_count.call_count, 3)

    def test_must_retry_one_time_and_return_correct_result(self):
        self.assertIsNone(self._target.retry_method_works_correct())
        self.assertEqual(self._target.retry_count.call_count, 1)
