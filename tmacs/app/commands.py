from inspect import getargspec
import __tmacs__


### The following are for using decorators as function annotations. When
### we get to a python version with func_annotations, these can go away.

class annotate(object):
    """Prepend an annotation. Because decorators apply last to first, this
    results in annotations applying to arguments in the order listed.
    
    Eg:
        
    @annotate(int)
    @annotate(str)
    def foo(i, s, x):
        pass
        
    is equivalent to:
     
    def foo(i:int, s:str, x):
        pass
    """
    
    def __init__(self, anno):
        self.anno = anno

    def __call__(self, func):
        args = getattr(func, '__tmacs_annotations__', None)
        if args is None:
            args = func.__tmacs_annotations__ = []
        args.insert(0, self.anno)

        return func



class returns(object):
    """
    @returns(foo)
    def bar(...): ...
    
    is like:
        
    def bar(...) -> foo: ...
    """
        
    def __init__(self, rt):
        self.rt = rt

    def __call__(self, func):
        fa = getattr(func, 'func_annotations', None)
        if fa is None:
            fa = func.func_annotations = {}

        fa['return'] = self.rt

        return func
        
        

def func_annotations(func):
    """get function annotations dictionary"""
    
    fa = getattr(func, 'func_annotations', None)
    if fa is None:
        fa = func.func_annotations = {}

    args = getargnames(func)
    annos = getattr(func, '__tmacs_annotations__', [])
        
    while annos:
        anno = annos.pop(0)
        arg = args.pop(0)
        fa[arg] = anno

    return fa



### Annotation types
                
class UniArg(object):
    """This argument will receive the Universal Argument."""

    def gen_arg_code(self, arg, indents):
        return ([], '_state.uniarg')

UniArg = UniArg()



class KeySeq(object):
    """Argument will recieve the current key sequence."""
    
    def gen_arg_code(self, arg, indents):
        return ([], '_state.keyseq')

KeySeq = KeySeq()



class SeqPromptedEvent(object):
    """
    Argument will recieve the next event, prompt will
    be the current event sequence. Rather specialized for quotenext.
    """
    
    def gen_arg_code(self, arg, indents):
        return ([
            "%s%s = ui.promptforevent(tmacs.ui.keys.repr_keysym(_state.keyseq))" % (
                indents, arg
        )], arg)

SeqPromptedEvent = SeqPromptedEvent()



class CmdLoopState(object):
    """Argument will receieve the current event loop state object."""
    
    def gen_arg_code(self, arg, indents):
        return ([], "_state")
        
CmdLoopState = CmdLoopState()



### Region annotations

class SelectedText(object):
    """Argument will recieve a unicode object containing the selected text."""

    def gen_arg_code(self, arg, indents):
        return ([
            "%s%s = ui.curview.getregiontext()" % (indents, arg),
        ], arg)

SelectedText = SelectedText()


class ReplacementText(object):
    """The returned text will replace the selected text."""
    
    def gen_ret_code(self, arg, indents):
        return "%sui.curview.setregiontext(%s)" % (indents, arg)

ReplacementText = ReplacementText()


class SelectionStart(object):
    """Argument will recieve a marker for the start of the selection."""

    def gen_arg_code(self, arg, indents):
        return ([
            "%s%s = ui.curview.getregion()[0]" % (indents, arg),
        ], arg)

SelectionStart = SelectionStart()


class SelectionEnd(object):
    """Argument will recieve a marker for the end of the selection."""

    def gen_arg_code(self, arg, indents):
        return ([
            "%s%s = ui.curview.getregion()[1]" % (indents, arg),
        ], arg)

SelectionEnd = SelectionEnd()


### UI-using interactive annotations for arguments

class WithPrompt(object):
    """Base class for argument annotations that prompt."""
    
    def __init__(self, prompt):
        self.prompt = prompt
    

class PromptText(WithPrompt):
    """Argument will receive text input by the user."""
    
    def gen_arg_code(self, arg, indents):
        return ([
            "%s%s = ui.askstring(%s)" % (indents, arg, repr(self.prompt))
        ], arg)
    

class ReadKeySeq(WithPrompt):
    """User will be prompted to enter a key sequence for this argument."""
    
    def gen_arg_code(self, arg, indents):
        return ([
            "%s%s, %s_cmdname, %s_evtval = ui.readkeyseq(_state, %s)" % (
                indents, arg, arg, arg, repr(self.prompt)),
        ], arg)

        
