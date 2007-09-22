from tmacs.edit.buffer import find_buffer
from tmacs.app.commands import *
from tmacs.ui.keys import keysym, repr_keysym, keymap
import sys, traceback, __tmacs__


def set_exception(exctuple):
    b = find_buffer('__errors__')
    del b[:]
    b.append(u''.join(traceback.format_exception(*exctuple)))
    
    return b
    

# UI Base Class

class UIBase(object):
    def __init__(self):
        pass
        
    def run(self):
        for b in __tmacs__.buffers.values():
            self.add_window(b)
            
        return self.cmdloop(__tmacs__)
        
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
            self.executecmd(state.thiscmd, state)
            # XXX redraw if no input pending
        
    def readkeyseq(self):
        seq, evtval = self.getevent()
        cmdname = self.lookup_keyseq(seq)

        while type(cmdname) is keymap:
            self.write_message(repr_keysym(seq))
            ev, evtval = self.getevent()
            seq += ev
            cmdname = self.lookup_keyseq(seq)
    
        return seq, cmdname, evtval

    def lookup_keyseq(self, seq):
        return __tmacs__.globalmap.get(seq)

    def lookup_cmd(self, cmdname):
        c = getattr(__tmacs__.curview, cmdname, None)
        if c and not hasattr(c, '__tmacs_cmd__'):
            c = None

        if c is None:
            c = getattr(self, cmdname, None)
            if not hasattr(c, '__tmacs_cmd__'):
                c = None

        return c

    ### Commands
    
    @command
    @annotate(None)
    @annotate(ReadCmd(': '))
    @annotate(CmdLoopState)
    def executecmd(self, cmd, state=__tmacs__):
        try:
            cmd.__tmacs_cmd__(cmd, state)
        except BaseException, ex:
            msg = ex.message
            if not msg:
                msg = ex.__class__.__name__
            self.beep()
            self.write_message('[%s]' % msg)
            set_exception(sys.exc_info())


    @command
    @annotate(None)
    @annotate(CmdLoopState)
    def uniarg(self, state=__tmacs__):
        k = state.keyseq[-1]
        first = False
        if k.isdigit():
            n = int(k)
        elif k == '-':
            n = False
        else:
            n = state.uniarg * 4
            first = True
        
        if n is False:
            self.write_message("Arg: -")
        else:
            self.write_message("Arg: %d" % n)
        ev, arg = self.getevent()

        if first:
            if ev == '-':
                self.write_message("Arg: -")
                n = False
                ev, arg = self.getevent()
            elif ev.isdigit():
                n = int(ev)
                self.write_message("Arg: %d" % n)
                ev, arg = self.getevent()

        while ev.isdigit():
            d = int(ev)
            if n is False:
                n = -int(ev)
            elif n < 0:
                n = n * 10 - d
            else:
                n = n * 10 + d
            self.write_message("Arg: %d" % n)
            ev, arg = self.getevent()
        
        self.ungetevent((ev, arg))

        state.nextuniarg = n



    @command
    @annotate(None)
    @annotate(CmdLoopState)
    @returns(ErrorToShow)
    def unknowncommand(self, state=__tmacs__):
        return "[Unknown command %s]" % state.cmdname

        
    @command
    @annotate(None)
    @annotate(CmdLoopState)
    @returns(ErrorToShow)
    def illegalsequence(self, state=__tmacs__):
        return "[Illegal input sequence '%s']" % repr_keysym(state.evtval)

        
    @command
    @annotate(None)
    @annotate(CmdLoopState)
    @returns(ErrorToShow)
    def notbound(self, state=__tmacs__):
        return "[Key %s not bound]" % repr_keysym(state.keyseq)
        
    @command
    @annotate(None)
    @annotate(CmdLoopState)
    @annotate(AskAbandonChanged("Modified buffers exist. Leave anyway"))
    def quit(self, state=__tmacs__, sure=True):
        if sure:
            state.quit = True
        
    @command
    def abort(self):
        raise KeyboardInterrupt

    @command
    def nop(self):
        pass

    ### binding commands
    
    @command
    @annotate(None)
    @annotate(ReadKeySeq(': describekey'))
    @returns(MessageToShow)
    def describekey(self, keyseq):
        cmdname = self.lookup_keyseq(keyseq)
        if cmdname is None:
            return '[Key not bound]'
        else:
            return '%s %s' % (repr_keysym(keyseq), cmdname)


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
