import __tmacs__

f = open(__file__.rsplit('.')[0]+'.txt')
for l in f:
    l = l.strip()
    if l[0] == ':':
        themap = getattr(__tmacs__, l[1:])
    else:
        seq, cmdname = l.split(None, 1)
        themap.bind(seq, cmdname)
