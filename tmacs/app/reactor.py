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

class UntwistedReactor(object):
    """Primitive partial replacement for 'twisted.internet.reactor'"""

    running = False

    def __init__(self):
        self.readers = []
        self.writers = []
        self.laters = []

    checkInterval = 5

    def callLater(self, delay, callable, *args, **kw):
        insort_right(self.laters, _Appt(time()+delay, callable, args, kw))

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


class _Appt(object):

    """Simple "Appointment" for doing 'callLater()' invocations"""

    __slots__ = 'time','func','args','kw'

    def __init__(self,t,f,a,k):
        self.time = t; self.func = f; self.args = a; self.kw = k

    def __call__(self):
        return self.func(*self.args, **self.kw)

    def __cmp__(self, other):
        return cmp(self.time, other.time)
