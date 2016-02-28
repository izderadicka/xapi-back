'''
Created on Sep 23, 2014

@author: ivan
'''

from xapi_back.cli import CommandForOneVM, register, log, ProgressMonitor, CommandError
from xapi_back.http import Client
from xapi_back.storage import Storage
from xapi_back import XenAPI
from backup_one import SNAPSHOT_PREFIX
import re
import sys

class RestoreOneCommand(CommandForOneVM):
    name="restore"
    description="Restores backup to given host"
    
    def execute_for_one(self, session, host):
        vm_name=self.args.vm
        show_progress=not self.args.no_progress
        restore= self.args.restore
        srid = self.args.sr_id
        if srid:
            try:
                srid=session.xenapi.SR.get_by_uuid(srid)
            except XenAPI.Failure, f:
                raise CommandError('Invalid SR uuid: %s'%f.details[0])
        storage=Storage(self.config['storage_root'], self.config.get('storage_retain', 3),
                        compression_method=self.config.get('compress', 'client'))
        try:
            rack=storage.find_rack_for(vm_name,self.args.uuid)
        except Storage.NotFound, e:
            raise CommandError(str(e))
        slot=rack.last_slot
        if not slot:
            raise CommandError('No backup to restore for VM %s' % vm_name)
        
        sid=session._session
        
        task_id=session.xenapi.task.create('VM.import', 'Import of %s'%vm_name)
        log.debug("Starting progress monitor")
        progress=ProgressMonitor(session, task_id, print_progress=show_progress)
        progress.start()
        
        with Client(host['url']) as c:
            log.info('Starting import of VM %s'% vm_name)
            params= {'session_id':sid,  'task_id':task_id}
            if srid:
                params['sr_id']=srid
            if restore:
                params['restore']=restore
            log.debug('PUT with following params: %s', params)
            _resp=c.put('/import', slot.get_reader(), slot.size_uncompressed, params)
            
            log.info('Finished import of VM %s', vm_name,)
            
        if progress:
            progress.join(300)
            if progress.is_alive():
                log.warn('Task did not finished')
            else:
                if progress.error:
                    msg='Import failed: %s'%progress.result
                    log.error(msg)
                    print >>sys.stderr, msg
                else:
                    res=progress.result
                    m=re.search(r'<value>(OpaqueRef:[^<]+)</value>', res)
                    if m:
                        vm_id=m.group(1)
                        try:
                            
                            vm_uuid=session.xenapi.VM.get_uuid(vm_id)
                            msg='VM imported as uuid=%s'%vm_uuid
                            log.info(msg)
                            print msg
                        except XenAPI.Failure, f:
                            log.error('Cannot get imported VM uuid, error: %s'%f.details[0])
                        if self.args.as_vm:
                            try:
                                vm=session.xenapi.VM.get_record(vm_id)
                                if vm['is_a_template']:
                                    name=vm['name_label'].replace(SNAPSHOT_PREFIX, '')
                                    session.xenapi.VM.set_is_a_template(vm_id, False)
                                    if name:
                                        session.xenapi.VM.set_name_label(vm_id, name)
                                    log.info('Template restored as VM %s', name)
                                else:
                                    log.warn('VM is not a template')
                            except XenAPI.Failure,f:
                                log.error('Cannot change template to VM: %s',f)
                        if self.args.rename:
                            try:
                                session.xenapi.VM.set_name_label(vm_id, self.args.rename) 
                                log.info('VM Renamed to %s', self.args.rename)
                            except XenAPI.Failure,f:
                                log.error('Cannot rename VM: %s',f)  
                                     
                    else:
                        log.error('Import result does not contain VM id')
            progress.stop()
            
            
                
                
        
    @classmethod
    def add_params(self, parser):
        super(RestoreOneCommand, self).add_params(parser)
        parser.add_argument('--no-progress', action='store_true', help="Do not print progress")
        parser.add_argument('--restore', action='store_true', help="Restore as replacement of original VM (MAC is the same)")
        parser.add_argument('--sr_id', help="uuid of SR to import to (if other then default SR)")
        parser.add_argument('--as-vm', action='store_true', help='In case of snapshot (backup of running VM) restores as VM with same name (not as a template)')
        parser.add_argument('--rename', help='Rename restored VM to this new name')
        
def register_me(commands):
    register(commands, RestoreOneCommand)
        
        
