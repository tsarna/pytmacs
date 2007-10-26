from tmacs.app.rcfile import runRCFile
from tmacs.app.reactor import UntwistedReactor as Reactor
from tmacs.edit.buffer import find_buffer, load_file, Buffer
from tmacs.ui.charcell import set_exception
from tmacs.termioscap import TCUI
import os, __tmacs__



def main(argv, environ):
    #from tmacs.termioscap import start
    __tmacs__.reactor = reactor = Reactor()

    __tmacs__.ui = ui = TCUI(reactor)
        
    c = environ.get('TMACS_FILE_ENCODING', 'utf8')
    __tmacs__.default_encoding = c

    exc = runRCFile(__tmacs__)
    if exc is not None:
        ui.add_window(set_exception(exc))

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
            ui.add_window(b)
            line = encoding = None

    # if there are no buffers, create one
    if not __tmacs__.buffers:
        ui.add_window(Buffer('__scratch__'))
            
    for mod in ('tmacs.ui.defmaps', 'tmacs.edit.buffer', 'tmacs.ui.keys'):
        exec "import %s" % mod in __tmacs__.__dict__
        
    from threading import Thread
    __tmacs__.uithread = uithread = Thread(target=ui.run)

    uithread.start()

    reactor.run()
    

