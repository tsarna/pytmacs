import os

class TestUI(object):
    def __init__(self):
        pass

    def setOutput(self, o):
        self.output = o

    def illegalSequence(self, s):
        self.output.write('illegal: %s\r\n' % `o`)
        
    def windowSize(self, x, y):
        self.output.write('size: %dx%d\r\n' % (x, y))
        
    def send(self, s):
        if 'q' in s:
            self.output.cleanup()
       
        self.output.write(`s`+ '\r\n')
        
       

def main(argv, environ):
    t = TestUI()
    
    from tmacs.termioscap import start
    reactor = start(t)
    
    reactor.run()
