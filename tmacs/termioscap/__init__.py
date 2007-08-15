from _tclayer import _TCLayer
from twisted.internet import reactor
import os, signal

import sys

class TCLayer(_TCLayer):
    def __init__(self, fd, ui, reactor, term=None, termenc=None):
        _TCLayer.__init__(self, fd, ui, reactor, term, termenc)
        reactor.addReader(self)

    def logPrefix(self):
        import pdb
        return 'tclayer'
    
    def doRead(self):
        data = os.read(self.fileno(), 10)
        self.send(data)

    def write(self, data):
        os.write(self.fileno(), data)
        
    def connectionLost(self, *a, **kw):
        pass
        


def start(ui):
    fd = os.open('/dev/tty', os.O_RDWR)
    t = TCLayer(fd, ui, reactor)

    def defer_SIGWINCH(signo, frame, t=t):
        t.reactor.callLater(0, t.got_SIGWINCH)

    signal.signal(signal.SIGWINCH, defer_SIGWINCH)

    return reactor
