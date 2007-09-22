from tmacs.app.rcfile import runRCFile
from tmacs.edit.buffer import find_buffer, load_file, Buffer
from tmacs.ui.ui import TestUI, set_exception
import os, __tmacs__



def main(argv, environ):
    __tmacs__.ui = ui = TestUI()
        
    #from tmacs.termioscap import start
    #__tmacs__.reactor = reactor = start(ui)

    c = environ.get('TMACS_FILE_CODING', 'utf8')
    __tmacs__.default_encoding = c

    exc = runRCFile(__tmacs__)
    if exc is not None:
        set_exception(exc)

    encoding = None
    line = None
    
    args = argv[1:]
    
    while args:
        arg = args.pop(0)

        if arg == '-e':
            if args:
                __tmacs__.default_encoding = args.pop(0)
            else:
                pass # XXX
        elif arg.startswith('-e'):
            __tmacs__.default_encoding = arg[2:]
        elif arg == '-E':
            if args:
                encoding = args.pop(0)
            else:
                pass # XXX
        elif arg.startswith('-E'):
            encoding = arg[2:]
        elif arg.startswith('+'):
            line = int(arg[1:])
        else:
            b = load_file(arg, encoding=encoding)
            if line:
                b.start_line = line
            line = encoding = None

    # if there are no buffers, create one
    if not __tmacs__.buffers:
        Buffer('__scratch__')
            
    #reactor.run()
    
    for mod in ('tmacs.ui.defmaps', 'tmacs.edit.buffer'):
        exec "import %s" % mod in __tmacs__.__dict__
        
    ui.run()
