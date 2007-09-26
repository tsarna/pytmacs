class TermWinUI(object):
    def __init__(self):
        self.windows = []
        self.curwin = None

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
