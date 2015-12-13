'''
Created on Sep 20, 2014

@author: ivan
'''
import os.path
import datetime
import time
from xapi_back.util import rand_hash
import gzip

SLOT_EXT='.xva.gz'
UNFINISHEND_EXT='.new'
SIZE_EXT='.size'


class Rack(object):
    def __init__(self, vm_name, root, max_slots, compression_level):
        self._path= os.path.join(root,vm_name)
        if not os.path.exists(self._path):
            os.mkdir(self._path)
        self._max_slots=max_slots
        self._comp_level=compression_level
        self.clear()
        
    @staticmethod
    def exists(vm_name, root):
        return os.path.exists(os.path.join(root,vm_name))
    
    def clear(self):
        """ Delete all unfinished backups"""
        for fname in os.listdir(self._path):
            if fname.endswith(UNFINISHEND_EXT):
                p=os.path.join(self._path, fname)
                os.unlink(p)
                size_file=p[:-len(UNFINISHEND_EXT)]+SIZE_EXT
                if os.path.exists(size_file):
                    os.unlink(size_file)
        
    def shrink(self):
        """ Removes old backups, so number of backups is less or equal then max"""
        slots= self.get_all_slots()
        for s in slots[self._max_slots:]:
            s.delete()
        
        
    def create_slot(self):
        """Create new slot with current date"""
        return Slot(self._path, compression_level=self._comp_level)
        
    @property    
    def last_slot(self):
        """Last valid slot with finished backup"""
        slots=self.get_all_slots()
        if slots:
            return slots[0]
        
    def get_all_slots(self):
        names=filter(lambda n: n.endswith(SLOT_EXT),os.listdir(self._path))
        slots= [Slot(self._path, n, compression_level=self._comp_level) for n in names]
        slots.sort(key=lambda i: i.created,reverse=True)
        return slots
        
    def get_slot(self, back_index):
        """ Get slot according to indes - 0 = current, 1 previous, 2 before previous ..."""
        slots=self.get_all_slots()
        if back_index<len(slots):
            return slots[back_index]
        
    def get_slot_before(self, timestamp):
        """ Get slot immediatelly before the timestamp (of datetime type or epoch time)"""
        if isinstance(timestamp, datetime):
            timestamp=(timestamp - datetime(1970, 1, 1)).total_seconds()
            
        for s in self.get_all_slots():
            if s.created<= timestamp:
                return s
        
class Storage(object):
    def __init__(self, root, max_slots_per_rack=5, compression_level=1):
        self._root=root
        if not os.path.isdir(root) or not os.access(root, os.R_OK|os.W_OK):
            raise Exception('Root storage dir %s does not exist or cannot read and write'%root)
        self._max_slots=max_slots_per_rack
        if not isinstance(compression_level, int) or compression_level < 0 or \
            compression_level > 9:
            raise ValueError('Invalid compression level - must be 0 - 9')
        self._comp_level = compression_level
        
    def get_rack_for(self, vm_name, exists=False):
        if exists and not Rack.exists(vm_name, self._root):
            return None
        return Rack(vm_name, self._root, self._max_slots, self._comp_level)
    
    def get_status(self):
        res={}
        for r in os.listdir(self._root):
            if os.path.isdir(os.path.join(self._root,r)):
                rack=self.get_rack_for(r)
                s=rack.last_slot
                last_backup=None
                if s:
                    last_backup=datetime.datetime.fromtimestamp(s.created) 
                    duration=s.duration
                else:
                    last_backup=None
                    duration=None
                res[r]={'last_backup':last_backup, 'duration':duration}
                
        return res
            
        
class WriterProxy(object):
    def __init__(self, f):
        self._size=0
        self._stream=f 
        self._started=time.time()
        
    def write(self, s):
        self._stream.write(s)
        self._size+=len(s)
    
    def close(self):
        self._stream.close()
        
    @property    
    def size(self):
        return self._size
    
    @property
    def started_on(self):
        return self._started
    
    
        
class Slot(object):
    def __init__(self, path, name=None, compression_level=1):
        if not name:
            h=rand_hash()[:4]
            name=time.strftime('%Y%m%d_%H%M%S_')+h+'_'+SLOT_EXT+UNFINISHEND_EXT
        self._path=os.path.join(path, name)
        self._open_file=None
        self._comp_level = compression_level
        
    @property    
    def size_uncompressed(self):
        with open(self._path+SIZE_EXT) as f:
            return int(f.readline())
        
    @property 
    def duration(self):
        with open(self._path+SIZE_EXT) as f:
            f.readline()
            return float(f.readline() or 0)
        
    @property
    def size(self):
        return os.stat(self._path).st_size
    
    @property
    def created(self):
        return os.stat(self._path).st_mtime
    
    def get_reader(self):
        self._open_file= gzip.open(self._path, 'rb')
        return self._open_file
        
    def get_writer(self):
        self._open_file= WriterProxy(gzip.open(self._path, 'wb', compresslevel=self._comp_level))
        return self._open_file
        
    def close(self):
        if self._open_file:
            self._open_file.close()
            if self._path.endswith(UNFINISHEND_EXT):
                new_path=self._path[:-len(UNFINISHEND_EXT)]
                assert isinstance(self._open_file, WriterProxy)
                duration=time.time()-self._open_file.started_on
                with file(new_path+SIZE_EXT, 'w') as f:
                    f.write(str(self._open_file.size))
                    f.write('\n')
                    f.write(str(duration))
                os.rename(self._path, new_path)
                self._path = new_path
                
            self._open_file=None
            
    def delete(self):
        if self._open_file:
            raise Exception('Slot is in use, cannot be deleted')
        os.unlink(self._path)
        size_file=self._path+SIZE_EXT
        if os.path.exists(size_file):
            os.unlink(size_file)
            
    def __enter__(self):
        return self
    
    def __exit__(self, ex, ex_type, frm):
        self.close()
            
        