import os, codecs
from tmacs.edit.sniff import preSniff, postSniff
import __tmacs__


try:
    __tmacs__.buffers
except:
    __tmacs__.buffers = {}

_protected_attr = {
    'name' : 1,
    'dirname' : 1,
    'filename' : 1
}.has_key    


class FakeBuffer(object):
    buf = u""
    
    def append(self, txt):
        self.buf = self.buf + txt

    def __str__(self):
        return self.buf

    def __len__(self):
        return len(self.buf)
        
    def __setitem__(self, i, v):
        self.buf = u''        
        
    def __delitem__(self, i):
        self.buf = u''   


    
class Buffer(FakeBuffer):
    def __init__(self, name):
        buffers = __tmacs__.buffers
        if buffers.has_key(name):
            raise KeyError, "buffer named '%s' already exists" % name
        
        self.name = name
        buffers[name] = self

        self.coding = __tmacs__.default_coding

    def loadFile(self, filename, coding=None, nofileok=False):
        self.dirname = os.path.dirname(filename)
        self.filename = os.path.basename(filename)
        
        try:
            f = open(filename, 'r')
            l1, l2 = f.readline(), f.readline()
        except:
            if nofileok:
                l1 = l2 = ''
                f = None
            else:
                raise

        self[:] = u''
        
        vars, top = preSniff(self.filename, l1, l2)
        
        if coding:
            vars['coding'] = coding
            
        if f is not None:
            self.append(top)

            for data in codecs.iterdecode(f, vars['coding']):
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
    


def loadFile(filename, bufname=None, coding=None):
    if bufname is None:
        fn = bufname = os.path.basename(filename)

    while __tmacs__.buffers.has_key(bufname):
        bufname = uniqify(bufname)
        
    b = Buffer(bufname)
    b.loadFile(filename, coding=coding, nofileok=True)
        
    return b


def findBuffer(name):
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
     
def makeBufferList():
    l = []
    
    for n, b in __tmacs__.buffers.items():
        modes = ','.join(getattr(b, 'modes', ['-'])) # XXX
        
        l.append([
            n, str(len(b)), modes, getattr(b, 'filename', ''),
            getattr(b, 'coding', ''), getattr(b, 'dirname', '')
        ])
        
    l.sort(cmp=_bufnamecmp)
    l.insert(0, ['Name', 'Size', 'Modes', 'Filename', 'Coding', 'Directory'])
    
    dl = []
    for c in range(len(l[0])):
        dl.append(max([len(x[c]) for x in l]))
    
    for r in l:
        for c in range(len(r)):
            r[c] = r[c].ljust(dl[c])
            
    dl = ['-' * x for x in dl]
    l.insert(1, dl)
    
    b = findBuffer('__buffers__')
    b[:] = u""
    b.append(u'\n'.join([u' '.join(x) for x in l]))

    return b        
        
