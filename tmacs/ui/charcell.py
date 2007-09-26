from tmacs.edit.view import View
from tmacs.ui.base import *
import __tmacs__

__tmacs__.yesnomap = keymap("yesnomap", inherit=[__tmacs__.basemap],
mapping = {
    u'Y' : 'yes',
    u'y' : 'yes',
    u'N' : 'no',
    u'n' : 'no',
})


class CCAskYesNo(object):
    def __init__(self, default=None):
        self.quit = False
        self.answer = default
        self.keymap = __tmacs__.yesnomap.copy()
        if default is True:
            self.keymap.bind('<Return>', 'yes')
        elif default is False:
            self.keymap.bind('<Return>', 'no')

        
    def lookup_cmd(self, cmdname):
        return getattr(self, cmdname, None)

        
    @command
    def yes(self):
        self.answer = True
        self.quit = True

    @command
    def no(self):
        self.answer = False
        self.quit = True

    @command
    def notbound(self):
        pass # don't want beeping



class CharCellWindow(View):
    def __init__(self, buffer):
        super(CharCellWindow, self).__init__(buffer)
        self._status_upd = True
        # force redraw of all

    def copy(self):
        """
        Return a copy of this window. It is half-shallow/half-deep copy
        (middle of the pool copy?) in that markers will be copies
        of the originals but the buffer will be shared.
        
        Positions will be shared, overlapping the original. They will
        need to be adjusted to not overlap. The new window will not be active.
        """
        
        n = super(CharCellWindow, self).copy()
        n.left, n.top, n.width, n.height = self.left, self.top, self.width, self.height
        n._active = False
        
        return n
        
    def position(self, left, top, width, height):
        """
        Move to the specified size and position. Not bounds checked.
        """
        # XXX try to keep remaining lines in same place:
        # adjust start by negative the amount that top moves
        # dot may end up outside the new window and if so we'll
        # need to recalculate start

        self.left, self.top, self.width, self.height = left, top, width, height
        self._status_upd = True

        # force redraw of all        

    def focus(self):
        """
        Take focus (become the active window)
        """
        self._active = True
        self._status_upd = True
        
    def blur(self):
        """
        Give up focus (losing active status).
        """
        self._active = False
        self._status_upd = True
        
    def refresh(self, ui):
        """
        Redraw ourself.
        """
        if self._status_upd:
            if self._active:
                l = '== ' + self.buf.name + ' '
                l += '=' * (self.width - len(l))
            else:
                l = '   ' + self.buf.name + ' '
                l += ' ' * (self.width - len(l))

            l = l[:self.width]
        
            ui.moveto(0, self.top + self.height - 1)
            ui.standout()
            ui.write(l)
            ui.nostandout()
            self._status_upd = False

        # XXX
        txt = self.buf[:].split('\n')[:self.height-1]
        row = self.top
        for l in txt:
            ui.moveto(self.left, row)
            ui.write(l[:self.width])
            ui.eeol()
            row += 1

        for row in range(row, self.top + self.height - 1):
            ui.moveto(self.left, row)
            ui.eeol()

        

