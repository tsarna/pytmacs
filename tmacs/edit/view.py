from tmacs.app.commands import *

class View(object):
    mark = None
    
    def __init__(self, buffer):
        self.buf = buffer
        self.dot = buffer.marker()

    ### Buffer Commands

    @command
    @annotate(AnyFileName("Name: "))
    def setfilename(self, name):
        self.buf.filename = name

    @command
    def markunchanged(self):
        self.buf.changed = False

    @command
    @annotate(NewBufferName("Change buffer name to: "))
    def renamebuffer(self, name):
        self.buf.name = name

    @command
    @annotate(UniArg)
    @returns(MessageToDisplay)
    def setfillcolumn(self, n=True):
        self.buf.fillcolumn = n
        return "[Fill column is %d]" % n
        
    ### Cursor Movement
    
    @command
    @annotate(UniArg)
    def prev(self, n=True):
        self.dot -= n

    @command
    @annotate(UniArg)
    def next(self, n=True):
        self.dot += n

    @command
    def tobufstart(self):
        self.dot.tobufstart()

    @command
    def tobufend(self):
        self.dot.tobufend()

    @command
    def tolinestart(self):
        self.dot.tolinestart()
        
    @command
    def tolineend(self):
        self.dot.tolineend()
        
    #XXX toline
            
    @command
    @annotate(UniArg)
    def prevword(self, n=True):
        self.dot.prevword(n)

    @command
    @annotate(UniArg)
    def nextword(self, n=True):
        self.dot.nextword(n)

    @command
    @annotate(UniArg)
    def prevline(self, n=True):
        self.dot.prevline(n)

    @command
    @annotate(UniArg)
    def nextline(self, n=True):
        self.dot.nextline(n)

    ### Editing
    
    @command
    @annotate(UniArg)
    def insertspace(self, n=True):
        self.dot.insertnext(u' ' * n)

    @command
    @annotate(UniArg)
    def newline(self, n=True):
        self.dot.insert(u'\n' * n)
        
    @command
    @annotate(UniArg)
    def openline(self, n=True):
        self.dot.insertnext(u'\n' * n)

    ### View
    
    @command
    @returns(MessageToShow)
    def swapdotandmark(self):
        if self.mark is None:
            return "No mark in this window"
        self.dot, self.mark = self.mark, self.dot

    @command
    @returns(MessageToShow)
    def setmark(self):
        self.mark = self.dot.copy()
        return "[Mark set]"

    ### Region

    def getregion(self, start, end):
        if start is None:
            start = self.mark
        if end is None:
            end = self.end
        if start is not None and start > end:
            start, end = end, start

        return start, end

        
    @command
    @returns(MessageToDisplay)
    def regionlower(self, start=None, end=None):
        start, end = self.getregion(start, end)
        if start is None:
            return "No mark set in this window"
        self.buf[start:end] = self.buf[start:end].lower()
    
    @command
    @returns(MessageToDisplay)
    def regionupper(self, start=None, end=None):
        start, end = self.getregion(start, end)
        if self.mark is None:
            return "No mark set in this window"
        self.buf[start:end] = self.buf[start:end].upper()

