# $Id: test_tmacs.py,v 1.3 2007-08-18 14:59:17 tsarna Exp $

def additional_tests():
    import doctest

    return doctest.DocFileSuite(
       'tmacs/edit/SNIFF.txt',
       'tmacs/edit/UBUF.txt',
       'tmacs/edit/EDITMISC.txt',
       'tmacs/edit/MARKER.txt',
       'tmacs/edit/MARKFILE.txt',
       'tmacs/edit/BUFFER.txt',
#       'tmacs/ui/INPUT.txt',
#       'tmacs/termioscap/README.txt',
        optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE,
    )

