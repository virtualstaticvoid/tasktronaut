import unittest

from tasktronaut.steps import Step, Steps


class StepTestCase(unittest.TestCase):
    def setUp(self):
        def _mock_func(*_, **__): ...

        self.step = Step(
            func=_mock_func,
            description="mock",
            kwargs={
                "foo": "bar",
            },
        )

    def test_is_process(self):
        self.assertFalse(self.step.is_process)

    def test_str(self):
        result = str(self.step)
        self.assertIsNotNone(result)
        self.assertTrue("foo" in result)

    def test_repr(self):
        result = repr(self.step)
        self.assertIsNotNone(result)
        self.assertTrue("foo" in result)


class StepsTestCase(unittest.TestCase):
    def test(self):
        steps = Steps()
        self.assertIsInstance(steps, list)
