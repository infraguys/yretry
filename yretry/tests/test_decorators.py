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

import mock

from yretry import decorators
from yretry.tests import base


RETRY_ATTEMPTS = 3

START_DELAY = 0

STEP = 1


class SuperPuperException(Exception):
    pass


class DontRetryException(Exception):
    pass


class FakeClass(mock.Mock):

    @decorators.retry(RETRY_ATTEMPTS, delay=0)
    def retry_method_works_incorrect(self):
        self.retry_count()
        raise SuperPuperException()

    @decorators.retry(RETRY_ATTEMPTS, delay=0,
                      retry_on=(SuperPuperException,))
    def retry_method_works_incorrect_2(self):
        self.retry_count()
        raise DontRetryException()

    @decorators.retry(RETRY_ATTEMPTS, delay=0)
    def retry_method_works_correct(self):
        self.retry_count()

    @decorators.retry(RETRY_ATTEMPTS, delay=START_DELAY,
                      step=STEP)
    def retry_with_custom_step(self):
        self.retry_count()
        raise SuperPuperException()

    @decorators.retry(RETRY_ATTEMPTS, delay=0,
                      retry_except=(SuperPuperException,))
    def retry_on_except(self):
        self.retry_count()
        raise SuperPuperException()


class RetryTestCase(base.TestCase):

    def setUp(self):
        self._target = FakeClass()

    def test_must_retry_three_time_and_raise_exception(self):
        self.assertRaises(
            SuperPuperException,
            self._target.retry_method_works_incorrect)
        self.assertEqual(self._target.retry_count.call_count,
                         RETRY_ATTEMPTS)

    def test_must_retry_one_time_and_return_correct_result(self):
        self.assertIsNone(self._target.retry_method_works_correct())
        self.assertEqual(self._target.retry_count.call_count, 1)

    def test_dont_retry_on_unexpected_error(self):
        """Don't retry if exception isn't SuperPuperException."""
        self.assertRaises(
            DontRetryException,
            self._target.retry_method_works_incorrect_2)
        self.assertEqual(self._target.retry_count.call_count, 1)

    @mock.patch('time.sleep')
    def test_step_is_works(self, sleep):
        """retry delay increases to step value."""
        self.assertRaises(
            SuperPuperException,
            self._target.retry_with_custom_step)
        sleep.assert_has_calls([
            mock.call(START_DELAY),
            mock.call(START_DELAY + STEP)
        ])

    def test_retry_works_with_function_without_parameters(self):
        @decorators.retry(RETRY_ATTEMPTS, delay=0)
        def function_without_parameters():
            return "OK"

        self.assertEqual(function_without_parameters(), "OK")

    def test_dont_retry_on_expected_error(self):
        """Don't retry if exception is SuperPuperException."""
        self.assertRaises(
            SuperPuperException,
            self._target.retry_on_except,
            )
        self.assertEqual(self._target.retry_count.call_count, 1)


class LoggerTestCase(base.TestCase):

    def setUp(self):
        super(LoggerTestCase, self).setUp()

        self.logger = mock.MagicMock()

    @mock.patch('time.sleep')
    def test_works_without_logger(self, sleep):
        class Counter(object):

            def __init__(self):
                self._value = 0

            @property
            def value(self):
                return self._value

            def inc(self):
                self._value += 1

        @decorators.retry(RETRY_ATTEMPTS,
                          retry_on=(SuperPuperException,))
        def bad_function(counter):
            counter.inc()
            raise SuperPuperException()

        counter = Counter()

        self.assertRaises(SuperPuperException,
                          bad_function,
                          counter)

        self.assertEqual(counter.value, 3)

    @mock.patch('time.sleep')
    def test_predefined_logger_is_used(self, sleep):
        """decorators.retry uses logger to write debug information

        Decorator writes warning messages about retries.
        """
        @decorators.retry(RETRY_ATTEMPTS,
                          logger=self.logger,
                          retry_on=(SuperPuperException,))
        def bad_function():
            raise SuperPuperException()

        self.assertRaises(SuperPuperException,
                          bad_function)

        self.assertEqual(self.logger.warning.call_count,
                         RETRY_ATTEMPTS - 1)

    @mock.patch('time.sleep')
    def test_object_logger_is_used(self, sleep):
        """decorators.retry uses object's logger

        """

        class TestClass(object):

            def __init__(self):
                self.logger = mock.MagicMock()

            def get_logger(self):
                return self.logger

            @decorators.retry(RETRY_ATTEMPTS,
                              retry_on=(SuperPuperException,))
            def reliable_method(self):
                raise SuperPuperException()

        obj = TestClass()

        self.assertRaises(SuperPuperException,
                          obj.reliable_method)

        self.assertEqual(obj.logger.warning.call_count,
                         RETRY_ATTEMPTS - 1)

    @mock.patch('time.sleep')
    def test_object_logger_is_used_predefined_is_ignored(self, sleep):
        """decorators.retry ignores predefined logger

        In case when object logger is defined.
        """

        class TestClass(object):

            def __init__(self):
                self.logger = mock.MagicMock()

            def get_logger(self):
                return self.logger

            @decorators.retry(RETRY_ATTEMPTS,
                              logger=self.logger,
                              retry_on=(SuperPuperException,))
            def reliable_method(self):
                raise SuperPuperException()

        obj = TestClass()

        self.assertRaises(SuperPuperException,
                          obj.reliable_method)

        self.assertEqual(self.logger.warning.call_count,
                         0)

        self.assertEqual(obj.logger.warning.call_count,
                         RETRY_ATTEMPTS - 1)

    @mock.patch('time.sleep')
    def test_works_if_get_logger_isnt_defined(self, sleep):
        """decorators works if get_logger isn't defined."""

        class TestClass(object):

            def __init__(self):
                pass

            @decorators.retry(RETRY_ATTEMPTS,
                              retry_on=(SuperPuperException,))
            def reliable_method(self):
                raise SuperPuperException()

        obj = TestClass()

        self.assertRaises(SuperPuperException,
                          obj.reliable_method)
