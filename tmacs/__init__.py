#!/usr/bin/env python

import sys, os, imp

sys.modules['__tmacs__'] = imp.new_module('__tmacs__')

if __name__ == '__main__':
    from tmacs.app.main import main
    main(sys.argv, os.environ)
