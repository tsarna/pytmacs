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

                
        
class CharCellUI(UIBase):
    def askyesno(self, prompt, default=None):
        state = CCAskYesNo(default)
        self.write_message(prompt)
        try:
            state.curview = state
            self.cmdloop(state)
            return state.answer            
        finally:
            # remove circular ref
            del state.curview



    

class TestUI(CharCellUI):
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
