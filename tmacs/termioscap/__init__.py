from _tclayer import _TCLayer
from twisted.internet import reactor
import os, signal

import sys

class TCLayer(_TCLayer):
    cb = None
    
    def __init__(self, fd, ui, reactor, term=None, termenc="utf8"):
        _TCLayer.__init__(self, fd, ui, reactor, term, termenc)
        reactor.addReader(self)

    def logPrefix(self):
        import pdb
        return 'tclayer'
    
    def doRead(self):
        data = os.read(self.fileno(), 10)
        self.send(data)

        r = self.reactor()
        if self.cb is None:
            self.cb = r.callLater(0.3, self.timeout)
        else:
            self.cb.reset(0.3)
            
    def timeout(self):
        self.cb = None
        _TCLayer.timeout(self)
            
    def write(self, data):
        os.write(self.fileno(), data)
        
    def connectionLost(self, *a, **kw):
        pass
        


def start(ui):
    fd = os.open('/dev/tty', os.O_RDWR)
    t = TCLayer(fd, ui, reactor)

    def defer_SIGWINCH(signo, frame, t=t):
        t.reactor().callLater(0, t.got_SIGWINCH)

    signal.signal(signal.SIGWINCH, defer_SIGWINCH)

    return reactor
