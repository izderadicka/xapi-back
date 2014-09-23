'''
Created on Sep 20, 2014

@author: ivan
'''
import unittest
from xapi_back.cli import load_commands, read_config, prepare_env

class Test(unittest.TestCase):


    def test_loading_commands(self):
        cc=load_commands()
        self.assertTrue(len(cc)>0)
        
    def test_cfg_file(self):
        cfg=read_config('../../xapi-back.cfg')
        self.assertTrue(len(cfg['servers'])>0)
        self.assertTrue(cfg['servers'][0]['name'])
        
    def test_cli(self):
        cmd=prepare_env(['-c', '../../xapi-back.cfg', 'hosts'])
        self.assertEqual('hosts', cmd.name)
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_loading_commands']
    unittest.main()