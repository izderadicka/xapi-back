'''
Created on Sep 23, 2014

@author: ivan
'''

from xapi_back.cli import CommandForOneHost, register
from tabulate import tabulate
from xapi_back.util import format_size

class ListSrsCommand(CommandForOneHost):
    name="srs"
    description="List Storage Repositories on host, which can be used for VM restore"
    
    def execute_for_one(self, session, host):
        all_srs= session.xenapi.SR.get_all_records()
        tab=[]
        for sr_id in all_srs:
            row=[]
            
            sr=all_srs[sr_id]
            size=int(sr.get('physical_size','0'))
            if size>0 and 'vdi_create' in  session.xenapi.SR.get_allowed_operations(sr_id):
                row.append(sr['uuid'])
                row.append(sr.get('name_label', ''))
                row.append('Yes' if sr.get('shared', '') else 'No')
                row.append(sr.get('type', ''))
                used=int(sr.get('virtual_allocation', '0'))
                free=size-used
                row.append(format_size(free))
                
                tab.append(row)
            
        print tabulate(tab, ['UUID', 'Name', 'Shared', 'Type','Free' ])
            
            
                
                
        
    @classmethod
    def add_params(self, parser):
        super(ListSrsCommand, self).add_params(parser)
        
        
def register_me(commands):
    register(commands, ListSrsCommand)
        
        
