'''
Created on Sep 23, 2014

@author: ivan
'''


from xapi_back.cli import CommandForEachHost, register, log
from xapi_back.common import AUTOBACKUP_KEY, AUTOBACKUP_BATCH, BACKUP_LOCK
from backup_one import BackupOne
from xapi_back.storage import Storage
from xapi_back.util import RuntimeLock

class BackupBatchCommand(CommandForEachHost, BackupOne):
    name="backup-batch"
    description="Backup batch of VMs (can be specified by batch param)"
    
    def before(self):
        log.info('Starting backup bacth %s', self.args.batch)
        
    def execute_for_each(self, session, host):
        all_vms = session.xenapi.VM.get_all_records()
        prog=not self.args.no_progress
        
        storage=Storage(self.config['storage_root'], self.config.get('storage_retain', 3))
        batch=self.args.batch
        with RuntimeLock(BACKUP_LOCK, 'Another backup is running!'):
            for vm_id in all_vms:
                vm = all_vms[vm_id]
                if not vm['is_control_domain'] and  \
                vm['other_config'].get(AUTOBACKUP_KEY) and \
                (not batch or batch == vm['other_config'].get(AUTOBACKUP_BATCH)):
                    vm_name=vm['name_label']
                    if prog:
                        print "Host %s - VM %s" % (host['name'], vm_name)
                    try:
                        self.backup(session, vm_id, vm_name, host, storage, self.args.shutdown, show_progress=prog)
                    except Exception, e:
                        log.error('Error while backing up VM %s on host %s', vm_name, host['name'])
                    
                    
                          
    def after(self):
        log.info('Finished backup bacth %s', self.args.batch)
        
        
    @classmethod
    def add_params(self, parser):
        super(BackupBatchCommand, self).add_params(parser)
        parser.add_argument('--batch', help="selects only backups that are indicated for this batch")
        parser.add_argument('--shutdown', action='store_true', help="Shutdown running VM before backup and start afterward")
        parser.add_argument('--no-progress', action='store_true', help="Do not print progress")
                
def register_me(commands):
    register(commands, BackupBatchCommand)                
    