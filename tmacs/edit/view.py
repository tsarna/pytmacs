from tmacs.app.commands import *
from tmacs.edit.buffer import make_buffer_list

class BasicView(object):
    def lookup_cmd(self, cmdname):
        return getattr(self, cmdname, None)

    ### Cursor Movement
    
    @command
    @annotate(None)
    @annotate(UniArg)
    def prev(self, n=True):
        self.dot -= n

    @command
    @annotate(None)
    @annotate(UniArg)
    def next(self, n=True):
        self.dot += n

    @command
    @annotate(None)
    def tobufstart(self):
        self.dot.tobufstart()

    @command
    @annotate(None)
    def tobufend(self):
        self.dot.tobufend()

    @command
    @annotate(None)
    def tolinestart(self):
        self.dot.tolinestart()
        
    @command
    @annotate(None)
    def tolineend(self):
        self.dot.tolineend()
        
    @command
    @annotate(None)
    @annotate(UniArg)
    def prevword(self, n=True):
        self.dot.prevword(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def nextword(self, n=True):
        self.dot.nextword(n)

    ### Editing
    
    @command
    @annotate(None)
    @annotate(UniArg)
    def wordtitle(self, n=True):
        self.dot.wordtitle(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def wordlower(self, n=True):
        self.dot.wordlower(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def wordupper(self, n=True):
        self.dot.wordupper(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def insertspace(self, n=True):
        self.dot.insertnext(u' ' * n)

    @command
    @annotate(None)
    @annotate(KeySeq)
    @annotate(UniArg)
    def insert(self, text, n=True):
        self.dot.insert(text * n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def delprev(self, n=True):
        self.dot.delprev(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def delnext(self, n=True):
        self.dot.delnext(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def delprevword(self, n=True):
        self.dot.delprevword(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def delnextword(self, n=True):
        self.dot.delnextword(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def insertspace(self, n=True):
        self.dot.insertnext(u' ' * n)


    
class View(BasicView):
    mark = None
    
    def __init__(self, buffer):
        if buffer is not None:
            self.setbuffer(buffer)

    def copy(self):
        n = self.__class__(None)
        n.buf = self.buf
        n.dot = self.dot.copy()
        if self.mark is None:
            n.mark = None
        else:
            n.mark = self.mark.copy()
        n.keymap = self.keymap

        return n
        
    def setbuffer(self, buffer):
        self.buf = buffer
        self.dot = buffer.marker()
        self.mark = None
        sl = getattr(buffer, 'start_line', None)
        if sl is not None:
            self.dot.toline(sl)
            del buffer.start_line
        self.keymap = buffer.keymap

    ### Buffer Commands

    @command
    @annotate(None)
    @annotate(AnyFileName("Name: "))
    def setfilename(self, name):
        self.buf.filename = name

    @command
    def markunchanged(self):
        self.buf.changed = False

    @command
    @annotate(None)
    @annotate(NewBufferName("Change buffer name to: "))
    def renamebuffer(self, name):
        self.buf.name = name

    @command
    @annotate(None)
    @annotate(UniArg)
    @returns(MessageToShow)
    def setfillcolumn(self, n=True):
        self.buf.fillcolumn = n
        return "[Fill column is %d]" % n
        
    @command
    @returns(BufferToShow)
    def bufferlist(self):
        return make_buffer_list()
        
    ### Cursor Movement

    @command
    @annotate(None)
    @annotate(UniArgOrInt("Line to GOTO: "))
    def toline(self, n):
        self.dot.toline(n)
        
    @command
    @annotate(None)
    @annotate(UniArg)
    def prevline(self, n=True):
        self.dot.prevline(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def nextline(self, n=True):
        self.dot.nextline(n)

    ### Editing

    @command
    @annotate(None)
    @annotate(UniArg)
    def newline(self, n=True):
        self.dot.insert(u'\n' * n)
        
    @command
    @annotate(None)
    @annotate(UniArg)
    def openline(self, n=True):
        self.dot.insertnext(u'\n' * n)

    ### View
    
    @command
    @annotate(None)
    @returns(MessageToShow)
    def swapdotandmark(self):
        if self.mark is None:
            return "No mark in this window"
        self.dot, self.mark = self.mark, self.dot

    @command
    @annotate(None)
    @returns(MessageToShow)
    def setmark(self):
        self.mark = self.dot.copy()
        return "[Mark set]"

    @command
    def nextbuffer(self):
        self.setbuffer(self.buf.next_buffer())

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
    @returns(MessageToShow)
    def regionlower(self, start=None, end=None):
        start, end = self.getregion(start, end)
        if start is None:
            return "No mark set in this window"
        self.buf[start:end] = self.buf[start:end].lower()
    
    @command    
    @returns(MessageToShow)
    def regionupper(self, start=None, end=None):
        start, end = self.getregion(start, end)
        if self.mark is None:
            return "No mark set in this window"
        self.buf[start:end] = self.buf[start:end].upper()

