import os
from re import compile

# TODO: sniff from regex list
# TODO: local variables
# TODO: seval

def sniffFromFilename(fn):
    v = {}

    try:
        from __tmacs__ import sniff_extensions
    except ImportError:
        return v
    
    mode = []
    coding = None
    
    for rule in sniff_extensions:
        s = rule.get('pattern', None)
        if s is None:
            continue
        
        f = rule.get('flags', 0)
        rx = compile(s, f)
        m = rx.search(fn)
        if m:
            coding = rule.get('coding', coding)
            smode = rule.get('mode', None)
            cont = rule.get('continue', 0)
            
            if smode is not None:
                if type(smode) is not list:
                    smode = [smode]
                mode.extend(smode)

            v.update(rule.get('also', {}))

            if cont:
                fn = fn[:m.start()] + fn[m.end():]
            else:
                break
    
    if mode:
        v['mode'] = mode
    if coding:
        v['coding'] = coding

    if v:
        v['sniff_method'] = 'filename'

    return v        
        

stars = compile(r'-\*-\s*(.*)\s*-\*-')
simple = compile(r'coding[:=]\s*([-\w.]+)')

def parseStarsString(s):
    if ':' not in s:
        return [('mode', s.strip())]
    v = [x.split(':', 1) for x in s.split(';') if x.strip()]
    v = [tuple([y.strip() for y in x]) for x in v if len(x) == 2]
    return v

    
def sniffFromStars(l1, l2):
    v = None
    m = stars.search(l1)
    if m:
        v = parseStarsString(m.group(1))
    else:
        m = stars.search(l2)
        if m:
            v = parseStarsString(m.group(1))

    rv = {}
    if v:
        rv['sniff_method'] = 'stars'
        for key, val in v:
            if key == 'mode':
                rv.setdefault(key, []).append(val)
            else:
                rv[key] = val
            
    return rv, ''.join([l1, l2])


def sniffCodingFromTop(l1, l2, v):
    m = simple.search(l1)
    if m is None:
        m = simple.search(l2)            

    if m:
        v['coding'] = m.group(1)
        return True
    
    return False


def sniffFromShell(shell):
    try:
        from __tmacs__ import sniff_shells
    except ImportError:
        return {}
    
    shell = shell[2:].strip()
    v = sniff_shells.get(shell, None)
    if v:
        v['sniff_method'] = 'shell'
    return v


def preSniff(filename, l1, l2):
    v, top = sniffFromStars(l1, l2)
    if not v and top.startswith('#!'):
        v = sniffFromShell(l1)
#    if not v:
#        v = sniffByRegex(top)
    if not v:
        v = sniffFromFilename(filename)

    if not v.has_key('coding'):
        if not sniffCodingFromTop(l1, l2, v):
            if top.find('\xef\xbb\xbf') >= 0:
                v['coding'] = 'utf8'

    c = v.get('coding')
    if c is None:
        try:
            from __tmacs__ import default_coding
            c = default_coding
        except ImportError:
            pass
    
    if c is None:
        c = 'utf8'

    top = top.decode(v.setdefault('coding', c))
                    
    return v, top



def postSniff(buf, v, bottom):
    pass
