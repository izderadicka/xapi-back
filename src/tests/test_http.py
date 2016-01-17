'''
Created on Sep 21, 2014

@author: ivan
'''
import unittest
from xapi_back.http import Client, HTTPError, RedirectError
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
            
    def test_https(self):
        with Client('https://httpbin.org/') as c:
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
        
    def test_redirect(self):
        with Client('http://httpbin.org/') as c:
            resp=c.get('/relative-redirect/1', {'uuid':'aaaa'})
            data=json.load(resp)
            self.assertTrue(data)
            
        with Client('http://httpbin.org/') as c:
            resp=c.get('/absolute-redirect/1', {'uuid':'aaaa'})
            data=json.load(resp)
            self.assertTrue(data)
        
        with Client('http://httpbin.org/') as c:
            try:
                resp=c.get('/relative-redirect/4', {'uuid':'aaaa'})
                self.fail('Should raise http error')
            except RedirectError:
                pass
            
            
            
        

        
    
    
       


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_get']
    unittest.main()