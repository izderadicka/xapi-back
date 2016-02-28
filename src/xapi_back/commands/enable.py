'''
Created on Sep 20, 2014

@author: ivan
'''

from xapi_back.cli import CommandForOneVM, register
from xapi_back.util import bool2str
from xapi_back.common import AUTOBACKUP_KEY, AUTOBACKUP_BATCH


class EnableCommand(CommandForOneVM): 
    name="enable"
    description="Enable VM periodic backup"
    def execute_for_one(self, session, host):
        id=self.find_vm(session, host)  # @ReservedAssignment
        session.xenapi.VM.remove_from_other_config(id, AUTOBACKUP_KEY)
        session.xenapi.VM.add_to_other_config(id, AUTOBACKUP_KEY, bool2str(True))
        if self.args.batch:
            session.xenapi.VM.remove_from_other_config(id, AUTOBACKUP_BATCH)
            session.xenapi.VM.add_to_other_config(id, AUTOBACKUP_BATCH, self.args.batch)
        else:
            session.xenapi.VM.remove_from_other_config(id, AUTOBACKUP_BATCH)
    
    @classmethod
    def add_params(self, parser):
        super(EnableCommand, self).add_params(parser)
        parser.add_argument('--batch', help="periodic backup batch - can be run under this name with backup-batch command",)
        
    
    
def register_me(commands):
    register(commands, EnableCommand)