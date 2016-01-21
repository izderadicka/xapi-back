#!/usr/bin/env python
'''
Created on Sep 25, 2014

@author: ivan
'''
from os.path import os
import re
import sys
import shutil

try:
    from setuptools import setup
    from setuptools.command.install import install
except ImportError:
    from distutils.core import setup
    from distutils.command.install import install
    
pkg_file= os.path.join(os.path.split(__file__)[0], 'src', 'xapi_back', '__init__.py')
cfg_file= os.path.join(os.path.split(__file__)[0], 'xapi-back.cfg.sample')

m=re.search(r"__version__\s*=\s*'([\d.]+)'", file(pkg_file).read())
if not m:
    print >>sys.stderr, 'Cannot find version of package'
    sys.exit(1)

version= m.group(1)

class CustInstall(install):
    def run(self):
        install.run(self)
        if os.geteuid()==0:
            cfg_dest='/etc/xapi-back.cfg'
        else:
            cfg_dest=os.path.expanduser('~/.xapi-back.cfg')
        if not os.path.exists(cfg_dest):
            try:
                if not self.dry_run:
                    shutil.copy(cfg_file, cfg_dest)
                print('IMPORTANT: Sample configuration file ws created in %s, you need to edit it before running the tool!' % cfg_dest)
            
            except (OSError, IOError):
                pass
    

setup(name='xapi-back',
      version=version,
      description='XenServer backup tool',
      package_dir={'':'src'},
      packages=['xapi_back', 'xapi_back.commands'],
      scripts=['src/xb'],
      author='Ivan Zderadicka',
      author_email='ivan.zderadicka@gmail.com',
      requires= ['tabulate (>=0.7.3)',],
      install_requires=['tabulate>=0.7.3',],
      provides=['xapi_back'],
      cmdclass={'install': CustInstall},
      keywords=['Xen', 'Hypervisor', 'backup'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                   'Natural Language :: English',
                   'Operating System :: POSIX',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Communications :: Email',
                   'Topic :: System :: Recovery Tools']
      
      )