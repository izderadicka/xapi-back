'''
Created on Sep 21, 2014

@author: ivan
'''

import logging
from xapi_back import XenAPI
log=logging.getLogger()

AUTOBACKUP_KEY='autobackup'
AUTOBACKUP_BATCH="autobackup_set"
BACKUP_LOCK='xapi_backup.lock'



def uninstall_VM(session, vm_id):
    vbds= session.xenapi.VM.get_VBDs(vm_id)
    vdis=[session.xenapi.VBD.get_VDI(ref) for ref in vbds \
          if session.xenapi.VBD.get_other_config(ref).has_key('owner')]
    log.debug('Deleting VM %s', vm_id)
    session.xenapi.VM.destroy(vm_id)
    for d in vdis:
        try:
            log.debug('Deleting VDI %s',d)
            session.xenapi.VDI.destroy(d)
        except XenAPI.Failure, e:
            log.error('Cannot delete temporary snapshot vdi %s, error: %s' % (d,e))
            
def cancel_task(session,task_ref):
    try:
        log.debug('Canceling task %s', task_ref)
        session.xenapi.task.cancel(task_ref)
    except XenAPI.Failure, f:
        log.debug('Cannot cancel task: %s'% f)
        
    
        
