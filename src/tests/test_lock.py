'''
Created on Sep 24, 2014

@author: ivan
'''
import unittest
from xapi_back.util import RuntimeLock, AlreadyLocked




class Test(unittest.TestCase):


    def test_lock(self):
        with RuntimeLock('tt1'):
            pass
        with RuntimeLock('tt1'):
            pass
        
    def test_lock_fail(self):
        with RuntimeLock('tt1'):
            l =RuntimeLock('tt1')
            try:
                l.lock()
                self.fail('should fail')
            except AlreadyLocked:
                pass
            
    def test_lock2(self):
        with RuntimeLock('tt1'):
            with RuntimeLock('tt2'):
                pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_lock']
    unittest.main()