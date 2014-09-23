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

def extract_uuid(ref):
    try:
        return ref.split(':')[1]
    except IndexError:
        raise ValueError('Invalid ID: %s' % ref)