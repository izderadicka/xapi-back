'''
Created on Sep 21, 2014

@author: ivan
'''

from xapi_back.cli import CommandForOneVM, register, log, CommandError, ProgressMonitor
from xapi_back.http import Client
from xapi_back.storage import Storage
from xapi_back.common import uninstall_VM, cancel_task, BACKUP_LOCK
from xapi_back.util import RuntimeLock, unsecure
from xapi_back import XenAPI
import traceback
import sys

SNAPSHOT_PREFIX='Temp.backup of '
class BackupOne(object):
    
    def backup(self, session, vm_id, vm_name, host, storage, force_shutdown=False, show_progress=False,
               compress_on_server=False, insecure=False):
        uuid=session.xenapi.VM.get_uuid(vm_id)  # @ReservedAssignment
        vm_uuid=uuid
        state = session.xenapi.VM.get_power_state(vm_id)
        restore_actions=[]
        try:
            
            if state =='Paused':
                log.error('Cannot backup VM is state Paused')
                return
            elif state =='Suspended':
                log.warn('Backing up machine in suspended stated')
            elif state =='Running':
                if not force_shutdown:
                    try:
                        tt_id=session.xenapi.VM.snapshot(vm_id,SNAPSHOT_PREFIX+ vm_name )
                    except XenAPI.Failure, f:
                        if f.details[0]== 'SR_OPERATION_NOT_SUPPORTED':
                            raise CommandError('Cannot create snapshot of vm %s (try backup in halted state, or detach disks, that do not support snapshots)'% vm_name)
                        else:
                            raise
                    uuid=session.xenapi.VM.get_uuid(tt_id)
                    restore_actions.append(lambda: uninstall_VM(session, tt_id))
                    log.debug('Made snapshot of %s(%s) to snapshot uuid: %s', vm_name, vm_uuid, uuid)
                else:
                    log.debug('Shutting down VM')
                    session.xenapi.VM.clean_shutdown(vm_id)
                    def restart_vm():
                        session.xenapi.VM.start(vm_id, False, False)
                        log.debug('Started VM')
                    restore_actions.append(restart_vm)
        
            sid=session._session
            rack=storage.get_rack_for(vm_name, vm_uuid)
            log.info('Starting backup for VM %s (uuid=%s) on server %s', vm_name, vm_uuid, host['name'])
            progress=None
            with Client(unsecure(host['url'],insecure)) as c:
                params={'session_id':sid, 'uuid': uuid}
                if compress_on_server:
                    params['use_compression']="true"
                resp=c.get('/export', params)
                task_id=resp.getheader('task-id')
                restore_actions.append(lambda: cancel_task(session,task_id))
                if show_progress:
                    log.debug("Starting progress monitor")
                    progress=ProgressMonitor(session, task_id)
                    progress.start()
                s=rack.create_slot()
                writer=s.get_writer()
                bufsize=65536 # 64k is enough - around this size got best performance
                while True:
                    data=resp.read(bufsize)
                    if not data: break
                    writer.write(data)
                s.close() # close only if finished
            if progress:
                progress.join(10)
                if progress.is_alive():
                    log.warn('Task did not finished')
                else:
                    if progress.error:
                        msg='Export failed: %s'%progress.result
                        log.error(msg)
                        print >>sys.stderr, msg
                progress.stop()
            rack.shrink()
        finally:
            try:
                for a in reversed(restore_actions):
                    a()
            except Exception, e:
                traceback.print_exc()
                log.error('Restore action %s after backup failed, this may leave some temporary snapshots or machine is halted. Error: %s %s', str(a), type(e), str(e))
        log.info('Finished backup for VM %s (uuid=%s) on server %s', vm_name, uuid, host['name']) 
        


class BackupOneCommand(CommandForOneVM, BackupOne):
    name="backup"
    description="Backups one VM"
    def execute_for_one(self, session, host):
        vm_name=self.args.vm
        show_progress=not self.args.no_progress
        force_shutdown=self.args.shutdown
        
        vm_id=self.find_vm(session, host)
        storage=Storage(self.config['storage_root'], self.config.get('storage_retain', 3),
                        self.config.get('compress_level', 1), self.config.get('compress', 'client'))
        with RuntimeLock(BACKUP_LOCK,'Another backup is running!'):
            self.backup(session, vm_id, vm_name, host, storage, force_shutdown, show_progress,
                        self.config.get('compress') == 'server', insecure=self.args.insecure)
        
        
    
    @classmethod
    def add_params(self, parser):
        super(BackupOneCommand, self).add_params(parser)
        parser.add_argument('--no-progress', action='store_true', help="Do not print progress")
        parser.add_argument('--shutdown', action='store_true', help="Shutdown running VM before backup and start afterward")
        parser.add_argument('--insecure', action='store_true', help="Enforces insecure (http) connection to server - can be bit faster")
        
def register_me(commands):
    register(commands, BackupOneCommand)