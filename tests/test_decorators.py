import unittest

from tasktronaut.decorators import task


class DecoratorTestCase(unittest.TestCase):
    def test_naked(self):
        @task
        def f():
            pass

        self.assertIsNotNone(f)
        self.assertIsNone(f.description)

    def test_parenthesis(self):
        @task()
        def f():
            pass

        self.assertIsNotNone(f)
        self.assertIsNone(f.description)

    def test_description(self):
        @task(description="test")
        def f():
            pass

        self.assertIsNotNone(f)
        self.assertEqual("test", f.description)
