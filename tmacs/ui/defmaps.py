import __tmacs__
from tmacs.ui.keys import *

__tmacs__.escmap = escmap = keymap('escmap', )
__tmacs__.ctlxmap = ctlxmap = keymap('ctlxmap')
__tmacs__.globalmap = globalmap = keymap('globalmap', {
    keysym('<Esc>') : escmap, keysym('<^X>') : ctlxmap
})

f = open(__file__.rsplit('.')[0]+'.txt')
for l in f:
    seq, cmdname = l.strip().split(None, 1)
    globalmap.bind(seq, cmdname)
