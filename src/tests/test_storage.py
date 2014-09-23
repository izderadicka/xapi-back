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


class Test(unittest.TestCase):


    def setUp(self):
        self.dir=tempfile.mkdtemp()
        
    def test_basic(self):
        sr=Storage(self.dir, 2)
        rack=sr.get_rack_for('test')
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