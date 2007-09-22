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
    def gen_code(self, arg, indents):
        return ([], '_state.uniarg')

UniArg = UniArg()



class CmdLoopState(object):
    def gen_code(self, arg, indents):
        return ([], "_state")
        
CmdLoopState = CmdLoopState()



### UI-using interactive annotations

class MessageToShow(object):   
    def gen_code(self, arg, indents):
        return "%sui.message_write(%s)" % (indents, arg)
                
                    
MessageToShow = MessageToShow()
                    


class ErrorToShow(object):   
    def gen_code(self, arg, indents):
        return "%sui.beep()\n%sui.message_write(%s)" % (indents, indents, arg)
                
                    
ErrorToShow = ErrorToShow()
                    


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
            code, argitem = anno.gen_code(arg, ' ')
            cl.extend(code)
            al.append(argitem)

    cl.append('\n _r = _func(' + ', '.join(al) + ')')
    if retanno is not None:
        cl.append(retanno.gen_code('_r', ' '))

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
