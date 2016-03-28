'''
Created on Jan 15, 2016

@author: ivan
'''
import unittest
from xapi_back.util import format_size, unsecure

class Test(unittest.TestCase):


    def test_fmt(self):
        self.assertEqual(format_size(500), '500')
        self.assertEqual(format_size(1023), '1023')
        self.assertEqual(format_size(1024), '1.0k')
        self.assertEqual(format_size(1023*1024), '1023.0k')
        self.assertEqual(format_size(1024*1024*10.51), '10.5M')
        self.assertEqual(format_size(1024*1024*1024*33), '33.0G')
        self.assertEqual(format_size(1024*1024*1024*1024*5), '5.0T')
        self.assertEqual(format_size(1024*1024*1024*1024*5000), '5000.0T')
        
    def test_assure_http(self):
        url='https://developer.mozilla.org/en-US/docs'
        url2='http://developer.mozilla.org/en-US/docs'
        self.assertEqual(unsecure(url), url2)
        self.assertEqual(unsecure(url2), url2)
        self.assertEqual(unsecure(url, None), url)
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()