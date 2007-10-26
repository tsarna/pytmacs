#!/usr/bin/env python

import sys, os, imp

sys.modules['__tmacs__'] = imp.new_module('__tmacs__')
import __tmacs__

__tmacs__.__appname__ = "TMACS"
__tmacs__.__version__ = "2.0dev4"

from tmacs.ui.keys import *

__tmacs__.basemap = basemap = keymap('basemap')
__tmacs__.accentmap = accentmap = keymap('accentmap')
__tmacs__.escmap = escmap = keymap('escmap', nocase=True, mapping={
    u"'" : accentmap
})
__tmacs__.ctlxmap = ctlxmap = keymap('ctlxmap', nocase=True)
__tmacs__.globalmap = globalmap = keymap('globalmap', inherit=[basemap],
mapping={
    keysym('<Esc>') : escmap, keysym('<^X>') : ctlxmap
})


if __name__ == '__main__':
    from tmacs.app.main import main
    main(sys.argv, os.environ)
