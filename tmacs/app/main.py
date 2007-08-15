from tmacs.app.rcfile import runRCFile
from tmacs.edit.buffer import findBuffer, loadFile, Buffer
import os, traceback, __tmacs__


class TestUI(object):
    x = 0
    y = 0
    
    def __init__(self):
        pass

    def setOutput(self, o):
        self.output = o

    def illegalSequence(self, s):
        self.output.beep()
        self.output.write('illegal: %s' % `s`)
        self.output.cleanup()
        
    def windowSize(self, x, y):
        self.x, self.y = x, y
        self.output.beep()
        self.output.moveto(0, self.y - 1)
        self.output.write('size: %dx%d' % (x, y))
        self.output.eeol()
                
    def send(self, s):
        self.output.moveto(0, self.y - 1)
        self.output.write(`s`)
        self.output.eeol()

        if 'q' in s:
            self.output.cleanup()



def setException(exctuple):
    b = findBuffer('__errors__')
    del b[:]
    b.append(u''.join(traceback.format_exception(*exctuple)))

    return b
    
       

def main(argv, environ):
    __tmacs__.ui = t = TestUI()
        
    from tmacs.termioscap import start
    __tmacs__.reactor = reactor = start(t)

    c = environ.get('TMACS_FILE_CODING', 'utf8')
    __tmacs__.default_coding = c

    exc = runRCFile(__tmacs__)
    if exc is not None:
        setException(exc)

    coding = None
    line = None
    
    args = argv[1:]
    
    while args:
        arg = args.pop(0)

        if arg == '-e':
            if args:
                __tmacs__.default_coding = args.pop(0)
            else:
                pass # XXX
        elif arg.startswith('-e'):
            __tmacs__.default_coding = arg[2:]
        elif arg == '-E':
            if args:
                coding = args.pop(0)
            else:
                pass # XXX
        elif arg.startswith('-E'):
            coding = arg[2:]
        elif arg.startswith('+'):
            line = int(arg[1:])
        else:
            b = loadFile(arg, coding=coding)
            if line:
                b.start_line = line
            line = coding = None

    if not __tmacs__.buffers:
        Buffer('__scratch__')
            
    reactor.run()
