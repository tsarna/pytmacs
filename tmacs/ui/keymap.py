from keysym import ParseKeySym, ReprKeySym
import __tmacs__

_marker = object()

class keymap(dict):
    def __init__(self, name, *args):
        dict.__init__(self, *args)
        self.name = name

    def bind(self, sym, val):
        self[ParseKeySym(sym)] = val

    def lookup(self, sym, default=_marker):
        v = self.get(ParseKeySym(sym), default)
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
                raise KeyError, ReprKeySym(k) + u' is not a prefix in ' + self.name
            nextmap[seq[1:]] = val

    def get(self, seq, default=None):
        if len(seq) == 1:
            return dict.get(self, seq, default)
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
            k = ReprKeySym(k)
            if type(v) is self.__class__:
                l.append((k, u'--> ' + v.name))
            else:
                l.append((k, unicode(v)))
                
        l.sort()
        l = [k + u'\t' + v for k, v in l] 
        return u'\n'.join(l)
