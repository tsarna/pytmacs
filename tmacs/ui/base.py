# $Id: base.py,v 1.21 2007-10-27 03:56:24 tsarna Exp $

from tmacs.edit.buffer import find_buffer
from tmacs.app.commands import *
from tmacs.ui.keys import keysym, repr_keysym, keymap
import sys, traceback, __tmacs__


def set_exception(exctuple):
    """
    Record the text of an exception (represented as a sys.exc_info()-type
    3-tuple) in a buffer so the user can inspect it.
    """
    
    b = find_buffer('__error__')
    b.read_only = False
    del b[:]
    b.append(u''.join(traceback.format_exception(*exctuple)))
    b.changed = False
    #print u''.join(traceback.format_exception(*exctuple))
    
    return b
    

# UI Base Class

class UIBase(object):
    """
    Base class for all user interfaces
    """
    
    def __init__(self):
        super(UIBase, self).__init__()
        self.default_sit = 3

        self.ungotten = []
        self.playback = []

        self.cmd_cache = {}
        
        # the stack of minibuffers
        self.minibufs = []
        
    def run(self):
        """
        Run the user interface. This is the top level loop of the
        application thread.
        """

        state = __tmacs__
        state._quit = False
        
        self.layout_windows()
        
        while not state._quit:
            try:
                self.cmdloop(state)
            except BaseException, ex:
                msg = ex.message
                if not msg:
                    msg = ex.__class__.__name__
                self.beep()
                self.write_message('[%s]' % msg)
                set_exception(sys.exc_info())
                self.refresh()
        
        self.cleanup()
        self.reactor.stop()

    def cleanup(self):
        """
        Do any cleanup necessary to shut down the UI (close windows, etc).
        To be overridden by subclasses.
        """
        pass
                
    def cmdloop(self, state):
        """
        Run a command loop.  Read key sequences, run the commands
        they're mapped to, and refresh the display. May be nested.
        (eg for minibuffers)
        """
        
        state._quit = False
        state.uniarg = state.lastwaskill = None
        state.nextuniarg = True
        state.thisiskill = False
    
        while not state._quit:
            state.keyseq, state.cmdname, state.evtval = self.readkeyseq(state)
            if state.cmdname is None:
                state.cmdname = "notbound"
            state.thiscmd = self.lookup_cmd(state, state.cmdname)
            if state.thiscmd is None:
                state.thiscmd = self.lookup_cmd(state, "unknowncommand")
            state.uniarg, state.nextuniarg = state.nextuniarg, True
            state.lastwaskill, state.thisiskill = state.thisiskill, False
            self.executecmd(state.thiscmd, state)
            self.refresh()

    # Macro support
    
    def buffer_for_macro(self, n=True):
        """Return the buffer for a numbered (or not) macro"""
        if n is True:
            name = "__macro__"
        else:
            name = "__macro%d__" % n
       
        b = find_buffer(name)
        b.read_only = False
        
        return b
        
    def record(self, event):
        """Record an event in the active recording macro"""
        
    def pushplayback(self, o):
        """Push a 'file'-like for playback"""
        self.playback.append(o)
        
    # Events

    def getevent(self):
        """Get next event, blocking if necessary"""
        if self.ungotten:
            return self.ungotten.pop()  

        while self.playback:
            ev = self.playback[-1].read(1)
            if ev == u"":
                self.playback.pop()
            else:
                return (ev, None)

        ev = self._getevent()

        return ev

    def ungetevent(self, ev):
        """Cause the given event to be returned by the next getevent()"""
        self.ungotten.append(ev)
                        
    def waitevent(self, secs):
        """Wait up to 'secs' seconds for an event to be available"""
        
        if self.evpending():
            return True
        
        ev = self._waitevent(self, secs)
        if ev is None:
            return False
        else:
            self.ungetevent(ev)
            return True

    def evpending(self):
        """True if an event is waiting to be gotten"""
        if self.ungotten:
            return True

        while self.playback:
            ev = self.playback[-1].read(1)
            if ev == u"":
                self.playback.pop()
            else:
                self.ungetevent((ev, None))
                return True
            
        return self._evpending()

    def readkeyseq(self, state, prompt=""):
        """
        Read a key sequence. The optional prompt is used by the
        ReadKeySeq annotation.
        
        Returns: the key sequence, the command it maps to, and the value
        associated with the last event in the sequence.
        """        
        if prompt:
            self.set_message(prompt)
            disp = True
        else:
            disp = False

        seq, evtval = self.getevent()
        if not prompt:
            self.clear_message()

        cmdname = self.curview.keymap.get(seq)

        while type(cmdname) is keymap:
            if not self.minibufs:
                if prompt:
                    self.set_message("%s %s" % (prompt, repr_keysym(seq)))
                else:
                    self.set_message(repr_keysym(seq))
                disp = True
            ev, evtval = self.getevent()
            seq += ev
            cmdname = self.curview.keymap.get(seq)
        
        if disp:
            self.clear_message()
    
        return seq, cmdname, evtval

    def promptforevent(self, prompt=""):
        """
        Read one event. The optional prompt is used by the
        SeqPromptedEvent annotation.
        
        Returns: the event
        """
           
        if prompt:
            self.set_message(prompt)

        e = self.getevent()

        if prompt:
            self.clear_message()
        
        return e

    # Command lookup
    
    def lookup_cmd(self, state, cmdname):
        """
        Look up a command by name. Delegates to the current view,
        then we look in ourself for UI-wide commands. Returns None
        on command not found.
        """
        # check the view
        c = self.curview.lookup_cmd(cmdname)

        if c is None:
            # Then check us
            c = getattr(self, cmdname, None)

            if c is None:
                # check .tmacsrc                
                c = getattr(__tmacs__, cmdname, None)

                if c is None:
                    # check cache
                    c = self.cmd_cache.get(cmdname)

                    if c is None:
                        if cmdname[0] in '[<':
                            c = self.lookup_cmd(state, "inputkeysym")
                        elif '-' in cmdname:
                            c = self.lookup_addon(cmdname)

        if c and not hasattr(c, '__tmacs_cmd__'):
            # not really a command
            return None

        return c

    
    def lookup_addon(self, cmdname):
        """Lookup a command in an addon module"""
        parts = cmdname.split('-')
        n = len(parts)

        # ensure alphanumeric parts
        if len([True for p in parts if p.isalnum()]) == n:
            if n == 2:
                s = "from tmacs.addons.%s import %s as func" % tuple(parts)
                d = {}
                try:
                    exec s in d
                except ImportError:
                    return None
            
                c = d.get('func')
                if c is not None:
                    self.cmd_cache[cmdname] = c
                    return c


    ### Commands
    
    @command
    @annotate(None)
    @annotate(ReadCmd(': '))
    @annotate(CmdLoopState)
    def executecmd(self, cmd, state=__tmacs__):
        """Execute a named command."""
        cmd.__tmacs_cmd__(cmd, state)


    @command
    @annotate(None)
    @annotate(CmdLoopState)
    def inputkeysym(self, state=__tmacs__):
        """Simulate unicode input, for bindings to keysyms."""
        c = state.cmdname
        ev = (keysym(c), None)
        self.ungetevent(ev)

    @command
    @annotate(None)
    @annotate(CmdLoopState)
    def uniarg(self, state=__tmacs__):
        """
        Input the universal argument for the following command.
        """
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
        """
        This command is run when a key sequence maps to an unknown command.
        """
        return "[Unknown command %s]" % state.cmdname

        
    @command
    @annotate(None)
    @annotate(CmdLoopState)
    @returns(ErrorToShow)
    def illegalsequence(self, state=__tmacs__):
        """
        This command is run when an illegal or undecodable key
        sequence is read.
        """
        return "[Illegal input sequence '%s']" % repr_keysym(state.evtval)

        
    @command
    @annotate(None)
    @annotate(CmdLoopState)
    @returns(ErrorToShow)
    def notbound(self, state=__tmacs__):
        """
        This command is run when a key sequence that is not bound is input.
        """
        return "[Key %s not bound]" % repr_keysym(state.keyseq)
        
    @command
    @annotate(None)
    @annotate(CmdLoopState)
    @annotate(AskAbandonChanged("Modified buffers exist. Leave anyway"))
    def quit(self, state=__tmacs__, sure=True):
        """Quit the application."""
        if sure:
            state._quit = True
        
    @command
    def quickexit(self, state=__tmacs__):
        """Save changed buffers and exit."""
        
        changed = [(n, b) for n, b in __tmacs__.buffers.items() if b.changed]
        noname = [n for n, b in changed if not hasattr(b, 'filename')]
        if noname:
            raise ValueError, "Buffer %s is changed but has no filename" % noname[0]

        for n, b in changed:
            b.save()
        
        state._quit = True
                                
    @command
    def abort(self):
        """Abort the current operation."""
        raise KeyboardInterrupt

    @command
    def nop(self):
        """This command does nothing."""
        pass

    ### binding commands
    
    @command
    @annotate(None)
    @annotate(ReadKeySeq(': describekey'))
    @annotate(CmdLoopState)
    @returns(MessageToShow)
    def describekey(self, keyseq, state=__tmacs__):
        """Describe the binding for a key sequence."""
        cmdname = self.curview.keymap.get(keyseq)
        if cmdname is None:
            return '[Key %s not bound]' % repr_keysym(keyseq)
        else:
            return '%s %s' % (repr_keysym(keyseq), cmdname)
