from tmacs.app.commands import *
from tmacs.edit.buffer import make_buffer_list
from tmacs.edit.ubuf import ubuf
import unicodedata
import __tmacs__

__tmacs__._killbuf = killbuf = ubuf()


class BasicView(object):
    def lookup_cmd(self, cmdname):
        """Find a command by name."""
        
        return getattr(self, cmdname, None)

    ### Cursor Movement
    
    @command
    @annotate(None)
    @annotate(UniArg)
    def prev(self, n=True):
        """Move cursor backwards by n characters."""
        self.dot -= n

    @command
    @annotate(None)
    @annotate(UniArg)
    def next(self, n=True):
        """Move cursor forwards by n characters."""
        self.dot += n

    @command
    @annotate(None)
    def tobufstart(self):
        """Move cursor to beginning of buffer."""
        self.dot.tobufstart()

    @command
    @annotate(None)
    def tobufend(self):
        """Move cursor to the end of the buffer."""
        self.dot.tobufend()

    @command
    @annotate(None)
    def tolinestart(self):
        """Move the cursor to the start of the line."""
        self.dot.tolinestart()
        
    @command
    @annotate(None)
    def tolineend(self):
        """Move the cursor to the end of the line."""
        self.dot.tolineend()
        
    @command
    @annotate(None)
    @annotate(UniArg)
    def prevword(self, n=True):
        """Move cursor backwards over n words."""
        self.dot.prevword(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def nextword(self, n=True):
        """Move cursor forwards over n words."""
        self.dot.nextword(n)

    ### Editing
    
    @command
    @annotate(None)
    @annotate(UniArg)
    def wordtitle(self, n=True):
        """Convert n words forward from cursor to title (initial caps) case."""
        self.dot.wordtitle(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def wordlower(self, n=True):
        """Convert n words forward from cursor to lower case."""
        self.dot.wordlower(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def wordupper(self, n=True):
        """Convert n words forward from cursor to upper case."""
        self.dot.wordupper(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def insertspace(self, n=True):
        """Insert n spaces"""
        self.dot.insertnext(u' ' * n)

    @command
    @annotate(None)
    @annotate(KeySeq)
    @annotate(UniArg)
    def insert(self, text, n=True):
        """Insert text n times at cursor position."""
        self.dot.insert(text * n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def delprev(self, n=True):
        """Delete n characters to the left."""
        self.dot.delprev(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def delnext(self, n=True):
        """Delete n characters to the right."""
        self.dot.delnext(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def delprevword(self, n=True):
        """Delete n words to the left."""
        self.dot.delprevword(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def delnextword(self, n=True):
        """Delete n words to the right."""
        self.dot.delnextword(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    @annotate(CmdLoopState)
    def killtext(self, n=True, state=__tmacs__):
        """
        With default argument, delete up to the end of line not including
        the newline, or if at the end of the line, delete the newline.

        With a positive numeric argument, deletes from dot through the
        next n lines, inclusive of their newlines. With a 0 or negative 
        argument, it deletes from dot to the beginning of the line and
        through the next n lines.
        
        The deleted text will be put in the kill buffer. If the last
        command was also a kill-type command the kill buffer will be
        appended to, otherwise it will replace the previous contents
        of the kill bufer.
        """
            
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
        """
        Copy the selected region (dot-mark) into the kill buffer,
        appending if the last command was a kill-type command, replacing
        the contents of the kill buffer otherwise. This command is
        considered a kill-type command.
        """
        
        killbuf.copyfrom(self.buf, s, e, state.lastwaskill)
        state.thisiskill = True
            
    @command
    @annotate(None)
    @annotate(SelectionStart)
    @annotate(SelectionEnd)
    @annotate(CmdLoopState)
    def killregion(self, s, e, state=__tmacs__):
        """
        Delete the selected region (dot-mark) and copy into the kill buffer,
        appending if the last command was a kill-type command, replacing
        the contents of the kill buffer otherwise. This command is
        considered a kill-type command.
        """

        killbuf.cutfrom(self.buf, s, e, state.lastwaskill)
        state.thisiskill = True
            
    @command
    @annotate(None)
    @annotate(UniArg)
    def yank(self, n=True):
        """Insert n copies of the kill buffer at the cursor position."""

        for x in range(n):
            self.dot.insert(killbuf)

    @command
    @annotate(None)
    @annotate(SeqPromptedEvent)
    def quotenext(self, ev):
        """
        Quote the next character for input. This allows inputting
        characters that are normally bound to commands.
        """
        
        self.dot.insert(ev[0])

    @command
    @annotate(None)
    @annotate(UniArg)
    def tab(self, n=True):
        """
        With universal argument, set the tab stop.
        Otherwise, handle inserting space until the next tab stop.
        If the tab stop is 0, insert a hard tab, otherwise insert
        enoough spaces to end on a stop.
        """
        if n is True:
            t = self.buf.tab_stop
            if t:
                n = t - (self.dot.display_col % t)
                self.insert(u" " * n)
            else:
                self.insert("\t")
        else:
            self.buf.tab_stop = abs(n)

    
class View(BasicView):
    mark = None
    
    def __init__(self, ui, buffer):
        self.ui = ui
        if buffer is not None:
            self.setbuffer(buffer)

    def copy(self):
        """Make c copy of this view. Used when splitting a view."""
        
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
        """Set the buffer that this view manipulates/displays."""
        
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
        """Set the filename for this buffer."""
        
        self.buf.filename = name

    @command
    def markunchanged(self):
        """Mark this buffer as unchanged."""
        
        self.buf.changed = False

    @command
    @annotate(None)
    @annotate(NewBufferName("Change buffer name to: "))
    def renamebuffer(self, name):
        """Rename this buffer."""
        
        self.buf.name = name

    @command
    @annotate(None)
    @annotate(UniArg)
    @returns(MessageToShow)
    def setfillcolumn(self, n=True):
        """Set the fill column of this buffer for wrapping."""
        
        self.buf.fillcolumn = n
        return "[Fill column is %d]" % n
        
    @command
    @returns(BufferToShow)
    def bufferlist(self):
        """Display a list of buffers."""
        
        return make_buffer_list()
        
    ### Cursor Movement

    @command
    @annotate(None)
    @annotate(UniArgOrInt("Line to GOTO: "))
    def toline(self, n):
        """Go to the nth line in the buffer. The first line is line 1.
        With a negative argument, counts lines backwards from the end."""

        self.dot.toline(n)
        
    @command
    @annotate(None)
    @annotate(UniArg)
    def prevline(self, n=True):
        """Move the cursor backwards (upwards) n lines."""
        self.dot.prevline(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def nextline(self, n=True):
        """Move the cursor forwards (downwards) n lines."""
        self.dot.nextline(n)

    @command
    @annotate(None)
    @annotate(UniArg)
    @returns(MessageToShow)
    def bufferpos(self, n=True):
        """
        Display information about the current position in the buffer.
        With a non-default argument, display the unicode name
        of the current character.
        """
        
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
        """Insert n newlines."""
        self.dot.insert(u'\n' * n)
        
    @command
    @annotate(None)
    @annotate(UniArg)
    def openline(self, n=True):
        """Insert n newlines after the cursor."""
        self.dot.insertnext(u'\n' * n)

    @command
    @annotate(None)
    @annotate(UniArg)
    def twiddle(self, n=True):
        """
        Swap characters on either side of the cursor, and advance
        one character. Repeat n times.
        """
        
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
        """
        Count charcters, words, and more in the selected region.
        """
        
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
        """Swap the dot (cursor position) with the mark."""
        
        if self.mark is None:
            raise IndexError, "No mark in this window"
        self.dot, self.mark = self.mark, self.dot
        self.dot.reset()


    @command
    @annotate(None)
    @returns(MessageToShow)
    def setmark(self):
        """Set the mark at the current cursor position ("dot")."""
        
        self.dot.reset()
        self.mark = self.dot.copy()
        return "[Mark set]"

    @command
    def nextbuffer(self):
        """Change this view's buffer to the next buffer in sequence."""
        
        self.setbuffer(self.buf.next_buffer())

    def getregion(self):
        """
        Helper method returns a tuple of two markers representing
        the begining and end of the selected region. The markers
        are always in start, end order regardless of the relative
        positions of dot and mark.
        """
        
        start = self.mark
        end = self.dot

        if start is None:
            raise ValueError, "no mark set in this window"
            
        if start > end:
            start, end = end, start

        return start, end
        
    def getregiontext(self):
        """Get the text within the selected region."""
        
        s, e = self.getregion()
        return self.buf[s:e]
        
    def setregiontext(self, text):
        """Replace the text in the selected region with new text."""
        
        s, e = self.getregion()
        self.buf[s:e] = text
        
    @command
    @annotate(None)
    @annotate(SelectedText)
    @returns(ReplacementText)
    def regionlower(self, text):
        """Lowercase the text in the selected region."""
        return text.lower()
    
    @command
    @annotate(None)
    @annotate(SelectedText)
    @returns(ReplacementText)
    def regionupper(self, text):
        """Uppercase the text in the selected region."""
        return text.upper()
