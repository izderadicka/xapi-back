Simple backup tool for Xenserver/XCP.  Works with XenApi enabled hosts - XenServer,  XCP

WARNINGS
--------

1. Provided as is,  don't blame for problems. I tried to make it working reliably, 
but if you loose backup sorry.   I use it myself for backup of VMs,  but cannot capture all scenarios.
2. v0.4.0 is NOT compatible with previous versions storage -  it enables backup VMs with same name - this
means that directory name is now - vm_name#vm_uuid -   some previous backups will not be visible to the 
tool (directories should be manually merged or renamed)

USAGE
-----

Usage is pretty straightforward:
* command name is xb -  xb -h gives overall help,  xb command -h gives help for given command
* update config file (~/.xapi-back.cfg or /etc/xapi-back.cfg)  with details about hosts connections (sorry but passwords are in 
cleartext for now - so for security reason it's better have config file in your home directory with 0600 access) and root of your 
backup directory
* xb hosts -  test that you connect to hosts and
* xb list  - see all VMs available on your host(s)
* go to [xapi-back homepage](http://zderadicka.eu/projects/python/xapi-back-simple-xen-backup-tool/) for more details  

LICENSE
-------
Licensed under [GPL v3](http://www.gnu.org/copyleft/gpl.html) 

INSTALL
-------
```
#as root
pip install git+https://github.com/izderadicka/xapi-back.git#egg=xapi-back
```

HISTORY
-------
v.0.1 - Initial version
v.0.2 - Added possibility to set compression level (basically default compression level in python
				is 9 - highest compression, which is very slow -  it's ~ 6x slower that level 1 for  gain of 
				just few % space - it does not make sense to use it)
v.0.3 - Added ssl option to not check server certificates
v.0.3.1 - HTTP Redirect for VM export - this should enable to backup VMs from pool
v.0.3.2 - fixed restore to particular SR uuid
v.0.3.3 - backup in pool (HTTP redirect of export), fixed restore to particular SR
v.0.3.4 - option to restore snapshot as VM
v.0.3.5 - config file could be in home directory ( default)  
v.0.3.8 - possibility to send log via email 
v.0.4.1 - VMs can have same name
				- backup repository is not compatible with previous versions !
				- rename after restore
