from tmacs.edit.buffer import find_buffer
from tmacs.app.commands import *
from tmacs.ui.keys import keysym, repr_keysym, keymap
import sys, traceback, __tmacs__


def set_exception(exctuple):
    b = find_buffer('__errors__')
    del b[:]
    b.append(u''.join(traceback.format_exception(*exctuple)))
    #print u''.join(traceback.format_exception(*exctuple))
    
    return b
    

# UI Base Class

class UIBase(object):
    def __init__(self):
        super(UIBase, self).__init__()
        self.default_sit = 3
        
    def run(self):
        for b in __tmacs__.buffers.values():
            self.add_window(b)

        state = __tmacs__
        state.quit = False
        
        while not state.quit:
            try:
                self.cmdloop(state)
            except BaseException, ex:
                msg = ex.message
                if not msg:
                    msg = ex.__class__.__name__
                self.beep()
                self.set_message('[%s]' % msg)
                set_exception(sys.exc_info())
        
        self.cleanup()
        self.reactor.crash()

    def cleanup(self):
        pass
                
    def cmdloop(self, state):
        state.quit = False
        state.uniarg = None
        state.nextuniarg = True
    
        while not state.quit:
            state.keyseq, state.cmdname, state.evtval = self.readkeyseq(state)
            if state.cmdname is None:
                state.cmdname = "notbound"
            state.thiscmd = self.lookup_cmd(state, state.cmdname)
            if state.thiscmd is None:
                state.thiscmd = self.lookup_cmd(state, "unknowncommand")
            state.prevuniarg, state.uniarg, state.nextuniarg = \
                state.uniarg, state.nextuniarg, True
            self.executecmd(state.thiscmd, state)
            self.refresh()
        
    def readkeyseq(self, state):
        seq, evtval = self.getevent()
        self.clear_message()
        cmdname = state.curview.keymap.get(seq)

        while type(cmdname) is keymap:
            self.set_message(repr_keysym(seq))
            ev, evtval = self.getevent()
            seq += ev
            cmdname = state.curview.keymap.get(seq)
    
        return seq, cmdname, evtval

    def lookup_cmd(self, state, cmdname):
        c = state.curview.lookup_cmd(cmdname)
        if c is None:
            c = getattr(self, cmdname, None)

        if c and not hasattr(c, '__tmacs_cmd__'):
            # not really a command
            return None

        return c


    ### Commands
    
    @command
    @annotate(None)
    @annotate(ReadCmd(': '))
    @annotate(CmdLoopState)
    def executecmd(self, cmd, state=__tmacs__):
        cmd.__tmacs_cmd__(cmd, state)


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
            self.set_message("Arg: -")
        else:
            self.set_message("Arg: %d" % n)
        ev, arg = self.getevent()

        if first:
            if ev == '-':
                self.set_message("Arg: -")
                n = False
                ev, arg = self.getevent()
            elif ev.isdigit():
                n = int(ev)
                self.set_message("Arg: %d" % n)
                ev, arg = self.getevent()

        while ev.isdigit():
            d = int(ev)
            if n is False:
                n = -int(ev)
            elif n < 0:
                n = n * 10 - d
            else:
                n = n * 10 + d
            self.set_message("Arg: %d" % n)
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
    @annotate(CmdLoopState)
    @returns(MessageToShow)
    def describekey(self, keyseq, state=__tmacs__):
        cmdname = state.curview.keymap.get(keyseq)
        if cmdname is None:
            return '[Key not bound]'
        else:
            return '%s %s' % (repr_keysym(keyseq), cmdname)
