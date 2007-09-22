from tmacs.app.main import set_exception
from tmacs.app.commands import *
from tmacs.ui.keys import keysym, repr_keysym, keymap
import __tmacs__


### annotations

class AskYesNo(object):
    def __init__(self, prompt):
        self.prompt = prompt
    

class PrompFileName(object):
    def __init__(self, prompt):
        self.prompt = prompt


class UniArgOrInt(object):
    def __init__(self, prompt):
        self.prompt = prompt


# UI Base Class

class UIBase(object):
    def __init__(self):
        pass

    def cmdloop(self, state):
        state.quit = False
        state.uniarg = None
        state.nextuniarg = True
    
        while not state.quit:
            state.keyseq, state.cmdname, state.evtval = self.readkeyseq()
            if state.cmdname is None:
                state.cmdname = "notbound"
            state.thiscmd = self.lookup_cmd(state.cmdname)
            if state.thiscmd is None:
                state.thiscmd = self.lookup_cmd("unknowncommand")
            state.prevuniarg, state.uniarg, state.nextuniarg = \
                state.uniarg, state.nextuniarg, True
            self.exec_cmd(state.thiscmd, state)
            # XXX redraw if no input pending
        
    def readkeyseq(self):
        seq, evtval = self.getevent()
        cmdname = self.lookup_keyseq(seq)

        while type(cmdname) is keymap:
            self.message_write(repr_keysym(seq))
            ev = self.getevent()
            seq += ev
            cmdname = self.lookup_keyseq(seq)
    
        return seq, cmdname, evtval

    def lookup_keyseq(self, seq):
        return __tmacs__.globalmap.get(seq)

    def lookup_cmd(self, cmdname):
        c = getattr(self, cmdname, None)
        if hasattr(c, '__tmacs_cmd__'):
            return c

    def exec_cmd(self, cmd, state):
        cmd.__tmacs_cmd__(cmd, state)

    ### Commands
    
    @command
    @annotate(None)
    @annotate(CmdLoopState)
    @returns(MessageToShow)
    def uniarg(self, state):
        state.nextuniarg = state.uniarg * 4
        
        return "Arg: %d" % state.nextuniarg

    @command
    @annotate(None)
    @annotate(CmdLoopState)
    @returns(ErrorToShow)
    def unknowncommand(self, state):
        return "[Unknown command %s]" % state.cmdname
        
    @command
    @annotate(None)
    @annotate(CmdLoopState)
    @returns(ErrorToShow)
    def illegalsequence(self, state):
        return "[Illegal input sequence '%s']" % repr_keysym(state.evtval)
        
    @command
    @annotate(None)
    @annotate(CmdLoopState)
    @returns(ErrorToShow)
    def notbound(self, state):
        return "[Key %s not bound]" % repr_keysym(state.keyseq)
        


class TestUI(UIBase):
    def getevent(self):
        ri = raw_input('KeySym: ')
        ev = keysym(ri)
        if len(ev) != 1:
            return keysym("<IllegalSequence>"), ri
        return ev, None

    def message_write(self, msg):
        print msg

    def beep(self):
        sys.stderr.write('\a')
        

import sys

def test():
    import tmacs.ui.defmaps
    
    __tmacs__.ui = ui = TestUI()
    
    ui.cmdloop(__tmacs__)
