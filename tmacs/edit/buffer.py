# $Id: buffer.py,v 1.7 2007-09-18 23:15:31 tsarna Exp $

import os, codecs
from tmacs.edit.sniff import preSniff, postSniff
from tmacs.edit.ubuf import ubuf, marker
import __tmacs__

if not hasattr(__tmacs__, "buffers"):
    __tmacs__.buffers = {}

class Buffer(ubuf):
    # settings defaults
    fillcolumn = 78
    tab_stop = 8
    # start_line = 0    # line for editing to start on set
                        # by +nn args on command line
    
    def __init__(self, name, *args, **kw):
        self._set_name(name)
        
        if not kw.has_key('encoding'):
            kw['encoding'] = getattr(__tmacs__, 'default_encoding', 'utf8')

        apply(super(Buffer, self).__init__, args, kw)

    ### special attributes
    
    def _get_name(self):
        return self.__dict__['name']

    def _set_name(self, newname):
        oldname = self.__dict__.get('name')
        bl = __tmacs__.buffers
        if newname == oldname:
            pass
        elif bl.has_key(newname):
            raise KeyError, 'Already a buffer named "%s"' % newname
        else:
            if oldname is not None:
                del bl[oldname]
            bl[newname] = self
            self.__dict__['name'] = newname

    name = property(_get_name, _set_name)

    ### File-like interface
    
    def writelines(self, aniter):
        """Write each item in iter in turn (file-like interface)"""
        for x in aniter:
            self.write(x)

    ### Misc functions
    
    def execute(self):
        exec self[:] in __tmacs__.__dict__

    def get_display_name(self):
        dn = getattr(self, 'filename', '')
        if not dn:
            dn = getattr(self, 'display_name', '')
            if dn:
                dn = '[%s]' % dn
        return dn
            
    def next_buffer(self):
        names = __tmacs__.buffers.keys()
        names.sort()
        newname = names[(names.index(self.name) + 1) % len(names)]
        return __tmacs__.buffers[newname]

    def __repr__(self):
        return "<Buffer '%s'>" % self.name
        
    ### Marker
    
    def marker(self, *args):
        args = (self,) + args
        return apply(marker, args)
        
    ### File operations
            
    def save(self, filename=None):
        if filename is not None:
            self.filename = filename
        else:
            filename = getattr(self, 'filename', None)

        if filename is None:
            raise IOError, "no filename to save"

        f = open_for_write(self, filename)
        f.write(self[:])
        f.close()
        
        self.changed = False
                
    def load(self, filename, encoding=None, nofileok=False):
        self.filename = filename
        
        try:
            f = open(filename, 'r')
            l1, l2 = f.readline(), f.readline()
        except:
            if nofileok:
                l1 = l2 = ''
                f = None
            else:
                raise

        del self[:]
        
        vars, top = preSniff(self.filename, l1, l2)
        
        if encoding:
            vars['encoding'] = encoding
            
        if f is not None:
            self.append(top)

            for data in codecs.iterdecode(f, vars['encoding']):
                self.append(data)

            # postSniff(self, vars, self[-3036:])

        for key, val in vars.items():
            key = key.replace('-', '_')
            if key.startswith('_'):
                continue
            if not _protected_attr(key):
                if getattr(self.__class__, key, None) is None:
                    setattr(self, key, val)

        if hasattr(__tmacs__, 'postSniff'):
            __tmacs__.postSniff(self)        



def uniqify(n):
    n = [c for c in n]
    d = []
    while n[-1].isdigit():
        d.insert(0, n.pop())
    if d:
        d = str(int(''.join(d))+1)
    else:
        d = '0'

    return ''.join(n) + d
    


def loadFile(filename, bufname=None, encoding=None):
    if bufname is None:
        fn = bufname = os.path.basename(filename)

    while __tmacs__.buffers.has_key(bufname):
        bufname = uniqify(bufname)
        
    b = Buffer(bufname)
    b.loadFile(filename, encoding=encoding, nofileok=True)
        
    return b


def find_buffer(name):
    b = __tmacs__.buffers.get(name)
    if b is None:
        b = Buffer(name)

    return b
    

def _bufnamecmp(a, b):
    sa = a[0].startswith('__'); sb = b[0].startswith('__')
    if sa and sb or not sa and not sb:
        return cmp(a, b)
    elif sa:
        return 1
    else:
        return -1


def make_buffer_list():
    l = []
    
    for n, b in __tmacs__.buffers.items():
        f = " %"[b.read_only]
        f += " *"[b.changed]
        
        l.append([
            f + n, str(len(b)),
            getattr(b, 'encoding', ''),
            b.get_display_name()
        ])
        
    l.sort(cmp=_bufnamecmp)
    l.insert(0, ['  Buffer', 'Size', 'Enc', 'File'])
    
    dl = []
    for c in range(len(l[0])):
        dl.append(max([len(x[c]) for x in l]))
    
    for r in l:
        for c in range(len(r)-1):
            if c == 1: # size column
                r[c] = r[c].rjust(dl[c])
            else:            
                r[c] = r[c].ljust(dl[c])
            
    dl = ['-' * x for x in dl]
    l.insert(1, dl)
    
    b = find_buffer('__buffers__')
    
    b[:] = u'\n'.join([u' '.join(x) for x in l])

    b.changed = False
    b.display_name = 'List of Buffers'
    
    return b 
        


def open_for_write(buffer, filename):
    f = open(filename, 'w', encoding=buffer.encoding)

