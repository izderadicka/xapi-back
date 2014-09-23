'''
Created on Sep 19, 2014

@author: ivan
'''

from xapi_back.cli import Command, register, XAPISession
from tabulate import tabulate

class HostsCommand(Command):
    name="hosts"
    description="Lists all available hosts from config file"
    def execute(self):
        def test_server(s):
            try:
                with XAPISession(s['url'], s['user'], s['password']):
                    return True
            except:
                return False
        servers=map(lambda s: (s['name'], s['url'], str(test_server(s))), self.config['servers'])
        print tabulate(servers, ['Name', 'URL', 'Can Connect'])
        
def register_me(commands):
    register(commands, HostsCommand)