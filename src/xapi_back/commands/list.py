'''
Created on Sep 19, 2014

@author: ivan
'''
from xapi_back.cli import CommandForEachHost, register
from tabulate import tabulate
from xapi_back.util import bool2str, shorten_uuid
from xapi_back.common import AUTOBACKUP_KEY, AUTOBACKUP_BATCH
from collections import OrderedDict
from xapi_back.storage import Storage

class ListCommand(CommandForEachHost):
    name="list"
    description="List all VMs and their current backup status"
    
    def before(self):
        self.result=OrderedDict()  
              
    def execute_for_each(self, session, host):
        all_vms = session.xenapi.VM.get_all_records()
        for vm_id in all_vms:
            vm = all_vms[vm_id]
            if not vm['is_a_template'] and not vm['is_control_domain'] and not vm['is_a_snapshot']:
                vm_uuid=vm['uuid']
                vm_name=vm['name_label']
                self.result[vm_uuid]=[host['name'],vm_name, shorten_uuid(vm_uuid),
                    vm['power_state'],
                    bool2str(vm['other_config'].get(AUTOBACKUP_KEY, False)),
                    vm['other_config'].get(AUTOBACKUP_BATCH) ]
                
    def after(self):
        def fmt_date(dt):
            if not dt:
                return ''
            return dt.strftime('%Y-%m-%d %H:%M')
        def fmt_dur(d):
            if not d:
                return ''
            return '%0.1f' % (d / 60.0)
        s=Storage(self.config['storage_root'], compression_method=self.config.get('compress', 'client'))
        stats=s.get_status()
        tab=[]
        for vm in self.result:
            row=self.result[vm]
            stat=stats.get(vm)
            if stat:
                row.append(fmt_date(stat['last_backup']))
                row.append(fmt_dur(stat['duration']))
            else:
                row.extend(['', ''])
            tab.append(row)
        for vm in stats:
            if not self.result.has_key(vm):
                tab.append(['', stats[vm]['name'], shorten_uuid(vm), '', '', '', fmt_date(stats[vm]['last_backup']), fmt_dur(stats[vm]['duration'])])
        print tabulate(tab, ['Host', 'VM', 'UUID','State', 'AutoBck', 'AutoBck Batch', 'Last Backup', 'Dur. (m)'])
        
                
def register_me(commands):
    register(commands, ListCommand)