class AskYesNo(WithPrompt):
    pass


class AskAbandonChanged(WithPrompt):
    """
    If unsaved changed buffers exist, prompt if the user wishes to continue.
    Arument will receive the boolean response. If no changed buffers,
    argument will receive True."
    """
    
    def gen_arg_code(self, arg, indents):
        return ([
            "%s%s = not tmacs.edit.buffer.changed_buffers_exist()" % (indents, arg),
            "%sif not %s:" % (indents, arg),
            "%s %s = ui.askyesno(%s)" % (indents, arg, repr(self.prompt))
        ], arg)


class AnyFileName(WithPrompt):
    """User will be prompted for a filename for the argument."""
    
    def gen_arg_code(self, arg, indents):
        return ([], "'XXX'")


class NewBufferName(WithPrompt):
    """User will be prompted for a buffer name for the argument.
    The name must not match an existing buffer."""

    def gen_arg_code(self, arg, indents):
        return ([], "'XXX'")


class UniArgOrInt(WithPrompt):
    """If a non-default universal argument has been specified, the argument
    will receive it, else the user will be prompted for a number for the
    argument."""
    
    def gen_arg_code(self, arg, indents):
        return ([
            "%s%s = _state.uniarg" % (indents, arg),
            "%sif %s is True:" % (indents, arg), 
            "%s %s = ui.askint(%s)" % (indents, arg, repr(self.prompt)), 
        ], arg)


class ReadCmd(WithPrompt):
    """The user will be prompted for the name of a command."""
    
    def gen_arg_code(self, arg, indents):
        return ([
            "%s%s_str = ui.askstring(%s)" % (indents, arg, repr(self.prompt)),
            "%s%s = ui.lookup_cmd(_state, %s_str)" % (indents, arg, arg),
            "%sif %s is None and %s_str:" % (indents, arg, arg), 
            """%s raise KeyError, "no such command '%%s'" %% %s_str""" % (indents, arg),
            "%selse:" % indents,
            "%s return" % indents
        ], arg)
        
        
        
### UI-using interactive annotations for returns

class MessageToShow(object):   
    """The returned text will be displayed as a message."""
    
    def gen_ret_code(self, arg, indents):
        return "%sui.write_message(%s)" % (indents, arg)
                
                    
MessageToShow = MessageToShow()
                    


class ErrorToShow(object):   
    """The returned text will be displayed as an error message."""

    def gen_ret_code(self, arg, indents):
        return "%sui.beep()\n%sui.write_message(%s)" % (indents, indents, arg)
                
                    
ErrorToShow = ErrorToShow()



class BufferToShow(object):
    """The returned object is a buffer to be displayed in a window,
    if the buffer is not already displayed."""
    
    def gen_ret_code(self, arg, indents):
        return "%sui.popupbuffer(%s)" % (indents, arg)

BufferToShow = BufferToShow()


### Support functions

def getargnames(func):
    sp = getargspec(func)
    args = sp[0]
    if sp[1] is not None:
        args.append(sp[1])
    if sp[2] is not None:
        args.append(sp[2])
    return args
    


def get_annotations(func):
    args = getargnames(func)
    fa = func_annotations(func)
    return ([(a, fa.get(a)) for a in args], fa.get('return'))



### Decorators   
    
def command(func):
    annos, retanno = get_annotations(func)
    name = "__tmacs_cmd_%s__" % func.func_name
    
    cl = ["def %s(_func, _state):" % name]
    al = []
    
    for arg, anno in annos:
        if anno is not None:
            code, argitem = anno.gen_arg_code(arg, ' ')
            cl.extend(code)
            al.append(argitem)

    cl.append('\n _r = _func(' + ', '.join(al) + ')')
    if retanno is not None:
        cl.append(retanno.gen_ret_code('_r', ' '))

    cl.append('')
    cl = '\n'.join(cl)

    exec cl in __tmacs__.__dict__
    
    cmdfunc = getattr(__tmacs__, name)
    delattr(__tmacs__, name)

    func.__tmacs_cmd__ = cmdfunc

    return func
    

@command
@annotate(UniArg)
def printn(n):
    print n
