'''
Created on Sep 20, 2014

@author: ivan
'''
import unittest
import tempfile
import os
from xapi_back.storage import Storage
import shutil
import time
import uuid

TEST_FILE= '/usr/bin/python'

def gen_uuid():
    return str(uuid.uuid4())

def write_test_file( s):
            w = s.get_writer()
            with open(TEST_FILE,'rb') as f:
                while True:
                    read= f.read(10000)
                    if not read:
                        break
                    w.write(read)
            s.close()

class Test(unittest.TestCase):


    def setUp(self):
        self.dir=tempfile.mkdtemp()
    
    def test_uuid(self):
        sr=Storage(self.dir, 2,compression_level= 0)
        uid=gen_uuid()
        rack=sr.get_rack_for('test',uid )
        slot=rack.create_slot()
        write_test_file(slot)
        slot.close()
        uid2=gen_uuid()
        rack=sr.get_rack_for('test',uid2 )
        self.assertEqual(rack.last_slot, None)
        self.assertTrue(os.path.exists(rack._path))
        uid3=gen_uuid()
        rack=sr.get_rack_for('test',uid3,exists=True)
        self.assertFalse(rack)
        
        try:
            r=sr.find_rack_for('test')
            self.fail('Should raise exception')
        except Storage.NotFound:
            pass
        
        try:
            r=sr.find_rack_for('test', '123')
            self.fail('Should raise exception')
        except Storage.NotFound:
            pass
        
        r=sr.find_rack_for('test', uid)
        self.assertTrue(r)
        s=r.last_slot
        self.assertTrue(s)
        
        r=sr.find_rack_for('test', uid[:5].upper())
        self.assertTrue(r)
        s=r.last_slot
        self.assertTrue(s)
        
        
        
    def test_compress(self):
        test_file_size=os.stat(TEST_FILE).st_size
        sr=Storage(self.dir, 2,compression_level= 0)
        uid=gen_uuid()
        rack=sr.get_rack_for('test',uid )
        slot=rack.create_slot()
        write_test_file(slot)
        res= rack.last_slot
        self.assertEqual(res._comp_method, 'client')
        self.assertEqual(test_file_size, res.size_uncompressed)
        self.assertTrue(test_file_size < res.size)
        
        sr=Storage(self.dir, 2,compression_level= 1)
        rack=sr.get_rack_for('test', uid)
        slot=rack.create_slot()
        write_test_file(slot)
        res= rack.last_slot
        self.assertEqual(test_file_size, res.size_uncompressed)
        self.assertTrue(test_file_size > res.size)
        comp_size = res.size
        
        sr=Storage(self.dir, 2,compression_level= 9)
        rack=sr.get_rack_for('test', uid)
        slot=rack.create_slot()
        write_test_file(slot)
        res= rack.last_slot
        self.assertEqual(test_file_size, res.size_uncompressed)
        self.assertTrue(comp_size > res.size)
        
    def test_no_compress(self):
        test_file_size=os.stat(TEST_FILE).st_size
        sr=Storage(self.dir, 2,compression_method= None)
        uid=gen_uuid()
        rack=sr.get_rack_for('test', uid)
        slot=rack.create_slot()
        write_test_file(slot)
        res= rack.last_slot
        self.assertEqual(res._comp_method, None)
        self.assertEqual(test_file_size, res.size_uncompressed)
        self.assertEqual(test_file_size , res.size)
        
        self.assertTrue(slot._path.endswith('.xva'))
        self.assertTrue(res._path.endswith('.xva'))
        self.assertTrue(res.duration)
        print 'duration',res.duration
        self.assertTrue(res.created)
        print 'created', res.created
        
        st=sr.get_status()
        self.assertTrue(st[uid])
        
    def test_no_compress_server(self):
        test_file_size=os.stat(TEST_FILE).st_size                
        sr=Storage(self.dir, 2,compression_method= 'server')
        uid=gen_uuid()
        rack=sr.get_rack_for('test',uid)
        slot=rack.create_slot()
        write_test_file(slot)
        res= rack.last_slot
        self.assertEqual(res._comp_method, 'server')
        self.assertEqual(test_file_size, res.size_uncompressed)
        self.assertEqual(test_file_size , res.size)
        
        self.assertTrue(slot._path.endswith('.xva.gz'))
        self.assertTrue(res._path.endswith('.xva.gz'))
        
    def test_basic(self):
        sr=Storage(self.dir, 2)
        uid=gen_uuid()
        rack=sr.get_rack_for('test', uid)
        slot=rack.create_slot()
        msg='Hi There Is Anybody In There'
        slot.get_writer().write(msg)
        time.sleep(0.001)
        slot.close()
        self.assertEqual(1, len(rack.get_all_slots()))
        m=rack.last_slot
        self.assertEqual(len(msg), m.size_uncompressed)
        self.assertTrue(m.duration>0)
        m.close()
        time.sleep(0.01)
        slot=rack.create_slot()
        slot.get_writer().write('Second')
        slot.close()
        self.assertEqual(2, len(rack.get_all_slots()))
        slot=rack.last_slot
        r=slot.get_reader().read()
        slot.close()
        self.assertEqual('Second',r)
        
        slot=rack.create_slot()
        w=slot.get_writer()
        w.write('aaa')
        w.close()
        self.assertEqual(2, len(rack.get_all_slots()))
        
        time.sleep(0.01)
        slot=rack.create_slot()
        slot.get_writer().write('Third')
        slot.close()
        self.assertEqual(3, len(rack.get_all_slots()))
        slot=rack.last_slot
        r=slot.get_reader().read()
        slot.close()
        self.assertEqual('Third',r)
        
        rack.shrink()
        self.assertEqual(2, len(rack.get_all_slots()))
        
        r=slot.get_reader().read()
        slot.close()
        self.assertEqual('Third',r)

    def tearDown(self):
       shutil.rmtree(self.dir)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()