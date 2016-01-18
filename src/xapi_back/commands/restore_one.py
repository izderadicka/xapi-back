'''
Created on Sep 23, 2014

@author: ivan
'''

from xapi_back.cli import CommandForOneHost, register, CommandError, log,\
    ProgressMonitor
from xapi_back.http import Client
from xapi_back.storage import Storage
from xapi_back import XenAPI

class RestoreOneCommand(CommandForOneHost):
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
        rack=storage.get_rack_for(vm_name, exists=True)
        if not rack:
            raise CommandError('No backup to restore for VM %s' % vm_name)
        slot=rack.last_slot
        if not slot:
            raise CommandError('No backup to restore for VM %s' % vm_name)
        
        sid=session._session
        progress=None
        task_id=None
        if show_progress:
                    task_id=session.xenapi.task.create('VM.import', 'Import of %s'%vm_name)
                    log.debug("Starting progress monitor")
                    progress=ProgressMonitor(session, task_id)
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
            
            
                
                
        
    @classmethod
    def add_params(self, parser):
        super(RestoreOneCommand, self).add_params(parser)
        parser.add_argument('--vm', required=True, help="Name of VM")
        parser.add_argument('--no-progress', action='store_true', help="Do not print progress")
        parser.add_argument('--restore', action='store_true', help="Restore as replacement of original VM (MAC is same)")
        parser.add_argument('--sr_id', help="uuid of SR to import to (if other then default SR)")
        
def register_me(commands):
    register(commands, RestoreOneCommand)
        
        
