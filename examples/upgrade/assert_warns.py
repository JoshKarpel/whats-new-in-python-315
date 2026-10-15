import io
import unittest
import warnings


class Test(unittest.TestCase):
    def test_deprecated(self):
        with self.assertWarns(DeprecationWarning):
            warnings.warn("unrelated", UserWarning)
            warnings.warn("expected", DeprecationWarning)


with warnings.catch_warnings(record=True) as leaked:
    warnings.simplefilter("always", UserWarning)
    tests = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(stream=io.StringIO()).run(tests)
print("leaked:", [str(warning.message) for warning in leaked])
