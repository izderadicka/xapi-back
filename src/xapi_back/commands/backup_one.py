'''
Created on Sep 21, 2014

@author: ivan
'''

from xapi_back.cli import CommandForOneHost, register, CommandError, log,\
    ProgressMonitor
from xapi_back.http import Client
from xapi_back.util import extract_uuid
from xapi_back.storage import Storage
from xapi_back.common import uninstall_VM, cancel_task


class BackupOne(object):
    
    def backup(self, session, vm_id, vm_name, host, force_shutdown=False, show_progress=False):
        uuid=session.xenapi.VM.get_uuid(vm_id)  # @ReservedAssignment
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
                    tt_id=session.xenapi.VM.snapshot(vm_id,'Temp.backup of %s'% vm_name )
                    uuid=session.xenapi.VM.get_uuid(tt_id)
                    restore_actions.append(lambda: uninstall_VM(session, tt_id))
                    log.debug('Made snapshot of %s to uuid: %s', vm_name, uuid)
                else:
                    log.debug('Shutting down VM')
                    session.xenapi.VM.clean_shutdown(vm_id)
                    restore_actions.append(lambda: session.xenapi.VM.start(vm_id, False, False))
        
            sid=session._session
            rack=Storage(self.config['storage_root'], self.config.get('storage_retain', 3)).get_rack_for(vm_name)
            log.info('Starting backup for VM %s (uuid=%s) on server %s', vm_name, id, host['name'])
            progress=None
            with Client(host['url']) as c:
                resp=c.get('/export', {'session_id':sid, 'uuid': uuid})
                task_id=resp.getheader('task-id')
                restore_actions.append(lambda: cancel_task(session,task_id))
                if show_progress:
                    log.debug("Starting progress monitor")
                    progress=ProgressMonitor(session, task_id)
                    progress.start()
                s=rack.create_slot()
                writer=s.get_writer()
                bufsize=1048576
                while True:
                    data=resp.read(bufsize)
                    if not data: break
                    writer.write(data)
                s.close() # close only if finished
            if progress:
                progress.stop()
        finally:
            try:
                for a in reversed(restore_actions):
                    a()
            except Exception, e:
                log.error('Restore action after backup failed, this may leave some temporary snapshots or machine is halted. Error: %s' % e)
        log.info('Finished backup for VM %s (uuid=%s) on server %s', vm_name, id, host['name']) 
        


class BackupOneCommand(CommandForOneHost, BackupOne):
    name="backup"
    description="Backups one VM"
    def execute_for_one(self, session, host):
        vm_name=self.args.vm
        show_progress=not self.args.no_progress
        force_shutdown=self.args.shutdown
        
        ids=session.xenapi.VM.get_by_name_label(vm_name)
        log.debug('Found this VMs %s', ids)
        if not ids:
            raise CommandError('VM %s not found on server %s' % (vm_name, host['name']))
        elif len(ids)>1:
            raise CommandError('Name %s is not unique, please fix'% vm_name)
        
        vm_id=ids[0]
        
        self.backup(session, vm_id, vm_name, host, force_shutdown, show_progress)
        
        
    
    @classmethod
    def add_params(self, parser):
        super(BackupOneCommand, self).add_params(parser)
        parser.add_argument('--vm', required=True, help="Name of VM")
        parser.add_argument('--no-progress', action='store_true', help="Do not print progress")
        parser.add_argument('--shutdown', action='store_true', help="Shutdown running VM before backup and start afterward")
        
def register_me(commands):
    register(commands, BackupOneCommand)