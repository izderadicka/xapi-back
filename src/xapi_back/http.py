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
    
    
class RedirectError(HTTPError):
    def __str__(self):
        return "Too many redirects - last redirect %d %s" % (self.status, self.reason)
    


class Client(object):
    def __init__(self, base_url):
        self._connect(base_url)
            
    def _connect(self, base_url):
        self._base_url = base_url
        prot,host, _, _, _ =urlparse.urlsplit(base_url)
        if prot=='http':
            self._conn=httplib.HTTPConnection(host, timeout=10)
        elif prot == 'https':
            self._conn=httplib.HTTPSConnection(host, timeout=10)
            
    def _reconnect(self, base_url):
        self._conn.close()
        self._connect(base_url)
            
    def _handle_resp(self, resp):
        if resp.status >=200 and resp.status< 300:
            return resp
        else:
            raise HTTPError(resp.status, resp.reason, resp.read())
    
    def _redirect(self, path, resp, redirects=0):
        if redirects>2:
            raise RedirectError(resp.status, resp.reason)
        if resp.status in (301,302,303): # 307, 308 not considered it needs additional approval form user as per HTTP RFC :
            new_url=resp.getheader('Location')
            if not new_url:
                raise HTTPError('Redirect must contain Location header')
            new_base, new_path=self._abs_url(path, new_url)
            self._reconnect(new_base)
            resp = self.get(new_path, redirects=redirects+1)
        return self._handle_resp(resp)
    
    def _abs_url(self,path, new_url):
        url=urlparse.urlsplit(new_url)
        if url.scheme:
            # we have absolute url
            return urlparse.urlunsplit((url.scheme, url.netloc, '', '', '')), urlparse.urlunsplit(('','',url.path, url.query, url.fragment))
        else:
            # we have relative url
            return self._base_url, urlparse.urljoin(path, new_url)
  
    
    def _prepare_url(self, path, params):
        if params:
            path=path+'?'+urllib.urlencode(params)
        return path
            
    def get(self, path, params=None, redirects=0):
        path=self._prepare_url(path, params)
        self._conn.request('GET', path)
        resp=self._conn.getresponse()
        return self._redirect(path, resp, redirects)
    
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
            
        
        