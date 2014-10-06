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
import logging.handlers



class ConfigError(Exception):
    def __init__(self, msg="Configuration Error"):
        super(ConfigError, self).__init__(msg)

class CommandError(Exception):
    def __init__(self, msg="Command Error"):
        super(CommandError, self).__init__(msg)      


def read_config(config_file):
    try:
        cfg = json.load(open(config_file))
        return cfg
    except ValueError, e:
        raise ConfigError('Invalid format of configuration file: %s' % e)
    except IOError, e:
        raise ConfigError('Cannot read configuration file: %s' % e)
    
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


class ProgressMonitor(threading.Thread):  
    def __init__(self, session, task_id, message="Progress {progress:0.2f}%\r", wait_period=5):  
        super(ProgressMonitor, self).__init__(name="Progress monitor")
        self._evt=threading.Event()
        self._running=True
        self._ses=session
        self._task_id=task_id
        self._msg=message
        self._wait=wait_period
        self.daemon=True
        
    def run(self):
        while self._running:
            progress=self._ses.xenapi.task.get_progress(self._task_id) * 100.0
            sys.stdout.write(self._msg.format(progress=progress))
            sys.stdout.flush()
            try:
                self._evt.wait(self._wait)
            except: # ignore errors of Event
                pass
            
    def stop(self):
        self._running=False
        self._evt.set()
            
        
        
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
    p.add_argument('-c', '--config', help="Configuration file", default='/etc/xapi-back.cfg')
    p.add_argument('--verbose', action="store_true", help="prints log output to stdout")
    p.add_argument('--debug', action="store_true", help="Logs debug events")
    p.add_argument('--log', help='Log file (can be also specified in config file')
    cmd_parser=p.add_subparsers(help="Available commands", dest='cmd')
    cmd_classes=load_commands()
    for cc in cmd_classes:
        cmd_classes[cc].add_args_parser(cmd_parser)
    
    args = p.parse_args(sys_args)
    if args.verbose:
        logging.basicConfig(format='%(levelname)s:%(message)s')
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    try:
        cfg = read_config(args.config)
    except ConfigError, e:
        print >> sys.stderr, 'Cannot load config file %s : %s' % (args.config, e)
        sys.exit(1)
    
    log_file=args.log or cfg.get('log_file') 
    if log_file:
        h=logging.handlers.RotatingFileHandler(log_file,maxBytes=1000000,backupCount=3)
        h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s:%(message)s'))
        log.addHandler(h)
    
    cmd_class=cmd_classes.get(args.cmd)
    if not cmd_class:
        print >> sys.stderr, 'Internal error - unknown command : %s' % args.cmd
        sys.exit(2)
    return cmd_class(cfg,args)
    
def main(sys_args):
    cmd = prepare_env(sys_args)
    try:
        log.debug('Executing command %s', cmd.name)
        cmd.execute()
    except Exception,e:
        print >> sys.stderr, "Error in command %s: %s" % (cmd.name, str(e))
        log.error('Command %s failed with %s', cmd.name, e)
        traceback.print_exc()
        sys.exit(3)
    
if __name__ == '__main__':
    main(sys.argv[1:])
