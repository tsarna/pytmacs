class TermWinUI(object):
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

    
    def balanceWindows(self):
        """Balance sizes of windows"""
        
        pass # XXX
