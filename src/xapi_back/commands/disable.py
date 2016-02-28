'''
Created on Sep 20, 2014

@author: ivan
'''

from xapi_back.cli import CommandForOneVM, register
from xapi_back.common import AUTOBACKUP_KEY, AUTOBACKUP_BATCH


class DisableCommand(CommandForOneVM): 
    name="disable"
    description="Disable VM periodic backup"
    def execute_for_one(self, session, host):
        
        id=self.find_vm(session, host)  #@ReservedAssignment
        session.xenapi.VM.remove_from_other_config(id, AUTOBACKUP_KEY)
        session.xenapi.VM.remove_from_other_config(id, AUTOBACKUP_BATCH)
    
    
def register_me(commands):
    register(commands, DisableCommand)