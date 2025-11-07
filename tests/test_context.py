import unittest

from tasktronaut.context import Context


class ContextTestCase(unittest.TestCase):
    def test(self):
        result = Context()
        self.assertIsNotNone(result)
