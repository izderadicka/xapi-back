'''
Created on Sep 21, 2014

@author: ivan
'''
import httplib
import urlparse
import urllib
import os

class HTTPError(Exception):
    def __init__(self, status, reason, reply=None):
        self.status=status
        self.reason=reason
        self.reply=reply
        super(HTTPError, self).__init__('%d %s'% (status, reason))
        
    def __str__(self):
        return "%d %s\n%s" % (self.status, self.reason, self.reply)


class Client(object):
    def __init__(self, base_url):
        prot,host, _, _, _ =urlparse.urlsplit(base_url)
        if prot=='http':
            self._conn=httplib.HTTPConnection(host, timeout=10)
        elif prot == 'https':
            self._conn=httplib.HTTPSConnection(host, timeout=10)
            
    def _handle_resp(self, resp):
        if resp.status<>200:
            raise HTTPError(resp.status, resp.reason, resp.read())
        return resp
    
    def _prepare_url(self, path, params):
        if params:
            path=path+'?'+urllib.urlencode(params)
        return path
            
    def get(self, path, params=None):
        path=self._prepare_url(path, params)
        self._conn.request('GET', path)
        resp=self._conn.getresponse()
        
        return self._handle_resp(resp)
    
    def put(self, path, body, length, params=None):
        path=self._prepare_url(path, params)
        self._conn.request('PUT',path, body, headers={'Content-length': str(length),
                                                      'Content-type':'application/octect-stream'})
        resp=self._conn.getresponse()
        return self._handle_resp(resp)
    
    def close(self):
        self._conn.close()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
            
        
        