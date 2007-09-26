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
        n = super(CharCellWindow, self).copy()
        n.left, n.top, n.width, n.height = self.left, self.top, self.width, self.height
        n._active = False
        
        return n
        
    def position(self, left, top, width, height):
        self.left, self.top, self.width, self.height = left, top, width, height
        self._status_upd = True
        # force redraw of all        

    def focus(self):
        self._active = True
        self._status_upd = True
        
    def blur(self):
        self._active = False
        self._status_upd = True
        
    def refresh(self, ui):
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
        

class CharCellUI(UIBase):
    window_class = CharCellWindow
    
    def __init__(self):
        super(CharCellUI, self).__init__()
        self._message = ""
        self._message_upd = False
        self.curview = None # XXX state's curview??
    
    def add_window(self, buffer):
        self.windows.append(self.window_class(buffer))
            
    def layout_windows(self):
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
        if self.curview is not None:
            self.curview.blur()
        self.curview = window
        window.focus() 
        
    def askyesno(self, prompt, default=None):
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
        self._message = message
        self._message_upd = True
        self.refresh()
        
    def clear_message(self):
        if self._message:
            self._message = ""
            self._message_upd = True
            self.refresh()
        
    def write_message(self, message):
        self._message = message
        self._message_upd = True
        if self.minibufs:
            self.sitfor(3)
            self.clear_message()
        else:
            self.refresh()
        
    def refresh(self, force=False):
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
        self.refresh()
        self.waitevent(secs)


    @command
    @annotate(None)
    @annotate(UniArg)
    def splitwindow(self, select=True):
        w = self.curview
        if w.height < 4:
            raise ValueError, "Window too small to split"
        nw = w.copy()
        nw.height //= 2
        w.height -= nw.height
        nw.top += w.height
        
        wl = self.windows
        wl.insert(wl.index(w) + 1, nw)

        if select == 2:
            self.focuswindow(nw)
        else:
            self.focuswindow(w)


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
