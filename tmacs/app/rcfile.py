import sys, os, imp, marshal

csfx = '.pyc'
for sfx, mode, typ in imp.get_suffixes():
    if typ == imp.PY_COMPILED:
        csfx = sfx
        break

def runrc(path, rcmod, globals):
    rcfile = os.path.join(path, '.' + rcmod)
    crcfile = rcfile + csfx
    
    try: 
        rcmt = os.stat(rcfile).st_mtime
    except:
        return # no rcfile
    try:
        crcmt = os.stat(crcfile).st_mtime
    except:
        crcmt = 0

    if rcmt >= crcmt:
        from py_compile import compile
        compile(rcfile, crcfile)
    
    f = open(crcfile, 'rb')
    hdr = f.read(8)
    if hdr[:4] != imp.get_magic():
        raise ImportError, "Invalid compiled ." + rcmod + ': ' + crcfile

    code = marshal.load(f)
    f.close()
    exec code in globals



def runRCFile(m):
    h = os.environ.get('HOME')
    if h is not None:
        try:
            runrc(h, 'tmacsrc', m.__dict__)
        except:
            return sys.exc_info()
    
    return None
