from tmacs.termioscap._tclayer import _TCLayer
from Queue import Queue, Full
import os
import sys, traceback

class TCLayer(_TCLayer):
    cb = None
    count = 0

    def __init__(self, fd, reactor, term=None, termenc="utf8"):
        _TCLayer.__init__(self, fd, reactor, term, termenc)
        self.queue = Queue(500)
        reactor.addReader(self)

    def doRead(self):
        try:
            data = os.read(self.fileno(), 10)
            self.feed(data)
        except:
            sys.stderr.write(''.join(traceback.format_exception(*sys.exc_info())))
            self.reactor().crash()

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

    def postevent(self, event):
        self.count += 1
        print repr(event)
        try:
            self.queue.put(event)
        except Full:
            pass
        except AttributeError:
            sys.stderr.write("NO QUEUE YET")
        if (event[0] == u'q'):
            self.reactor().crash()


if __name__ == '__main__':
    from tmacs.app.reactor import UntwistedReactor as Reactor
    import sys
    
    fd = sys.stdin.fileno()
    reactor = Reactor()
    t = TCLayer(fd, reactor)
    #sys.stderr.write(repr(t.getmap()))
    #sys.stderr.flush()
    #from time import sleep
    #sleep(2)
    #t.cleanup()
    #sys.exit(0)
    try:    
        reactor.callLater(30, reactor.crash)
        reactor.run()
    finally:
        t.cleanup()
    print t.count

    print t.queue


"""
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
"""
