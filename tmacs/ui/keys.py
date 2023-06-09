from keysym_tab import *
from unicodedata import lookup
import __tmacs__

anynormal = symtochar["anynormal"]

_marker = object()


def keysym(k):
    """
    Parse a string containing a sequence of human readable
    key symbols and return a unicode string containing the characters
    representing those keys.
    """
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
    """
    Convert a unicode string to a new string containing the human
    readable representation of the keys represented by those characters.
    """
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
    """
    A keymap represents a set of bindings from keys to command strings.
    Keys may be bound to other maps, allowing sequences of keys to
    be bound to commands. Keymaps may also be set to inherit from a
    list of other keymaps.
    """

    def __init__(self, name, inherit=None, mapping={}, nocase=False):
        dict.__init__(self, mapping)
        self.name = name
        if inherit is None:
            inherit = []
        self.inherit = inherit
        self.nocase = nocase

    def bind(self, sym, val):
        """Bind a keysym to a value (command or keymap)"""
        
        self[keysym(sym)] = val

    def lookup(self, sym, default=_marker):
        """Look up a keysym"""
        
        v = self.get(keysym(sym), default)
        if v is _marker:
            raise KeyError, sym
        return v
        
    def __setitem__(self, seq, val):
        """Set a mapping by key codes"""

        if self.nocase:
            seq = seq.upper()
        if len(seq) == 1:
            dict.__setitem__(self, seq, val)
        else:
            k = seq[0]
            nextmap = dict.get(self, k)
            if type(nextmap) is not self.__class__:
                raise KeyError, repr_keysym(k) + u' is not a prefix in ' + self.name
            nextmap[seq[1:]] = val

    def get(self, seq, default=None):
        """Look up a mapping by codes"""
        
        if self.nocase:
            seq = seq.upper()
        v = _marker
        if len(seq) == 1:
            v = dict.get(self, seq, _marker)
            if v is not _marker:
                return v
            o = ord(seq)
            if o >= 32 and o < 0xEC00:
                v = dict.get(self, anynormal, _marker)
        else:
            k = seq[0]
            nextmap = dict.get(self, k, _marker)
            if type(nextmap) is self.__class__:
                v = nextmap.get(seq[1:], _marker)

        if v is _marker:
            for i in self.inherit:
                v = i.get(seq, _marker)
                if v is not _marker:
                    break
                
        if v is _marker:
            v = default
         
        return v


    def walk(self):
        """
        Iterator over a keymap and its submaps, producing a flattened
        list of bindings.
        """
        
        for k, v in dict.items(self):
            if type(v) is self.__class__:
                yield k, v
                for k2, v2 in v.walk():
                    yield (k + k2, v2)
            else:
                yield (k, v)
            
    def items(self):
        """
        Return a flattened list of bindings in ourself and our submaps.
        """
        return list(self.walk)


    def __repr__(self):
        """Textual representation of this keymap (and submaps)."""

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


    def copy(self):
        """Duplicate a keymap. This is a shallow copy opertation."""
        
        return keymap(self.name, inherit=self.inherit[:], mapping=self, nocase=self.nocase)
