from tmacs.app.main import set_exception
from tmacs.app.commands import *
from tmacs.ui.keysym import ParseKeySym, ReprKeySym
from tmacs.ui.keymap import keymap
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


class MessageToShow(object):
    def gen_code(self, arg, indents):
        return "%sui.message_write(%s)" % (indents, arg)


MessageToShow = MessageToShow()


# UI Base Class

class UIBase(object):
    def __init__(self):
        pass

    def cmdloop(self, state):
        state.quit = False
        state.uniarg = None
        state.nextuniarg = True
    
        while not state.quit:
            state.keyseq, state.cmdname = self.readkeyseq()
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
        seq = self.getevent()
        cmdname = self.lookup_keyseq(seq)

        while type(cmdname) is keymap:
            self.message_write(ReprKeySym(seq))
            ev = self.getevent()
            seq += ev
            cmdname = self.lookup_keyseq(seq)
    
        return seq, cmdname

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

        

class TestUI(UIBase):
    def getevent(self):
        ev = raw_input('KeySym: ')
        ev = ParseKeySym(ev)
        if len(ev) != 1:
            ev = ParseKeySym("<IllegalSequence>")
        return ev

    def message_write(self, msg):
        print msg

        
def test():
    import tmacs.ui.defmaps
    
    __tmacs__.ui = ui = TestUI()
    
    ui.cmdloop(__tmacs__)
