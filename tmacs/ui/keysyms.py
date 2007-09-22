from keysym_tab import *
from unicodedata import lookup

class keysym(unicode):
    def __new__(klass, k=None, chars=u''):
        if k is not None:
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

            chars = u''.join(r)

        return unicode.__new__(klass, chars)


    def __repr__(self):
        r = []
    
        for b in self:
            k = chartosym.get(b)
            if k:
                r.extend([u'<', k, u'>'])
            elif ord(b) > 31 and ord(b) < 127:
                r.append(b)
            else:
                r.append('[%04X]' % ord(b))

        return u''.join(r)
