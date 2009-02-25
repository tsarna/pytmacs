from code import InteractiveConsole
import sys

class PyInteract(InteractiveConsole):
    def __init__(self):
        self.ps1 = getattr(sys, 'ps1', '>>> ')
        self.ps2 = getattr(sys, 'ps2', '... ')
        
        InteractiveConsole.__init__(self)

    def write(self, txt):
        sys.stderr.write(txt)

    def start(self):
        cprt = 'Type "help", "copyright", "credits" or "license" for more information.'
        self.write("Python %s on %s\n%s\n(TMACS)\n" %
                (sys.version, sys.platform, cprt))
        self.write(self.ps1)

    def input(self, txt):
        self.write(txt)
        self.write("\n")
        more = self.push(txt)
        if more:
            self.write(self.ps2)
        else:
            self.write(self.ps1)
        
    

i = PyInteract()
i.start()
i.input("1+1")
i.input("print __name__")
i.input("def f(x):")
i.input("    return x + 1")
i.input("")
i.input("f(2)")
i.input(")")

