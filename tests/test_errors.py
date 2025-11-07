import unittest

from tasktronaut.errors import CancelProcessError, NonRetryableProcessError


class CancelProcessErrorTestCase(unittest.TestCase):
    def test(self):
        result = CancelProcessError()
        self.assertIsNotNone(result)


class NonRetryableProcessErrorTestCase(unittest.TestCase):
    def test(self):
        result = NonRetryableProcessError()
        self.assertIsNotNone(result)
