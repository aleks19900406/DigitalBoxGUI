import unittest

class Test01LinkLayer(unittest.TestCase):
    def test_01_llid1(self):
        # Arrange
        # (Setup your test data here)
        actual_result =10
        # Act
        # (Call the method or function you want to test here)
        expected_result = 10
        # Assert
        # (Check that the actual result matches the expected result)
        self.assertEqual(actual_result, expected_result, "The test failed")

if __name__ == '__main__':
    unittest.main()
