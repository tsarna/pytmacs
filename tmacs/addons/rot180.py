# -*- coding: utf8 -*-

# The following table taken from Acme::Rot180 which carries this license:
#
# Copyright (C) 2005 by Jan-Pieter Cornet
#
# This library is free software; you can redistribute it and/or modify
# it under the same terms as Perl itself, either Perl version 5.8.6 or,
# at your option, any later version of Perl 5 you may have available.

_turns = {
    u' ' : u' ',
    u'!' : u"\u00a1",          # ¡
    u'"' : u"\u201e",          # „
    u'#' : u'#',
    u'$' : u'$',
    u'%' : u'%',
    u'&' : u"\u214b",          # ⅋
    u"'" : u"\u0375",          # ͵
    u'(' : u')',
    u')' : u'(',
    u'*' : u'*',
    u'+' : u'+',
    u',' : u"\u2018",          # ‘
    u'-' : u'-',
    u'.' : u"\u02d9",          # ˙
    u'/' : u'/',
    u'0' : u'0',
    u'1' : u"\u002c\u20d3",  # ,⃓ can be improved
    u'2' : u"\u10f7",          # ჷ
    u'3' : u"\u03b5",          # ε
    u'4' : u"\u21c1\u20d3",  # ⇁⃓ can be improved
    u'5' : u"\u1515",          # ᔕ or maybe just "S"
    u'6' : u'9',
    u'7' : u"\u005f\u0338",  # _̸
    u'8' : u'8',
    u'9' : u'6',
    u':' : u':',
    u';' : u"\u22c5\u0315",  # ⋅̕ sloppy, should be improved
    u'<' : u'>',
    u'=' : u'=',
    u'>' : u'<',
    u'?' : u"\u00bf",          # ¿
    u'@' : u'@',                 # can be improved
    u'A' : u"\u13cc",          # Ꮜ
    u'B' : u"\u03f4",          # ϴ can be improved
    u'C' : u"\u0186",          # Ɔ
    u'D' : u'\u15ed',          
    u'E' : u"\u018e",          # Ǝ
    u'F' : u"\u2132",          # Ⅎ
    u'G' : u"\u2141",          # ⅁
    u'H' : u'H',
    u'I' : u'I',
#    u'J' : u"\u017f\u0332",  # ſ̲
    u'J' : u"\u017f",  # ſ̲
    u'K' : u"\u4e2c",          #  丬
    u'L' : u"\u2142",          # ⅂
    u'M' : u"\u019c",          # Ɯ or maybe just "W"
    u'N' : u'N',
    u'O' : u'O',
    u'P' : u'd',                 # should be uppercase P
    u'Q' : u"\u053e",          # Ծ can be improved
    u'R' : u"\u0222",          # Ȣ can be improved
    u'S' : u'S',
    u'T' : u"\u22a5",          # ⊥
    u'U' : u"\u144e",          # ᑎ
    u'V' : u"\u039b",          # Λ
    u'W' : u'M',
    u'X' : u'X',
    u'Y' : u"\u2144",          # ⅄
    u'Z' : u'Z',
    u'[' : u']',
    u'\\' : u'\\',
    u']' : u'[',
    u'^' : u"\u203f",          # ‿
    u'_' : u"\u203e",          # ‾
    u'`' : u"\u0020\u0316",  #  ̖
    u'a' : u"\u0250",          # ɐ
    u'b' : u'q',
    u'c' : u"\u0254",          # ɔ
    u'd' : u'p',
    u'e' : u"\u01dd",          # ǝ
    u'f' : u"\u025f",          # ɟ
    u'g' : u"\u0253",          # ɓ
    u'h' : u"\u0265",          # ɥ
#   u'i' : u"\u0131\u0323",  # ı̣
    u'i' : u"\u1d09",		# ᴉ
#    u'j' : u"\u017f\u0323",  # ſ̣
    u'j' : u"\u017f",  # ſ̣
    u'k' : u"\u029e",          # ʞ
    u'l' : u"\u01ae",          # Ʈ can be improved
    u'm' : u"\u026f",          # ɯ
    u'n' : u'u',
    u'o' : u'o',
    u'p' : u'd',
    u'q' : u'b',
    u'r' : u"\u0279",          # ɹ
    u's' : u's',
    u't' : u"\u0287",          # ʇ
    u'u' : u'n',
    u'v' : u"\u028c",          # ʌ
    u'w' : u"\u028d",          # ʍ
    u'x' : u'x',
    u'y' : u"\u028e",          # ʎ
    u'z' : u'z',
    u'{' : u'}',
    u'|' : u'|',
    u'}' : u'{',
    u'~' : u"\u223c",          # ∼
}

for k, v in _turns.items():
    if v not in _turns:
        _turns[v] = k
        
def turnletter(s):
    global turns
    
    v = _turns.get(s)
    if v is not None:
        return v

    v = '?' # ???
        
    return v
            

def turn(s):
    l = []
    for c in s:
        l.append(turnletter(c))
        
    l.reverse()
    
    return u''.join(l)
    

if __name__ == '__main__':
    import sys
    print turn(sys.argv[1].decode('utf8')).encode('utf8')
