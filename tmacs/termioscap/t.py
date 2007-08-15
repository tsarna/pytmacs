import os, ctypes, ctypes.util, tckeymap

TERM = os.environ['TERM']

buf = ctypes.create_string_buffer(1000)
for libname in ('termcap', 'curses'):
    lib = ctypes.CDLL(ctypes.util.find_library(libname))

tgetent = lib.tgetent

print tgetent(buf, TERM)
print buf

tcb = ctypes.create_string_buffer(32)

tgetstr = lib.tgetstr
tgetstr.restype = ctypes.c_char_p

for tc, key in tckeymap.tckeys:
    ccp = tgetstr(tc, ctypes.byref(tcb))
    if ccp:
        print tc, `ccp`