class CharCellUI(UIBase):
    window_class = CharCellWindow
    
    def __init__(self):
        super(CharCellUI, self).__init__()
        self._message = ""
        self._message_upd = False
        self.curview = None
    
    def add_window(self, buffer):
        """
        Add a window. Used at startup time to indicate a buffer we
        want to start displaying. Not valid after layout_windows()
        
        XXX should enforce that
        """
        self.windows.append(self.window_class(buffer))
            
    def layout_windows(self):
        """
        Distribute screen space to requested windows
        
        XXX should become balancewindows
        """
        lines = self.lines - 1
        top = 0

        wl = self.windows        
        # start dumping the last-added windows 
        nw = len(wl)
        while (nw > (lines // 2)):
            wl.pop()
            nw -= 1

        # now divide out the space            
        for w in wl:
            height = lines // nw
            w.position(0, top, self.columns, height)
            top += height
            lines -= height            
    
        self.focuswindow(wl[0])

    def focuswindow(self, window):
        """
        Choose a window to receive focus.
        """
        if self.curview is not None:
            self.curview.blur()
        self.curview = window
        window.focus() 
        
    def _pickwindow(self, n):
        """
        Convert a universal argument into a window.
        Default is current, 1 is the topmost, 2 second from top, etc.
        Out of range throws IndexError.
        """
        if n is True:
            return self.curview

        if n >= 1 and n <= len(self.windows):
            return self.windows[n - 1]

        raise IndexError, "Window number out of range %d..%d" % (1, len(self.windows))
                    
    def askyesno(self, prompt, default=None):
        """
        Ask a yes/no question. A default may be specified in
        which case <Return> activates the default.
        
        Prompt should not end with a quesiton mark, since an ending
        will be calculated and applied.
        """
        state = CCAskYesNo(default)
        if default == True:
            yn = "Y/n"
        elif default == False:
            yn = "y/N"
        else:
            yn = "y/n"
            
        prompt += " [%s]? " % yn
        self.set_message(prompt)
        try:
            saved_view = self.curview
            self.curview = state
            self.cmdloop(state)
            return state.answer            
        finally:
            # remove circular ref
            self.clear_message()
            self.curview = saved_view

    def set_message(self, message):
        """
        Set the status line to display a message.
        Unlike write_message() this will always stay displayed until
        cleared (explicitly or by readind new keys) or a new message is set.
        """
        self._message = message
        self._message_upd = True
        self.refresh()
        
    def clear_message(self):
        """
        Clear the status line message, if any. Note that if a minibuffer
        is in effect we'll go back to displaying that instead of
        actually clearing the line.
        """
        if self._message:
            self._message = ""
            self._message_upd = True
            self.refresh()
        
    def write_message(self, message):
        """
        Display a message on the status line. It will stay displayed
        under the same conditions as set_message() message, unless
        a minibuffer is in effect in which case it will automatically
        clear after a few seconds to reveal the minibuffer.
        """
        self._message = message
        self._message_upd = True
        if self.minibufs:
            self.sitfor(self.default_sit)
            self.clear_message()
        else:
            self.refresh()
        
    def refresh(self, force=False):
        """
        Update the display. If input is pending, the refresh will be
        skipped or interrupted, unless Force is set.
        """
        if force or not self.evpending():
            if self._message_upd:
                self.moveto(0, self.lines-1)
                m = self._message[:self.columns]
                self.write(m.encode('utf8'))
                self.eeol()
                self._message_upd = False

            for w in self.windows:
                w.refresh(self)

    def sitfor(self, secs):
        """
        Refresh the display and wait for the specified number of seconds
        or until there is an input event available.
        """
        self.refresh()
        self.waitevent(secs)


    @command
    @annotate(None)
    @annotate(UniArg)
    def splitwindow(self, focustop=True):
        """"
        Split the current window vertically into two windows viewing the
        same buffer. By default focus goes to the top window, with any
        argument other than True, the bottom is focused
        """

        w = self.curview
        if w.height < 4:
            raise ValueError, "Window too small to split"
        nw = w.copy()
        
        nwh = nw.height // 2
        nw.position(nw.left, nw.top + w.height - nwh, nw.width, nwh)
        w.position(w.left, w.top, w.width, w.height - nwh)
        
        wl = self.windows
        wl.insert(wl.index(w) + 1, nw)

        if focustop is not True:
            self.focuswindow(nw)
        else:
            self.focuswindow(w)

    @command
    @annotate(None)
    @annotate(UniArg)
    def onlywindow(self, winnum=True, window=None):
        """
        Delete all windows but the specified one (default current)
        """
        if window is None:
            window = self._pickwindow(winnum)

        self.windows = [window]
        window.position(0, 0, self.columns, self.lines-1)
        
        

class TestUI(CharCellUI):
    def __init__(self):
        self.windows = []
        self.ungotten = []


    def getevent(self):
        if self.ungotten:
            return self.ungotten.pop()
            
        ri = raw_input('KeySym: ')
        ev = keysym(ri)
        if len(ev) != 1:
            return keysym("<IllegalSequence>"), ri
        return ev, None


    def ungetevent(self, ev):
        self.ungotten.append(ev)

        
    @command
    @annotate(None)
    @annotate(PromptText("Message:"))
    def write_message(self, msg):
        print msg.encode('utf8')


    @command
    def beep(self):
        sys.stderr.write('\a')


    @command
    def forceredraw(self):
        for w in self.windows:
            b = w.buf
            print "BUFFER %s:" % b.name
            print b[:].encode('utf8')


    def askstring(self, prompt):
        return raw_input(prompt)



def test():
    import tmacs.ui.defmaps
    
    __tmacs__.ui = ui = TestUI()
    
    ui.cmdloop(__tmacs__)
