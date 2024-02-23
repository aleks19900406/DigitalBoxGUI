import HtmlTestRunner
import unittest


class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_error(self):
        """ This test should be marked as error one. """
        raise ValueError

    def test_fail(self):
        """ This test should fail. """
        self.assertEqual(1, 2)
    
    def test_list(self):
        with self.subTest(msg="compere two list"):
            self.assertListEqual([1,2,3],[1,2,3])

    def test_string(self):
        with self.subTest(msg="compere two string"):
            self.assertEqual(
                    'test1',
                    'test2',
                )
    
    @unittest.skip("This is a skipped test.")
    def test_skip(self):
        """ This test should be skipped. """
        pass


class MyTest(TestStringMethods):
    


if __name__ == '__main__':
    unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='REPORTS',report_title="Test_001",report_name = "firstTest",open_in_browser =True,combine_reports = True))