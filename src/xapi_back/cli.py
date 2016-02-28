#! /usr/bin/env python
'''
Created on Sep 19, 2014

@author: ivan
'''
from xapi_back import __version__
import sys
import argparse
import json
import XenAPI
import logging 
import os.path
import importlib
import xapi_back.commands
from inspect import isclass
import traceback
import threading
log = logging.getLogger()
log.setLevel(logging.INFO)
import logging.handlers
from xapi_back.logmail import BufferingSMTPHandler


class ConfigError(Exception):
    def __init__(self, msg="Configuration Error"):
        super(ConfigError, self).__init__(msg)

DEFAULT_CONFIG_FILES=[os.path.expanduser('~/.xapi-back.cfg'), '/etc/xapi-back.cfg']
def read_config(config_file):
    if not config_file:
        for f in DEFAULT_CONFIG_FILES:
            if os.access(f, os.R_OK):
                config_file=f
                break
    if not config_file:
        msg='Config file is missing - either supply it via -c parameter or create one at default location %s'%DEFAULT_CONFIG_FILES
        log.error('msg')
        print >>sys.stderr, msg
        sys.exit(4)
    try:
        cfg = json.load(open(config_file))
        return cfg
    except ValueError, e:
        raise ConfigError('Invalid format of configuration file: %s' % e)
    except IOError, e:
        raise ConfigError('Cannot read configuration file: %s' % e)

class CommandError(Exception):
    def __init__(self, msg="Command Error"):
        super(CommandError, self).__init__(msg)     
            
class Command(object):  
    name = ""  
    description = ""
    def __init__(self, config, args):
        self.config = config
        self.args =args
        
    def execute(self):
        raise NotImplementedError
    
    @classmethod
    def add_args_parser(cls, subparsers):
        p = subparsers.add_parser(cls.name,  help=cls.description )
        cls.add_params(p)
        
    @classmethod
    def add_params(self, parser):
        pass
        
class XAPISession(object):
    """Wrapper for xapi sessions as context object"""
    def __init__(self, host_url, user=None, password=None):
        self._host_url = host_url
        self._user=user
        self._password=password
        self._session = None
        
    def __enter__(self):
        self._session = XenAPI.Session(self._host_url)
        self._session.xenapi.login_with_password(self._user,
                                                 self._password)
        return self._session
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.xenapi.logout()
            
                
                
class CommandForEachHost(Command):
    def __init__(self, config, args):
        Command.__init__(self, config, args)
        
    def execute_for_each(self, session, host):
        pass
    
    def after(self):
        pass
    
    def before(self):
        pass
    
    def execute(self):
        self.before()
        for s in self.config['servers']:
            log.debug('Opening session to %s', s.get('name'))
            with XAPISession(s['url'], s.get('user'), s.get('password')) as session:
                self.execute_for_each(session, s)
        self.after()
                
class CommandForOneHost(Command):
    def __init__(self, config, args):
        Command.__init__(self, config, args)
        
    def execute_for_one(self, session, host):
        pass
    
    def execute(self):
        host_name = self.args.host
        hosts = filter(lambda h: h['name']==host_name, self.config['servers'])
        if not hosts:
            raise CommandError('No such host configured: %s'%host_name)
        s=hosts[0]
        with XAPISession(s['url'], s.get('user'), s.get('password')) as session:
                self.execute_for_one(session, s)
            
    @classmethod
    def add_params(self, parser):
        super(CommandForOneHost, self).add_params(parser)
        parser.add_argument('--host', required=True, help='name of host to connect to (from config file)')

class CommandForOneVM(CommandForOneHost):
    
    def find_vm(self, session, host):
        vm_name = self.args.vm
        if self.args.uuid:
            vm_uuid=self.args.uuid.lower()
        else:
            vm_uuid=None
        ids=session.xenapi.VM.get_by_name_label(vm_name)
        log.debug('Found this VMs %s', ids)
        if not ids:
            raise CommandError('VM %s not found on server %s' % (vm_name, host['name']))
        else:
            def filter_by_uuid(vm_id):
                if vm_uuid:
                    vm_uuid2=session.xenapi.VM.get_uuid(vm_id)
                    return vm_uuid2.startswith(vm_uuid)
                return True
            ids = filter(filter_by_uuid,ids)
            if not ids:
                raise CommandError('VM %s, uuid=%s not found on server %s' % (vm_name, vm_uuid, host['name']))
            elif len(ids)>1:
                raise CommandError('Name %s, uuid=%s is not unique, please fix'% (vm_name, vm_uuid) )
            
        return ids[0]
    
    @classmethod
    def add_params(self, parser):
        super(CommandForOneVM, self).add_params(parser)
        parser.add_argument('--vm', required=True, help="Name of VM")
        parser.add_argument('--uuid', help="UUID of VM (can be just few starting chars) - use to distinguish VMs with same name")

