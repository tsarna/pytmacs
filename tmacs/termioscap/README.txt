================
TMACS Termioscap
================

:Author: Ty Sarna

.. contents ::

Module
------

the ``tmacs.termioscap`` module needs more documentation than this::

    >>> from tmacs.termioscap import TCLayer
    >>> import os
    >>> fd = os.open('/dev/null', os.O_RDWR)
    >>> t = TCLayer(fd)
