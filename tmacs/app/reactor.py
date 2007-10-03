# $Id: reactor.py,v 1.3 2007-10-03 03:02:47 tsarna Exp $

# The following is derived from the PEAK UntwistedReactor as of
# 12/28/2003, which carried the following copyright:
#    
# Copyright (C) 1996-2003 by Phillip J. Eby and Tyler C. Sarna.
# All rights reserved.  This software may be used under the same terms
# as Zope or Python.  THERE ARE ABSOLUTELY NO WARRANTIES OF ANY KIND.

from select import select, error as select_error
from bisect import insort_right
from time import sleep, time
from errno import EINTR

CANCELED, ACTIVE, CALLED = -1, 0, 1

class AlreadyCalled(Exception):
    """DelayedCall was already called"""

    
class AlreadyCanceled(Exception):
    """DelayedCall was canceled"""
    
    
class UntwistedReactor(object):
    """Primitive partial replacement for 'twisted.internet.reactor'"""

    running = False

    def __init__(self):
        self.readers = []
        self.writers = []
        self.laters = []

    checkInterval = 5

    def callLater(self, delay, callable, *args, **kw):
        return _DelayedCall(time()+delay, self, callable, args, kw)

    def addReader(self, reader):
         if reader not in self.readers: self.readers.append(reader)

    def addWriter(self, writer):
        if writer not in self.writers: self.writers.append(writer)

    def removeReader(self, reader):
        if reader in self.readers: self.readers.remove(reader)

    def removeWriter(self, writer):
        if writer in self.writers: self.writers.remove(writer)

    def run(self):
        try:
            self.running = True

            while self.running:
                try:
                    self.iterate()
                except:
                    raise
                    pass # log it
        finally:
            self.running = False

    def stop(self):
        self.callLater(0, self.crash)

    def crash(self):
        self.running = False

    def iterate(self, delay=None):
        now = time()
        wasRunning = self.running

        while (
            (self.running or not wasRunning)
            and self.laters and self.laters[0].time <= now
        ):
            try:
                self.laters.pop(0)()
            except:
                pass # XXX log it

        if delay is None:
            if not self.running:
                delay = 0
            elif self.laters:
                delay = self.laters[0].time - time()
            else:
                delay = self.checkInterval

        delay = max(delay, 0)

        if (self.readers or self.writers) and (self.running or not wasRunning):
            try:
                r, w, e = select(self.readers, self.writers, [], delay)
            except select_error,v:
                if v.args[0]==EINTR:    # signal received during select
                    return
                raise

            for reader in r: reader.doRead()
            for writer in w: writer.doWrite()

        elif delay and self.running:
            sleep(delay)


class _DelayedCall(object):
    """callLater() result objects"""

    __slots__ = 'time','reactor','state','func','args','kw'

    def __init__(self, t, r, f, a, k):
        self.time = t; self.reactor = r; self.state = ACTIVE
        self.func = f; self.args = a; self.kw = k
        insort_right(r.laters, self)

    def __call__(self):
        self.state = CALLED
        return self.func(*self.args, **self.kw)

    def __cmp__(self, other):
        return cmp(self.time, other.time)
        
    def active(self):
        """Not canceled or called"""

        return self.state == ACTIVE

    def cancel(self):
        """Don't run this delayed call"""
        
        if self.state == ACTIVE:
            self.state = CANCELED
            l = self.reactor.laters
            l.remove(self)
        elif self.state == CALLED:
            raise AlreadyCalled
        elif self.state == CANCELED:
            raise AlreadyCanceled

    def delay(self, delay):
        """Reschedule for 'delay' seconds from current scheduled time"""

        if self.state == ACTIVE:
            self.time += delay
            l = self.reactor.laters
            l.remove(self)
            insort_right(l, self)
        elif self.state == CALLED:
            raise AlreadyCalled
        elif self.state == CANCELED:
            raise AlreadyCanceled
        
    def reset(self, delay):
        """Reschedule for 'delay' seconds from now"""

        if self.state == ACTIVE:
            self.time = time() + delay
            l = self.reactor.laters
            l.remove(self)
            insort_right(l, self)
        elif self.state == CALLED:
            raise AlreadyCalled
        elif self.state == CANCELED:
            raise AlreadyCanceled
