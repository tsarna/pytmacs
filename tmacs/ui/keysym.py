from keysym_tab import *
from unicodedata import lookup

def ParseKeyDef(k):
    r = []

    while k:
        if k[0] == u'<':
            try:
                m, k = k.split(u'>', 1)
            except:
                raise ValueError, 'Unterminated <> key symbol'
            try:
                r.append(symtochar[m[1:].lower()])
            except:
                raise ValueError, 'Unknown key symbol %s>' % m
        elif k[0] == u'[':
            try:
                m, k = k.split(u']', 1)
            except:
                raise ValueError, 'Unterminated [] key symbol'
            h = m.upper()
            try:
                r.append(lookup(h[1:]))
            except:
                if h.startswith(u'[0X') or h.startswith(u'[U+'):
                    h = h[3:]
                elif h.startswith(u'[U'):
                    h = h[2:]
                else:
                    h = h[1:]
                try:
                    r.append(unichr(int(h, 16)))
                except:
                    raise ValueError, 'Illegal Unicode character %s]' % m
        else:
            r.append(k[0])
            k = k[1:]

    return u''.join(r)


def ReprKeyDef(u):
    r = []
    
    for b in u:
        k = chartosym.get(b)
        if k:
            r.extend([u'<', k, u'>'])
        elif ord(b) > 31 and ord(b) < 127:
            r.append(b)
        else:
            r.append('[%04X]' % ord(b))

    return u''.join(r)
