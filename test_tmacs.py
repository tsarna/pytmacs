def additional_tests():
    import doctest

    return doctest.DocFileSuite(
       'tmacs/ui/INPUT.txt',
       'tmacs/termioscap/README.txt',
        optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE,
    )
