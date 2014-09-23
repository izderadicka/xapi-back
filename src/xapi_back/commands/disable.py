'''
Created on Sep 20, 2014

@author: ivan
'''

from xapi_back.cli import CommandForOneHost, register, CommandError, log
from xapi_back.common import AUTOBACKUP_KEY, AUTOBACKUP_FREQ_KEY


class DisableCommand(CommandForOneHost): 
    name="disable"
    description="Disable VM periodic backup"
    def execute_for_one(self, session, host):
        ids=session.xenapi.VM.get_by_name_label(self.args.vm)
        log.debug('Found this VMs %s', ids)
        if not ids:
            raise CommandError('VM %s not found on server %s' % (self.args.vm, host['name']))
        elif len(ids)>1:
            raise CommandError('Name %s is not unique, please fix'% self.args.vm)
        id=ids[0]  # @ReservedAssignment
        session.xenapi.VM.remove_from_other_config(id, AUTOBACKUP_KEY)
        session.xenapi.VM.remove_from_other_config(id, AUTOBACKUP_FREQ_KEY)
    
    @classmethod
    def add_params(self, parser):
        super(DisableCommand, self).add_params(parser)
        parser.add_argument('--vm', required=True, help="Name of VM")
    
    
def register_me(commands):
    register(commands, DisableCommand)