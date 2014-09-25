'''
Created on Sep 20, 2014

@author: ivan
'''
import time
from math import floor
import random
import hashlib
import struct
import sys
from os.path import os
import errno


def bool2str(b):
    if b:
        return 'true'
    return 'false'

def str2bool(s):
    if s=='true':
        return True
    else:
        return False
    
def rand_hash():
    now=time.time()
    frac=int(round((now-floor(now)) *1e9))
    r=random.randint(0,sys.maxint)
    h=hashlib.sha1()
    h.update(struct.pack('I', frac))
    h.update(struct.pack('L', r))
    return h.hexdigest()

#
def gzip_size(filename):
    """return UNCOMPRESSED filesize of a gzipped file.
       But works only for sizes under 4GB - for bigger it's reminder and dividing size by 4GB
    """
    fo = open(filename, 'rb')
    fo.seek(-4, 2)
    r = fo.read()
    fo.close()
    return struct.unpack('<I', r)[0]

class AlreadyLocked(Exception):
    def __init__(self, msg):
        super(AlreadyLocked, self).__init__(msg)
    pass
class RuntimeLock(object):
    def __init__(self, name, fail_msg='Runtime lock exists, cannot continue'):
        locs=['/run/lock/', '/var/run/lock', '/var/run', '/tmp']
        loc = None
        for l in locs:
            if os.path.isdir(l) and os.access(l, os.R_OK|os.W_OK):
                loc=l
                break
        if not loc:
            raise Exception('No directory for lock file')
        self._lock_file= os.path.join(loc, name)
        self._fp = None
        self._fail_msg=fail_msg
        
        
    def lock(self):
        try:
            self._fp=os.open(self._lock_file, os.O_CREAT|os.O_EXCL|os.O_RDWR)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise AlreadyLocked(self._fail_msg)
            
    def unlock(self):
        os.close(self._fp)
        os.unlink(self._lock_file)
        
        
    def __enter__(self):
        self.lock()
        return self
    
    def __exit__(self, ex_type, ex_value, frm):
        self.unlock()