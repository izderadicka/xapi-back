#!/usr/bin/env python
import sys
import os.path
rd=os.path.join(os.path.split(__file__)[0], '..')
sys.path.append(rd)

from xapi_back.storage import Storage
import argparse
import time

import shutil


TEST_RACK="test"

def write_file(dir_name,f, compression_level=0, block_size=10000):
    def w(s):
        w = s.get_writer()
        while True:
            read= f.read(block_size)
            if not read:
                break
            w.write(read)
        slot.close()
    sr=Storage(dir_name, 2,compression_level= compression_level)
    rack=sr.get_rack_for(TEST_RACK, '1234')
    slot=rack.create_slot()
    w(slot)
    
    
def main():
    p=argparse.ArgumentParser()
    p.add_argument('test_file', type=file, help='Test file')
    p.add_argument('-c', '--compression', type=int, default=0, help='Compression level')
    p.add_argument('-b', '--block-size', type=int, default=10000, help='Compression level')
    opts=p.parse_args()
    f=opts.test_file
    size=os.stat(f.name).st_size
    d=os.path.split(f.name)[0]
    start=time.time()
    write_file(d,f, compression_level=opts.compression, block_size=opts.block_size)
    dur= time.time()-start
    print 'Duration: %f sec'%dur
    print 'Speed %f MB/s' % ((size / (1024.0 *1024)) / dur)
    f.close()
    shutil.rmtree(os.path.join(d, TEST_RACK), ignore_errors=True)
    
    
if __name__ == '__main__':
    main()