#!/usr/bin/env python -i

from tmacs.termioscap import *
import os


class T(object):
    def __init__(self):
        pass
        
    def setOutput(self, o):
        print `o`
        self.o = o
    
    def illegalSequence(self, x):
        print "illegal: %s" % `x`

    def send(self, x):
        print "sent: %s (%d)" % (`x`, len(x))


class reactor:
    def addReader(self, r):
        pass
        
g = T()

fd = os.open('/dev/null', os.O_RDWR)

t = TCLayer(fd, g, reactor())
t = TCLayer(fd, g, reactor())

t.send('A\x1bOAA\x1b')
print
t.send('O')
t.send('B\x1b')
t.send('OCx\xe2')
t.send('\x86\x90hi\xe2zzzzz\x1b')
t.timeout()
t.send('\x1b\x1bOA')

os.close(fd)
