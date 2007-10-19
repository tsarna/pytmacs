# $Id: test.py,v 1.1 2007-10-19 12:47:44 tsarna Exp $

class FakeReactor(object):
    """Fake reactor for TCLayer testing"""

    def addReader(self, r):
        """Print so we can tell we were attached"""
        
        print "Reader added"

    def callLater(self, time, callable):
        self.later = callable

    def itsLater(self):
        self.later()
