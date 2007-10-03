# $Id: __init__.py,v 1.16 2007-10-03 15:02:06 tsarna Exp $

from tmacs.termioscap._tclayer import _tclayer
from tmacs.ui.charcell import CharCellUI
from tmacs.app.commands import *
from Queue import Queue, Full, Empty
import sys, os, __tmacs__, traceback

class TCLayer(_tclayer):
    count = 0

    def __init__(self, ifd, ofd, reactor, term=None, termenc=None):
        self.queue = Queue(500)
        _tclayer.__init__(self, ifd, ofd, reactor, term, termenc)
        self.ungotten = []

    def write(self, data):
        os.write(self.fileno(), data.encode('utf8'))

    def postevent(self, event):
        self.count += 1
        #print >>sys.stderr, repr(event)
        try:
            self.queue.put(event)
        except Full:
            pass
        if (event[0] == u'q'):
            __tmacs__._quit = True
            self.reactor.crash()

    def getevent(self):
        if self.ungotten:
            return self.ungotten.pop()
                        
        ev = self.queue.get()
        self.queue.task_done()
        return ev

    def ungetevent(self, ev):
        self.ungotten.append(ev)

    def waitevent(self, secs):
        if self.ungotten:
            return True
        try:
            ev = self.queue.get(timeout=secs)
            self.ungetevent(ev)
            return True
        except Empty:
            return False
            
    def evpending(self):
        if self.ungotten:
            return True
        return not self.queue.empty()

                

class TCUI(TCLayer, CharCellUI):
    activechar = ">"
    #activechar = u"\u2550"
    #activechar = u"\xbb"
        
    def __init__(self, reactor):
        TCLayer.__init__(self, sys.stdin.fileno(), sys.stdout.fileno(), reactor)
        CharCellUI.__init__(self)
        self.windows = []

    @command
    def forceredraw(self):
        l = []
        for w in self.windows:
           b = w.buf
           if len(l) < (self.lines - 1):
               l.append("BUFFER %s:" % b.name)
               l.extend(b[:].encode('utf8').split('\n')[:self.lines - len(l) - 1])
        self.moveto(0, 0)
        self.write('\r\n'.join(l))



if __name__ == '__main__':

    from tmacs.app.reactor import UntwistedReactor as Reactor
    import sys
    
    fd = sys.stdin.fileno()
    reactor = Reactor()

    t = TCLayer(fd, reactor)
    try:    
        reactor.callLater(30, reactor.crash)
        reactor.run()
    finally:
        t.cleanup()
    print t.count

    print t.queue
