'''
Created on Sep 20, 2014

@author: ivan
'''
import unittest
import os.path
from xapi_back.cli import load_commands, read_config, prepare_env

CFG = os.path.join(os.path.split(__file__)[0], '../../xapi-back.cfg')

class Test(unittest.TestCase):


    def test_loading_commands(self):
        cc=load_commands()
        self.assertTrue(len(cc)>0)
        
    def test_cfg_file(self):
        cfg=read_config(CFG)
        self.assertTrue(len(cfg['servers'])>0)
        self.assertTrue(cfg['servers'][0]['name'])
        
    def test_cli(self):
        cmd=prepare_env(['-c', CFG, 'hosts'])
        self.assertEqual('hosts', cmd.name)
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_loading_commands']
    unittest.main()