class ProgressMonitor(threading.Thread):  
    def __init__(self, session, task_id, message="Progress {progress:0.2f}%\r", wait_period=1, 
                 print_progress=True):  
        super(ProgressMonitor, self).__init__(name="Progress monitor")
        self._evt=threading.Event()
        self._running=True
        self._ses=session
        self._task_id=task_id
        self._msg=message
        self._wait=wait_period
        self.daemon=True
        self.result=None
        self.error=False
        self._print_progress=print_progress
        
    def run(self):
        while self._running:
            try:
                if self._print_progress:
                    progress=self._ses.xenapi.task.get_progress(self._task_id) * 100.0
                    sys.stdout.write(self._msg.format(progress=progress))
                    sys.stdout.flush()
                status=self._ses.xenapi.task.get_status(self._task_id)
                if status != 'pending' and status !='cancelling':
                    if status=='failure':
                        self.error=True
                        errors=self._ses.xenapi.task.get_error_info(self._task_id)
                        log.error('Task has failed: %s', '; '.join(errors))
                        self.result='; '.join(errors)
                    elif status=='cancelled':
                        self.errors=True
                        msg='Task was canceled'
                        log.warn(msg)
                        self.result=msg
                    elif status =='success':
                        res=self._ses.xenapi.task.get_result(self._task_id)
                        self.result=res
                        log.debug('Task finished with this result: %s', res)
                    else:
                        self.errors=True
                        msg='Unknown task status: %s' % status
                        log.error(msg)
                        self.result=msg
                    break    
                self._evt.clear()   
                self._evt.wait(self._wait)
            except XenAPI.Failure,f:
                code=f.details[0]
                if code in ['HANDLE_INVALID']:
                    break
                else:
                    log.debug("Progress thread error: %s", f)
            except Exception, e: # ignore errors in progress monitoring
                log.debug("Progress thread error: %s", e)
            
    def stop(self):
        self._running=False
        self._evt.set()
        
    def join(self, timeout=None):
        self._evt.set()
        threading.Thread.join(self, timeout=timeout)
            
        
        
def register(commands, me):   
    if not isclass(me) and not issubclass(me, Command): 
        raise ValueError('This is not Command class!')
    commands[me.name]=me
                
def load_commands():   
    plugs={}
    path=os.path.split(xapi_back.commands.__file__)[0]
    for fname in os.listdir(path):
        mod,ext=os.path.splitext(fname)
        fname=os.path.join(path,fname)
        if os.path.isfile(fname) and ext=='.py' and not mod.startswith('_'):
            m=importlib.import_module('xapi_back.commands.'+mod)
            if hasattr(m, 'register_me') and callable(m.register_me):
                m.register_me(plugs)
                    
    return plugs                         
                
def prepare_env(sys_args):
    p = argparse.ArgumentParser(version=__version__)
    p.add_argument('-c', '--config', help="Configuration file")
    p.add_argument('--verbose', action="store_true", help="prints log output to stdout")
    p.add_argument('--debug', action="store_true", help="Logs debug events")
    p.add_argument('--log', help='Log file (can be also specified in config file')
    p.add_argument('--no-ssl-crt-check', action='store_true', help='Disables server certificate check in https (which is default in latest python)')
    cmd_parser=p.add_subparsers(help="Available commands", dest='cmd')
    cmd_classes=load_commands()
    for cc in cmd_classes:
        cmd_classes[cc].add_args_parser(cmd_parser)
    
    args = p.parse_args(sys_args)
    if args.verbose:
        logging.basicConfig(format='%(levelname)s:%(message)s')
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        
    if args.no_ssl_crt_check:
        import ssl
        try:
            _create_unverified_https_context = ssl._create_unverified_context  # @UndefinedVariable
        except AttributeError:
            # Legacy Python that doesn't verify HTTPS certificates by default
            pass
        else:
            # Handle target environment that doesn't support HTTPS verification
            ssl._create_default_https_context = _create_unverified_https_context
    try:
        cfg = read_config(args.config)
        if not 'compress' in cfg:
            cfg['compress']='client'
    except ConfigError, e:
        print >> sys.stderr, 'Cannot load config file %s : %s' % (args.config, e)
        sys.exit(1)
    
    log_file=args.log or cfg.get('log_file') 
    if log_file:
        h=logging.handlers.RotatingFileHandler(log_file,maxBytes=1000000,backupCount=3)
        h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s:%(message)s'))
        log.addHandler(h)
    else:
        log.addHandler(logging.NullHandler())
    
    mail_log_handler = None   
    if cfg.has_key('mail_log') and cfg['mail_log'].get('host'):
        mc=cfg['mail_log']
        mail_log_handler=BufferingSMTPHandler(mailhost=mc['host'], 
                           mailport= mc.get('port'), 
                           fromaddr= mc['from'], 
                           toaddr=mc['to'], 
                           subject=mc.get('subject', 'xapi-back log'),
                           secure=mc.get('secure', False),
                           user=mc.get('user'),
                           password=mc.get('password'))
        log.addHandler(mail_log_handler)
    
    cmd_class=cmd_classes.get(args.cmd)
    if not cmd_class:
        print >> sys.stderr, 'Internal error - unknown command : %s' % args.cmd
        sys.exit(2)
    return cmd_class(cfg,args), mail_log_handler
    
def main(sys_args):
    cmd, mail_log_handler = prepare_env(sys_args)
    try:
        log.debug('Executing command %s', cmd.name)
        cmd.execute()
    except Exception,e:
        print >> sys.stderr, "Error in command %s: %s" % (cmd.name, str(e))
        log.error('Command %s failed with %s', cmd.name, e)
        traceback.print_exc()
        sys.exit(3)
    finally:
        try:
            if mail_log_handler:
                mail_log_handler.flush()
        except Exception,e:
            print >>sys.stderr, 'Cannot email log: %s'%e
            traceback.print_exc()
            
    
if __name__ == '__main__':
    main(sys.argv[1:])
