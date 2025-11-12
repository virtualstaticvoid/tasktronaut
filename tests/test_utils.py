import unittest

import tasktronaut
from tasktronaut.utils import load_definition, to_dict, to_kwargs
from .examples import SimpleSequential


class UtilsTestCase(unittest.TestCase):
    def test_version(self):
        self.assertNotEqual("0.0.0.dev", tasktronaut.__version__)

    def test_to_dict(self):
        result = to_dict(foo=1)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(1, result["foo"])

    def test_to_kwargs(self):
        result = to_kwargs(to_dict(foo=1), bar=2)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(1, result["foo"])
        self.assertEqual(2, result["bar"])

    def test_load_definition(self):
        result = load_definition(
            module_name=SimpleSequential.__module__,
            definition_class=SimpleSequential.__qualname__,
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, SimpleSequential)
