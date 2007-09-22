from keysym_tab import *
from unicodedata import lookup
import __tmacs__

anynormal = symtochar["anynormal"]

_marker = object()


def keysym(k):
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


def repr_keysym(u):
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



class keymap(dict):
    def __init__(self, name, *args):
        dict.__init__(self, *args)
        self.name = name

    def bind(self, sym, val):
        self[keysym(sym)] = val

    def lookup(self, sym, default=_marker):
        v = self.get(keysym(sym), default)
        if v is _marker:
            raise KeyError, sym
        return v
        
    def __setitem__(self, seq, val):
        if len(seq) == 1:
            dict.__setitem__(self, seq, val)
        else:
            k = seq[0]
            nextmap = dict.get(self, k)
            if type(nextmap) is not self.__class__:
                raise KeyError, repr_keysym(k) + u' is not a prefix in ' + self.name
            nextmap[seq[1:]] = val

    def get(self, seq, default=None):
        if len(seq) == 1:
            v = dict.get(self, seq, default)
            if v is not default:
                return v
            o = ord(seq)
            if o >= 32 and o < 0xEC00:
                return dict.get(self, anynormal, default)
        else:
            k = seq[0]
            nextmap = dict.get(self, k)
            if type(nextmap) is self.__class__:
                return nextmap.get(seq[1:], default)
                
            return default

    def walk(self):
        for k, v in dict.items(self):
            if type(v) is self.__class__:
                yield k, v
                for k2, v2 in v.walk():
                    yield (k + k2, v2)
            else:
                yield (k, v)
            
    def items(self):
        return list(self.walk)

    def __repr__(self):
        l = []
        for k, v in self.walk():
            k = repr_keysym(k)
            if type(v) is self.__class__:
                l.append((k, u'--> ' + v.name))
            else:
                l.append((k, unicode(v)))
                
        l.sort()
        l = [k + u'\t' + v for k, v in l] 
        return u'\n'.join(l)
