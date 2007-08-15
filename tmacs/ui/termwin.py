"""UI with multiple emacs-style windows on a Terminal"""

class Window(object):
    def __init__(self):
        self.active = False

    def focus(self, hasFocus=True):
        self.active = hasFocus
    
    def resize(self, top, height):
        self.top, self.height = top, height
        
    def redraw(self):
        pass

    def delete(self):
        pass        
    
class TermWinUI(object):
    x = 0
    y = 0
    
    def __init__(self):
        self.windows = []
        self.curwin = None

    def focusWindow(self, w):
        if self.curwin:
            self.curwin.focus(False)

        self.curwin = w
        w.focus(True)

    def _getWindow(self, number=None, w=None):
        if number is not None:
            if number >= 1 and number <= len(self.windows):
                w = self.windows[number-1]
            else:
                raise IndexError, "Window number out of range (%d-%d)" % (1, len(self.windows))
        elif w is None:
            w = self.curwin

        return w, w is self.curwin

        
    def deleteWindow(self, number=None, w=None):
        """Delete the given window"""
        
        w, iscur = self._getWindow(number, w)

        if len(self.windows) < 2:
            raise ValueError, "Can't delete only window"

        i = self.windows.index(w)
        # give space to window above, unless top then give to next below
        if i == 0:
            other = self.windows[1]
            other.resize(0, other.height + w.height)
        else:
            other = self.windows[i - 1]
            other.resize(other.top, other.height + w.height)

        w.delete()
        self.windows.remove(w)

        if iscur:
            self.focusWindow(other)


    def splitWindow(self, number=None, w=None):
        """Split thegiven window in half"""
        
        w, iscur = self._getWindow(number, w)
        
        if w.height < 4:
            raise ValueError, "Window too small to split"

        # XXX

        
    def onlyWindow(self, number=None, w=None):
        """Make the given window full-screen, deleting other windows"""
        
        w, iscur = self._getWindow(number, w)
        
        for dw in self.windows:
            if dw is not w:
                dw.delete()
            
        self.windows = [w]

        w.resize(0, self.y - 1)
        
        if not iscur:
            self.focusWindow(w)


    def resizeWindow(self, newsize=None, winnum=None, w=None):
        """Resize window"""

        w, iscur = self._getWindow(number, w)
        
        nwin = len(self.windows)
        if nwin == 1:
            raise ValueError, "Can't resize only window"

        i = self.windows.index(w)
        if i == (nwin - 1):
            other = self.windows[i-1]
        else:
            other = self.windows[i+1]

        delta = newsize - w.height
        if other.height - delta < 2:
            raise ValueError, "Would make other window too small"

        if newsize < 2:                
            raise ValueError, "Would make window too small"

        # XXX do resize
        

    def growWindow(self, amount=1, winnum=None, w=None)
        "Make window larger"

        w, iscur = self._getWindow(number, w)
        
        # XXX
        # XXX choose victim
        # decide 


    def shrinkWindow(self, amount=1, winnum=None, w=None)
        "Make window smaller"
        # XXX

    
    def previousWindow(self): pass # XXX
    
    def nextWindow(self): pass # XXX

    def balanceWindows(self):
        """Balance sizes of windows"""
        
        pass # XXX

    # ---
        
    def setOutput(self, o):
        self.output = o

    def illegalSequence(self, s):
        self.output.beep()
        #self.output.write('illegal: %s' % `s`)
        
    def windowSize(self, x, y):
        self.x, self.y = x, y
        self.output.beep()
        self.output.moveto(0, self.y - 1)
        self.output.write('size: %dx%d' % (x, y))
        self.output.eeol()
                
    def send(self, s):
        self.output.moveto(0, self.y - 1)
        self.output.write(`s`)
        self.output.eeol()

        if 'q' in s:
            self.output.cleanup()
