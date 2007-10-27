from tmacs.app.commands import *
from tmacs.edit.buffer import make_buffer_list
from tmacs.edit.ubuf import ubuf
import unicodedata
import __tmacs__

__tmacs__._killbuf = killbuf = ubuf()


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

    @command
    @annotate(None)
    @annotate(UniArg)
    @annotate(CmdLoopState)
    def killtext(self, n=True, state=__tmacs__):
        if n is True:
            self.dot.killline(killbuf, state.lastwaskill)
        else:
            self.dot.killtext(killbuf, n, state.lastwaskill)
        state.thisiskill = True
            
    @command
    @annotate(None)
    @annotate(SelectionStart)
    @annotate(SelectionEnd)
    @annotate(CmdLoopState)
    def copyregion(self, s, e, state=__tmacs__):
        killbuf.copyfrom(self.buf, s, e, state.lastwaskill)
        state.thisiskill = True
            
    @command
    @annotate(None)
    @annotate(SelectionStart)
    @annotate(SelectionEnd)
    @annotate(CmdLoopState)
    def killregion(self, s, e, state=__tmacs__):
        killbuf.cutfrom(self.buf, s, e, state.lastwaskill)
        state.thisiskill = True
            
    @command
    @annotate(None)
    @annotate(UniArg)
    def yank(self, n=True):
        for x in range(n):
            self.dot.insert(killbuf)

    @command
    @annotate(None)
    @annotate(SeqPromptedEvent)
    def quotenext(self, ev):
        self.dot.insert(ev[0])


    
class View(BasicView):
    mark = None
    
    def __init__(self, ui, buffer):
        self.ui = ui
        if buffer is not None:
            self.setbuffer(buffer)

    def copy(self):
        n = self.__class__(self.ui, None)
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

    @command
    @annotate(None)
    @annotate(UniArg)
    @returns(MessageToShow)
    def bufferpos(self, n=True):
        d = self.dot
        l = len(self.buf)

        if n is True:
            if l:
                p = u"%d" % (d * 100.0 / l)
            else:
                p = '-'
            
            if d == l:
                cd = u'(End)'
            else:
                c = self.buf[d]
                ct = unicodedata.category(c)
                if ct[0] == 'N':
                    dv = unicodedata.numeric(c, u'?')
                    ct += (u"=%g" % dv)
                cd = u"U+%04X (%s)" % (ord(c), ct)
            
            return u"Line ?/? Col ?/? Char %d/%d (%s%%) %s" % (
                d, l, p, cd
            )
        else:
            if d == l:
                cd = u'(End)'
            else:
                c = self.buf[d]
                cd = unicodedata.name(c, None)
                if cd is None:
                    cd = u"(no name, category %s)" % unicodedata.category(c)
                
                cd = "U+%04X %s" % (ord(c), cd)
        
            return cd
            
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

    @command
    @annotate(None)
    @annotate(UniArg)
    def twiddle(self, n=True):
        d = self.dot
        b = self.buf
        if d > 0:
            while n:
                if d == len(b):
                    d -= 1
                t = b[d-1:d+1]
                b[d-1:d+1] = t[1] + t[0]
                n -= 1
                d += 1 # XXX?
        else:
            raise IndexError, "Beginning of buffer"
            
    ### Regions
    
    @command
    @annotate(None)
    @annotate(SelectionStart)
    @annotate(SelectionEnd)
    @returns(MessageToShow)
    def countwords(self, s, e):
        lines = words = 0
        chars = (e - s)
        letters = 0

        category = unicodedata.category
                
        m = e.copy()
        m.tolinestart()
        while m > s:
            m.prevline()
            lines += 1
            
        b = e.buffer
        lw = False
        while m < e:
            c = b[m]
            cc = category(c)
            inw = cc[0] in 'LM' # in a word?
            if inw:
                letters += 1
                if not lw:
                    words += 1

            lw = inw
            m += 1
            
        if words:
            cw = "%g" % (float(chars) / words)
            lw = "%g" % (float(letters) / words)
        else:
            cw = lw = "-"
        
        return "chr %d letters %d words %d lines %d Avg chr/word %s ltr/wd %s" % (
            chars, letters, words, lines, cw, lw
        )

    
    @command
    def swapdotandmark(self):
        if not hasattr(self, 'mark'):
            raise IndexError, "No mark in this window"
        self.dot, self.mark = self.mark, self.dot
        self.dot.reset()


    @command
    @annotate(None)
    @returns(MessageToShow)
    def setmark(self):
        self.dot.reset()
        self.mark = self.dot.copy()
        return "[Mark set]"

    @command
    def nextbuffer(self):
        self.setbuffer(self.buf.next_buffer())

    def getregion(self):
        start = self.mark
        end = self.dot

        if start is None:
            raise ValueError, "no mark set in this window"
            
        if start > end:
            start, end = end, start

        return start, end
        
    def getregiontext(self):
        s, e = self.getregion()
        return self.buf[s:e]
        
    def setregiontext(self, text):
        s, e = self.getregion()
        self.buf[s:e] = text
        
    @command
    @annotate(None)
    @annotate(SelectedText)
    @returns(ReplacementText)
    def regionlower(self, text):
        return text.lower()
    
    @command
    @annotate(None)
    @annotate(SelectedText)
    @returns(ReplacementText)
    def regionupper(self, text):
        return text.upper()
