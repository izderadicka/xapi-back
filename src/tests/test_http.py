'''
Created on Sep 21, 2014

@author: ivan
'''
import unittest
from xapi_back.http import Client, HTTPError
import json
import pprint
from StringIO import StringIO
import requests

class Test(unittest.TestCase):


    def test_get(self):
        with Client('http://httpbin.org/') as c:
            resp=c.get('/get', {'uuid':'aaaa'})
            data=json.load(resp)
            pprint.pprint(data)
            
    def test_error(self):
        with Client('http://httpbin.org/') as c:
            try:
                resp=c.get('/status/404')
                self.fail('Should rise msg')
            except HTTPError,e:
                self.assertEqual(404, e.status)
                
    def test_put(self):
        msg='Sedm lumpu slohlo pumpu pobliz zumpu v zupe kumpu'
        body=StringIO(msg)
        with Client('http://httpbin.org/') as c:
            resp=c.put('/put', body, len(msg), {'uuid':'aaaa'})
            data=json.load(resp)
        pprint.pprint(data)
        print "Response Header:",resp.getheaders()

        
    
    
       


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_get']
    unittest.main()