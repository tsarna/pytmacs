# $Id: test_tmacs.py,v 1.7 2007-09-29 01:41:21 tsarna Exp $

def additional_tests():
    import doctest

    return doctest.DocFileSuite(
       'tmacs/edit/SNIFF.txt',
       'tmacs/edit/UBUF.txt',
       'tmacs/edit/EDITMISC.txt',
       'tmacs/edit/MARKER.txt',
       'tmacs/edit/MARKFILE.txt',
       'tmacs/edit/MARKMOVE.txt',
       'tmacs/edit/MARKEDIT.txt',
       'tmacs/edit/BUFFER.txt',
       'tmacs/ui/KEYSYMS.txt',
       'tmacs/ui/KEYMAP.txt',
       'tmacs/ui/CHARCELL.txt',
#       'tmacs/termioscap/README.txt',
        optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE,
    )

