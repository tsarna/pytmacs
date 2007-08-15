from codecs import lookup

def open_for_write(buffer, fn):
    f = open(fn, 'wb')
    codec = lookup(buffer.encoding)
    sw = codec.streamwriter(f, 'strict') # XXX strict?
    return sw
    
