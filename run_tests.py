import unittest

loader = unittest.TestLoader()
tests = loader.discover('tests')
testRunner = unittest.TextTestRunner()
testRunner.run(tests)

