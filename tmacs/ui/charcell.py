from tmacs.ui.base import *
import __tmacs__


class TestUI(UIBase):
    from tmacs.edit.view import View as window_class
    
    def __init__(self):
        self.windows = []
        self.ungotten = []


    def add_window(self, buffer):
        w = self.window_class(buffer)
        if not self.windows:
            __tmacs__.curview = w
        self.windows.append(w)

            
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
        print msg


    @command
    def beep(self):
        sys.stderr.write('\a')


    @command
    def forceredraw(self):
        for w in self.windows:
            b = w.buf
            print "BUFFER %s:" % b.name
            print b[:]


    def askyesno(self, prompt):
        x = None
        while True:
            x = raw_input(prompt + '[y/n]? ')
            if x in 'yY':
                return True
            elif x in 'nN':
                return False


    def askstring(self, prompt):
        return raw_input(prompt)
        

def test():
    import tmacs.ui.defmaps
    
    __tmacs__.ui = ui = TestUI()
    
    ui.cmdloop(__tmacs__)
