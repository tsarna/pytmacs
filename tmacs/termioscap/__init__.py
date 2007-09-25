from tmacs.termioscap._tclayer import _tclayer
from tmacs.ui.charcell import CharCellUI
from tmacs.app.commands import *
from Queue import Queue, Full
import os, __tmacs__, traceback
import sys

class TCLayer(_tclayer):
    cb = None
    count = 0

    def __init__(self, fd, reactor, term=None, termenc="utf8"):
        _tclayer.__init__(self, fd, reactor, term, termenc)
        self.queue = Queue(500)
        reactor.addReader(self)

    def doRead(self):
        try:
            data = os.read(self.fileno(), 10)
            self.feed(data)
        except:
            sys.stderr.write(''.join(traceback.format_exception(*sys.exc_info())))
            self.reactor.crash()

        r = self.reactor
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
        # print repr(event)
        try:
            self.queue.put(event)
        except Full:
            pass
        except AttributeError:
            sys.stderr.write("NO QUEUE YET")
        if (event[0] == u'q'):
            self.reactor.crash()

    def getevent(self):
        if self.ungotten:
            return self.ungotten.pop()
                        
        ev = self.queue.get()
        self.queue.task_done()
        return ev


class TCUI(TCLayer, CharCellUI):
    from tmacs.edit.view import View as window_class

    def __init__(self, reactor):
        TCLayer.__init__(self, sys.stdin.fileno(), reactor)
        CharCellUI.__init__(self)
        self.windows = []
        self.ungotten = []

    def add_window(self, buffer):
        w = self.window_class(buffer)
        if not self.windows:
            __tmacs__.curview = w
        self.windows.append(w)

    def ungetevent(self, ev):
        self.ungotten.append(ev)

    def write_message(self, message):
        self.moveto(0, 24)
        self.write(message)
        self.eeol()

    @command
    def forceredraw(self):
        lines = 24
        l = []
        for w in self.windows:
           b = w.buf
           if len(l) < (lines - 1):
               l.append("BUFFER %s:" % b.name)
               l.extend(b[:].encode('utf8').split('\n')[:lines - len(l) - 1])
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
