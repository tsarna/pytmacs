from tmacs.edit.view import View
from tmacs.ui.base import *
import __tmacs__
from __tmacs__ import __version__ as app_version, __appname__ as app_name


__tmacs__.yesnomap = keymap("yesnomap", inherit=[__tmacs__.basemap],
mapping = {
    u'Y' : 'yes',
    u'y' : 'yes',
    u'N' : 'no',
    u'n' : 'no',
})


class CCAskYesNo(object):
    def __init__(self, default=None):
        self._quit = False
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
        self._quit = True

    @command
    def no(self):
        self.answer = False
        self._quit = True

    @command
    def notbound(self):
        pass # don't want beeping



class CharCellWindow(View):
    _active = False
    
    def __init__(self, ui, buffer):
        super(CharCellWindow, self).__init__(ui, buffer)
        self._status_upd = True
        # XXX force redraw of all

    def setbuffer(self, buffer):
        super(CharCellWindow, self).setbuffer(buffer)
        self._status_upd = True
        # XXX force redraw of all

    def copy(self):
        """
        Return a copy of this window. It is half-shallow/half-deep
        (middle of the pool?) copy in that markers will be copies
        of the originals but the buffer will be shared.
        
        Positions will be shared, overlapping the original. They will
        need to be adjusted to not overlap. The new window will not be active.
        """
        
        n = super(CharCellWindow, self).copy()
        n.left, n.top, n.width, n.height = self.left, self.top, self.width, self.height
        
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
        
    def refresh_status(self):
        """Refresh the status line."""

        if self._status_upd:
            ui = self.ui
            if self._active:
                f = '>'
                f = ui.activechar
            else:
                f = ' '

            b = self.buf
            if b.read_only:
                s = '%'
            elif b.changed:
                s = '*'
            else:
                s = f
            
            l = '%s%s %s %s %s%s %s ' % (f, s, app_name, app_version, f, f, b.name)
            dn = b.get_display_name()
            if dn:
                l += "%s%s %s " % (f, f, dn)
                
            l += f * (self.width - len(l))
            l = l[:self.width]
        
            ui.moveto(0, self.top + self.height - 1)
            ui.standout()
            ui.write(l)
            ui.nostandout()
            self._status_upd = False

        
    def refresh(self):
        """
        Redraw ourself.
        """
        self.refresh_status()
        # XXX
        ui = self.ui
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

    def index(self):
        """Find the index of this window"""
        
        return self.ui.windows.index(self)
        
    def delete(self):
        """Delete this window"""
        
        ui = self.ui
        if len(ui.windows) <= 1:
            raise ValueError, "Can't delete only window"

        # Give space to the window above, unless we're at the top
        i = self.index()
        if i == 0:
            other = ui.windows[1]
            first = self
        else:
            other = ui.windows[i - 1]
            first = other

        other.position(other.left, first.top,
            other.width, other.height + self.height)
            
        del ui.windows[i]
        
        if self._active:
            ui.focuswindow(other)
        
        del self.ui

    def only(self):
        """Make this the only window."""
        
        ui = self.ui
        ui.windows = [self]
        self.position(0, 0, ui.columns, ui.lines-1)


    def split(self):
        """Split this window."""
        
        if self.height < 4:
            raise ValueError, "Window too small to split"
        nw = self.copy()
        
        nwh = nw.height // 2
        nw.position(nw.left, nw.top + self.height - nwh, nw.width, nwh)
        self.position(self.left, self.top, self.width, self.height - nwh)
        
        wl = self.ui.windows
        wl.insert(self.index() + 1, nw)

        return nw


    @command
    @annotate(None)
    @annotate(UniArg)
    def growwindow(self, n=True):
        """Grow this window"""
        
        if n < 0:
            return self.shrinkwindow(-n)

        ui = self.ui
        if len(ui.windows) == 1:
            raise ValueError, "Can't grow only window"

        wi = self.index()
        if wi == len(ui.windows) - 1:
            # shrink above
            o = ui.windows[wi - 1]
            if (o.height - n) < 2:
                raise ValueError, "Not enough room to grow"

            self.position(self.left, self.top - n, self.width, self.height + n)
            o.position(o.left, o.top, o.width, o.height - n)
        else:
            # shrink below
            o = ui.windows[wi + 1]
            if (o.height - n) < 2:
                raise ValueError, "Not enough room to grow"

            self.position(self.left, self.top, self.width, self.height + n)
            o.position(o.left, o.top + n, o.width, o.height - n)

        
    @command
    @annotate(None)
    @annotate(UniArg)
    def shrinkwindow(self, n=True):
        """Shrink this window"""
        if n < 0:
            return self.growwindow(-n)

        ui = self.ui
        if len(ui.windows) == 1:
            raise ValueError, "Can't shrink only window"

        if (self.height - n) < 2:
            raise ValueError, "Can't make window that small"

        wi = self.index()
        if wi == len(ui.windows) - 1:
            # grow above
            o = ui.windows[wi - 1]
            self.position(self.left, self.top + n, self.width, self.height - n)
            o.position(o.left, o.top, o.width, o.height + n)
        else:
            # grow below
            o = ui.windows[wi + 1]
            self.position(self.left, self.top, self.width, self.height - n)
            o.position(o.left, o.top - n, o.width, o.height + n)
                

    @command
    @annotate(None)
    @annotate(UniArg)
    def resizewindow(self, n=True):
        """
        Resize this window. Must have a non-default argument.
        The size includes the content areas and not the status line.
        """
        
        if n is True or n == (self.height - 1):
            return
            
        return self.growwindow(n - (self.height - 1))
                
        

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
        want to start displaying.
        """
        self.windows.append(self.window_class(self, buffer))
            
    def layout_windows(self):
        """
        Called at startup to lay out the initially requested windows.
        """
        self.balancewindows()    
        self.focuswindow(self.windows[0])

    def getpopup(self):
        """
        Get a window to display a buffer in
        """
        if len(self.windows) == 1:
            self.splitwindow()
            return self.windows[1] # the other one
        else:
            for w in self.windows:
                if not w._active:
                    return w

    def popupbuffer(self, buffer):
        """
        Pop up a buffer in a new window, if not already displayed
        """
        for w in self.windows:
            if w.buf is buffer:
                return
        self.getpopup().setbuffer(buffer)
        
    @command
    def balancewindows(self):
        """
        Evenly Distribute screen space to requested windows.
        Drop later windows if there is no space.
        """
        lines = self.lines - 1
        top = 0

        wl = self.windows        
        # start dumping the last-added windows if not enough space
        nw = len(wl)
        while (nw > (lines // 2)):
            wl.pop()
            nw -= 1

        # now divvy up the space
        for w in wl:
            height = lines // nw
            w.position(0, top, self.columns, height)
            top += height
            lines -= height
            nw -= 1
            

    def focuswindow(self, window):
        """
        Choose a window to receive focus.
        """
        if self.curview is not None:
            self.curview.blur()
        self.curview = window
        window.focus() 
        
    def _pickwindow(self, n, delta=0):
        """
        Convert a universal argument into a window.
        1 is the topmost, 2 second from top, etc.
        Default is current, or next window if delta=1, or previous
        if delta=-1. Out of range throws IndexError.
        """
        if n is True:
            if delta:
                n = self.windows.index(self.curview)
                n = (n + delta) % len(self.windows)
                return self.windows[n]
                
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
        cleared (explicitly or by reading new keys) or a new message is set.
        """
        self._message = message
        self._message_upd = True
        self.refresh()
        
    @command
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
                w.refresh()

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
    def delwindow(self, winnum=True, window=None):
        """
        Delete the given window.
        """
        if window is None:
            window = self._pickwindow(winnum)

        window.delete()
        

    @command
    @annotate(None)
    @annotate(UniArg)
    def onlywindow(self, winnum=True, window=None):
        """
        Delete all windows but the specified one (default current)
        """
        if window is None:
            window = self._pickwindow(winnum)

        window.only()


    @command
    @annotate(None)
    @annotate(UniArg)
    def splitwindow(self, focustop=True):
        """"
        Split the current window vertically into two windows viewing the
        same buffer. By default focus goes to the top window, with any
        argument other than True, the bottom is focused
        """

        ow = self.curview
        nw = ow.split()

        if focustop is True:
            self.focuswindow(ow)
        else:
            self.focuswindow(nw)


    @command
    @annotate(None)
    @annotate(UniArg)
    def nextwindow(self, n=True):
        """
        Activate the next winwow down, wrapping around, or
        to the numbered window if specified
        """
        self.focuswindow(self._pickwindow(n, delta=1))

                
    @command
    @annotate(None)
    @annotate(UniArg)
    def prevwindow(self, n=True):
        """
        Activate the next winwow up, wrapping around, or
        to the numbered window if specified
        """
        self.focuswindow(self._pickwindow(n, delta=-1))
