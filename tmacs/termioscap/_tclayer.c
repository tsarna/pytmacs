/* $Id: _tclayer.c,v 1.16 2007-10-03 15:07:50 tsarna Exp $ */

#include <Python.h>
#include "structmember.h"

#include <term.h>
#include <termios.h>
#include <unistd.h>

#include <sys/ioctl.h>


#define MAXINHOLD       16      /* max length of encoded input seq */
#define OBUFSIZ         64
#define IBUFSIZ         64

extern char PC, *BC, *UP;       /* termcap upgliness */
extern short ospeed;

#include "tckeymap.h"

/* functions defined in the module */

static PyMethodDef _tclayerMethods[] = {
#if 0
    {"system",  spam_system, METH_VARARGS, "Execute a shell command."},
#endif

    {NULL, NULL, 0, NULL}
};


typedef struct {
    PyObject_HEAD

    PyObject *map;
    PyObject *curmap;
    PyObject *reactor;
    PyObject *callback;
    PyObject *timeout;

    struct termios old_termios;
    struct termios new_termios;
    
    char tcstrs[1024];
    char *CL, *CM, *CE, *SE, *TI, *TE, *SO, *BL;

    unsigned char inhold[MAXINHOLD];
    int inholdlen;

    char obuf[OBUFSIZ];
    int obuflen;
    
    int li, co;
    
    int ifd, ofd;
    int enclen;
} tclayer;


typedef enum Timeout {
    TO_ERR, TO_NONE, TO_TRAVERSE, TO_ENCODE, TO_MAX
} Timeout;

static double timeouts[TO_MAX] = { /* correspond to the above */
    0.0, 0.2, 0.2, 5.0
};


static tclayer *thelayer = NULL;




static void putpad(tclayer *, const char *);




static PyObject *
tclayer_new(PyTypeObject *type, PyObject *args, PyObject *kdws)
{
    tclayer *self;
    
    if (thelayer) {
        PyErr_SetString(PyExc_OSError,
            "only one instance allowed due to termcap");

        return NULL;
    }

    self = (tclayer *)type->tp_alloc(type, 0);
    if (self) {
        self->map = self->curmap = self->reactor = NULL;
        self->obuflen = 0;
        thelayer = self;
    }
    
    return (PyObject *)self;
}



static void
tclayer_dealloc(tclayer *self)
{
    Py_XDECREF(self->map);
    Py_XDECREF(self->reactor);
    Py_XDECREF(self->callback);
    Py_XDECREF(self->timeout);
    
    self->ob_type->tp_free((PyObject *)self);
    
    if (thelayer == self) {
        thelayer = NULL;
    }
}



static PyObject *
AllocMap(void)
{
    PyObject *o;
    int i;
    
    o = PyTuple_New(256);
    if (o) {
        for (i = 0; i < 256; i++) {
            Py_INCREF(Py_None);
            PyTuple_SetItem(o, i, Py_None);
        }
    }

    return o;
}



static int
PutMap(PyObject *o, unsigned char *s, size_t l, Py_UNICODE u)
{
    PyObject *v;
    
    if (l > 1) {
        v = PyTuple_GET_ITEM(o, *s);

        if (PyTuple_CheckExact(v) && (PyTuple_GET_SIZE(o) == 256)) {
            return PutMap(v, s+1, l-1, u);
        } else if (v == Py_None) {
            v = AllocMap();
            if (v) {
                PyTuple_SetItem(o, *s, v);

                return PutMap(v, s+1, l-1, u);
            } else {
                return 0;
            }
        } else {
            PyErr_SetString(PyExc_KeyError, "conflicting termcap keymaps");

            return 0;
        }
    } else {
        if (PyTuple_GET_ITEM(o, *s) != Py_None) {
            PyErr_SetString(PyExc_KeyError, "conflicting termcap keymaps");

            return 0;
        } else {
            v = Py_BuildValue("(u#s)", &u, 1, NULL);
            if (v) {
                PyTuple_SetItem(o, *s, v);
            } else {
                return 0;
            }
        }
    }

    return 1;
}



static int
window_size(tclayer *self)
{
    PyObject *ret = NULL;
    struct winsize ws;
    Py_UNICODE uc = TCKEYSYM_WindowResize;
    
    ws.ws_row = self->li;
    ws.ws_col = self->co;
    
    if (ioctl(self->ifd, TIOCGWINSZ, &ws) >= 0) {
        self->li = ws.ws_row;
        self->co = ws.ws_col;
    }

    ret = PyObject_CallMethod((PyObject *)self, "postevent", "((u#(ii)))",
        &uc, 1, self->co, self->li);
    
    if (ret) {
        Py_DECREF(ret);

        return 1;
    } else {
        return 0;
    }
}



static void
reset_input(tclayer *self)
{
    self->curmap = self->map;
    self->enclen = 0;
    self->inholdlen = 0;
}



static int
illegal_sequence(tclayer *self)
{
    PyObject *ret = NULL;
    Py_UNICODE uc = TCKEYSYM_IllegalSequence;
    
    ret = PyObject_CallMethod((PyObject *)self, "postevent", "((u#s#))",
        &uc, 1, self->inhold, self->inholdlen);
    
    reset_input(self);

    if (ret) {
        Py_DECREF(ret);

        return 1;
    } else {
        return 0;
    }
}



static int
decode_and_send(tclayer *self)
{
    PyObject *o = NULL, *args = NULL, *ret = NULL;
    Py_ssize_t l, i;
    
    o = PyUnicode_Decode((char *)self->inhold, self->inholdlen, "utf8", "strict");
    if (o) {
        l = PyUnicode_GET_SIZE(o);
        if (l == 1) {
            ret = PyObject_CallMethod((PyObject *)self, "postevent", "((Os))",
                o, NULL);
        } else {
            /* need to split into individual character events */
            i = 0;
            ret = Py_None;
            while (ret && (i < l)) {
                ret = PyObject_CallMethod((PyObject *)self, "postevent", "((u#s))",
                    &(PyUnicode_AS_UNICODE(o)[i]), 1, NULL);
                i++;
                Py_XDECREF(ret);
            }
        }
    } else {
        PyErr_Clear();
        return illegal_sequence(self);
    }
    
    Py_XDECREF(o);

    reset_input(self);
    
    if (ret) {
        Py_DECREF(ret);

        return 1;
    } else {
        return 0;
    }
}



static void
termcap_arrow_hack(tclayer *self, int okind, int bkind)
{
    if ((okind == 4) && (bkind == 0)) {
        PutMap(self->map, (unsigned char *)"\x1b[A", 3, 0xEC40);
        PutMap(self->map, (unsigned char *)"\x1b[B", 3, 0xEC41);
        PutMap(self->map, (unsigned char *)"\x1b[C", 3, 0xEC43);
        PutMap(self->map, (unsigned char *)"\x1b[D", 3, 0xEC42);
    } else if ((okind == 0) && (bkind == 4)) {
        PutMap(self->map, (unsigned char *)"\x1bOA", 3, 0xEC40);
        PutMap(self->map, (unsigned char *)"\x1bOB", 3, 0xEC41);
        PutMap(self->map, (unsigned char *)"\x1bOC", 3, 0xEC43);
        PutMap(self->map, (unsigned char *)"\x1bOD", 3, 0xEC42);
    }
}



static int
termcap_init(tclayer *self, char *term, char *termenc)
{
    PyObject *o, *tp;
    TermcapKeymap *tck;
    char termcap[1024], tccode[3] = "\0\0\0", *p, *t;
    unsigned char c;
    int r, i, n, l;
    int okind = 0, bkind = 0;

    if (term) {
        r = tgetent(termcap, term);
    }
    
    if (!term || (r < 1)) {
        PyErr_SetString(PyExc_RuntimeError, "termcap initialization failed");
        return 0;
    }

    p = self->tcstrs;

    t = tgetstr("pc", &p);
    PC = t ? *t : 0;

    UP = tgetstr("up", &p);         /* up line              */
    BC = tgetstr("bc", &p);         /* backspace            */

    self->CL = tgetstr("cl", &p);   /* clear screen & home  */
    self->CM = tgetstr("cm", &p);   /* cursor move          */
    self->CE = tgetstr("ce", &p);   /* clear to EOL         */
    self->SE = tgetstr("se", &p);   /* end standout         */
    self->TI = tgetstr("ti", &p);   /* term init            */
    self->TE = tgetstr("te", &p);   /* term end             */
    self->SO = tgetstr("so", &p);   /* standout             */
    self->BL = tgetstr("bl", &p);   /* bell                 */

    self->li = tgetnum("li");       /* lines                */
    self->co = tgetnum("co");       /* columns              */

    if (!self->CL || !self->CM || !UP) {
        PyErr_SetString(PyExc_RuntimeError, "incomplete termcap entry");
        return 0;
    }

    self->map = AllocMap();
    if (!self->map) {
        return 0;
    }

    reset_input(self);
    
    tck = tckeys;
    while (tck->tccode[0]) {
        tccode[0] = tck->tccode[0];
        tccode[1] = tck->tccode[1];

        t = tgetstr(tccode, &p);

        if (t) {
            l = strlen(t);
            if (l > MAXINHOLD) {
                PyErr_SetString(PyExc_KeyError, "sequence encoding too long");
                
                return 0;
            }

            /* hack for messed up termcaps to get arrows right */
            
            if ((l == 3) && (t[0] == '\x1b')) {
                if ((t[2] >= 'A') && (t[2] <= 'D')) {
                    if (t[1] == 'O') {
                        okind++;
                    } else if (t[1] == '[') {
                        bkind++;
                    }                    
                }
            }
            
            if (!PutMap(self->map, (unsigned char *)t, l, tck->unichar)) {
                return 0;
            }
        }
        
        tck++;
    }

    termcap_arrow_hack(self, okind, bkind);


    /* if utf8, put in length bytes */
    
    if (!strcmp(termenc, "utf8")) {
        for (i = 128; i < 256; i++) {
            n = 0;
            
            if ((i & 0xE0) == 0xC0) {
                n = 2;
            } else if ((i & 0xF0) == 0xE0) {
                n = 3;
            } else if ((i & 0xF8) == 0xF0) {
                n = 4;
            } else if ((i & 0xFC) == 0xF8) {
                n = 5;
            } else if ((i & 0xFE) == 0xFC) {
                n = 6;
            }
            
            if (n) {
                o = PyInt_FromLong(n);
                if (!o) {
                    return 0;
                } else {
                    PyTuple_SetItem(self->map, i, o);
                }
            }
        }
    }

    /* fill remaining slots w/ encoding */
    for (i = 0; i < 256; i++) {
        c = (unsigned char)i;
        
        if (PyTuple_GET_ITEM(self->map, i) == Py_None) {
            o = PyUnicode_Decode((char *)&c, 1, termenc, "strict");
            if (o) {
                tp = PyTuple_New(2);
                if (tp) {
                    PyTuple_SET_ITEM(tp, 0, o);
                    Py_INCREF(Py_None);
                    PyTuple_SET_ITEM(tp, 1, Py_None);
                    PyTuple_SetItem(self->map, i, tp);
                } else {
                    Py_DECREF(o);
                    return 0;
                }
            } else {
                PyErr_Clear();
                /* XXX what to do here? */
            }
        }
    }
    
    if (!PyObject_CallMethod((PyObject *)self->reactor,
    "addReader", "(O)", self)) {
        return 0;
    }
    
    return 1;
}



static int
termios_init(tclayer *self)
{
    if (isatty(self->ifd)) {
        tcgetattr(self->ifd, &(self->old_termios));

        self->new_termios = self->old_termios;
        cfmakeraw(&(self->new_termios));
    
        tcsetattr(self->ifd, TCSASOFT | TCSAFLUSH, &(self->new_termios));
    }
    
    return 1;
}



static int
output_init(tclayer *self)
{
    putpad(self, self->TI);

    return window_size(self);
}



static int
termios_cleanup(tclayer *self)
{
    if (isatty(self->ifd)) {
        tcsetattr(0, TCSASOFT | TCSAFLUSH, &(self->old_termios));
    }
    
    return 1;
}



static int
output_cleanup(tclayer *self)
{
    putpad(self, self->TE);
    
    return 1;
}



static int
tclayer_init(tclayer *self, PyObject *args, PyObject *kwds)
{
    char *term = NULL, *termenc = NULL;

    if (!PyArg_ParseTuple(args, "iiO|zz",
        &(self->ifd), &(self->ofd), &(self->reactor), &term, &termenc)) {

        goto failnew;
    }
    
    term = term ? term : getenv("TERM");
    termenc = termenc? termenc : getenv("TMACS_TERM_ENCODING");
    termenc = termenc? termenc : "utf8";

    if (termcap_init(self, term, termenc)) {
        if (termios_init(self)) {
            if (output_init(self)) {
                self->timeout = PyObject_GetAttrString((PyObject *)self,
                    "timeout");

                if (self->timeout) {
                    return 0;
                }
            }
        }
    }

failnew:
    tclayer_dealloc(self);

    return -1;
}



/* Output Functions */



static int
ttputc(int c)
{
    if (thelayer->obuflen < OBUFSIZ) {
        thelayer->obuf[thelayer->obuflen++] = c;
    } else {
        exit(7);
    }
}



static void
putpad(tclayer *self, const char *str)
{
    tputs(str, 1, ttputc);
    
    write(self->ofd, thelayer->obuf, thelayer->obuflen);

    thelayer->obuflen = 0;
}



PyDoc_STRVAR(tclayer_moveto_doc,
"Move cursor to position (x,y) on the display.\n\
\n\
Counting starts from (0,0) in the upper left hand corner.");



static PyObject *
tclayer_moveto(tclayer *self, PyObject *args)
{
    int x, y;
    
    if (!PyArg_ParseTuple(args, "ii:moveto", &x, &y)) {
        return NULL;
    } 

    putpad(self, tgoto(self->CM, x, y));
    
    Py_RETURN_NONE;
}



PyDoc_STRVAR(tclayer_eeol_doc,
"Erase from the current cursor position to the end of the line.");



static PyObject *
tclayer_eeol(tclayer *self, PyObject *args)
{
    putpad(self, self->CE);
    
    Py_RETURN_NONE;
}


PyDoc_STRVAR(tclayer_eeop_doc,
"Erase from the current cursor position to the end of the screen.");



static PyObject *
tclayer_eeop(tclayer *self, PyObject *args)
{
    putpad(self, self->CL);
    
    Py_RETURN_NONE;
}



PyDoc_STRVAR(tclayer_beep_doc,
"Beep the terminal.");



static PyObject *
tclayer_beep(tclayer *self, PyObject *args)
{
    putpad(self, self->BL);
    
    Py_RETURN_NONE;
}



PyDoc_STRVAR(tclayer_standout_doc,
"Enter 'standout' (generally reverse-video) mode.");



static PyObject *
tclayer_standout(tclayer *self, PyObject *args)
{
    putpad(self, self->SO);
    
    Py_RETURN_NONE;
}



PyDoc_STRVAR(tclayer_nostandout_doc,
"Leave 'standout' mode -- return to normal text.");



static PyObject *
tclayer_nostandout(tclayer *self, PyObject *args)
{
    putpad(self, self->SE);
    
    Py_RETURN_NONE;
}



/* Begin tclayer methods */



PyDoc_STRVAR(tclayer_cleanup_doc,
"Restore terminal to previous state in preparation for exit");



static PyObject *
tclayer_cleanup(tclayer *self, PyObject *args)
{
    output_cleanup(self);
    termios_cleanup(self);

    Py_RETURN_NONE;
}



PyDoc_STRVAR(tclayer_fileno_doc,
"Return the input file descriptor number. Used by the reactor.");



static PyObject *
tclayer_fileno(tclayer *self, PyObject *args)
{
    return Py_BuildValue("i", self->ifd);
}



PyDoc_STRVAR(tclayer_got_SIGWINCH_doc,
"Clients of _TCLayer should arrange to have this method called\n\
when SIGWINCH occurs, so that _TCLayer can update its idea of\n\
the terminal's size.");



static PyObject *
tclayer_got_SIGWINCH(tclayer *self, PyObject *args)
{
    window_size(self);
    
    Py_RETURN_NONE;
}



static Timeout
tclayer_feed(tclayer *self, unsigned char *inbuf, Py_ssize_t inlen)
{
    PyObject *o, *ret;

    while (inlen) {
        self->inhold[self->inholdlen++] = *inbuf; 

        if (self->inholdlen >= MAXINHOLD) {
            if (!illegal_sequence(self)) {
                return TO_ERR;
            }
        } else if (self->enclen == self->inholdlen) {
            if (!decode_and_send(self)) {
                return TO_ERR;
            }
        } else if (self->enclen > 0) {
            /* just wait until we get a whole multibyte seq */
        } else {
            /* walking maps */

            o = PyTuple_GET_ITEM(self->curmap, *inbuf);
            if (PyTuple_CheckExact(o)) {
                if (PyTuple_GET_SIZE(o) == 2) {
                    ret = PyObject_CallMethod((PyObject *)self,
                        "postevent", "(O)", o);

                    Py_XDECREF(ret);
                    reset_input(self);

                    if (!ret) {
                        return TO_ERR;
                    }  
                } else {
                    /* move to next map */

                    self->curmap = o;
                }
            } else if (o == Py_None) {
                if (self->inholdlen > 1) {
                    self->inholdlen--;
                    if (!decode_and_send(self)) {
                        return TO_ERR;
                    }

                    continue;   /* retry w/ current character */
                } else {
                    if (!decode_and_send(self)) {
                        return TO_ERR;
                    }
                }
            } else if (PyInt_CheckExact(o)) {
                self->enclen = PyInt_AS_LONG(o);
            }
        }

        inbuf++; inlen--;
    }

    if (self->enclen) {
        return TO_ENCODE;
    } else if (self->curmap != self->map) {
        return TO_TRAVERSE;
    } else {
        return TO_NONE;
    }
}



PyDoc_STRVAR(tclayer_doRead_doc,
"The reactor calls this method to indicate new input for reading.\n\
doRead will consume it, run its state machine, and call postevent\n\
on itself to queue events for the client. (postevent() must be\n\
defined in a subclass.)");



static PyObject *
tclayer_doRead(tclayer *self, PyObject *args)
{
    unsigned char inbuf[IBUFSIZ];
    Py_ssize_t inlen;
    Timeout timo;
    PyObject *ret;
    
    inlen = read(self->ifd, inbuf, IBUFSIZ);
    if (inlen < 0) {
        return PyErr_SetFromErrno(PyExc_IOError);
    } else {
        timo = tclayer_feed(self, inbuf, inlen);
        if (timo == TO_ERR) {
            if (self->callback) {
                ret = PyObject_CallMethod(self->callback, "cancel", "()");
                if (ret) {
                    Py_DECREF(ret);
                } else {
                    PyErr_Clear();
                }

                Py_DECREF(self->callback);
                self->callback = NULL;
            }
            
            return NULL;
        } else {
            if (self->callback) {
                ret = PyObject_CallMethod(self->callback,
                    "reset", "(d)", timeouts[timo]);
                if (ret) {
                    Py_DECREF(ret);
                    
                    Py_RETURN_NONE;
                } else {
                    PyErr_Clear();
                    Py_DECREF(self->callback);
                    self->callback = NULL;
                }
            }
            
            ret = PyObject_CallMethod(self->reactor,
                "callLater", "(dO)", timeouts[timo], self->timeout);
            if (ret) {
                self->callback = ret;
            } else {
                return NULL;
            }
        }
    }

    Py_RETURN_NONE;
}



PyDoc_STRVAR(tclayer_timeout_doc,
"Through the reactor, _TCLayer will arrange to have this method called\n\
some time after input is read to handle partial input sequences.");



static PyObject *
tclayer_timeout(tclayer *self, PyObject *args)
{
    /* clear timeout since it expired*/
    Py_XDECREF(self->callback);
    self->callback = NULL;

    if (self->inholdlen) {
        if (!decode_and_send(self)) {
            return NULL;
        }
    }

    Py_RETURN_NONE;
}



static PyMemberDef tclayer_members[] = {
    {"reactor", T_OBJECT, offsetof(tclayer, reactor),
        READONLY, "I/O reactor instance"},
    
    {"map", T_OBJECT, offsetof(tclayer, map),
        READONLY, "Input byte translation map tree"},
    
    {"curmap", T_OBJECT, offsetof(tclayer, curmap),
        READONLY, "Current level in input translation tree"},
    
    {"lines", T_INT, offsetof(tclayer, li),
        READONLY, "Number of lines in current display size"},
    
    {"columns", T_INT, offsetof(tclayer, co),
        READONLY, "Number of columns in current display size"},
    
    NULL
};



static PyMethodDef tclayer_methods[] = {
    {"moveto",      (PyCFunction)tclayer_moveto,        METH_VARARGS,
        tclayer_moveto_doc},
        
    {"eeol",        (PyCFunction)tclayer_eeol,          METH_NOARGS,
        tclayer_eeol_doc},
        
    {"eeop",        (PyCFunction)tclayer_eeop,          METH_NOARGS,
        tclayer_eeop_doc},
        
    {"beep",        (PyCFunction)tclayer_beep,          METH_NOARGS,
        tclayer_beep_doc},
        
    {"standout",    (PyCFunction)tclayer_standout,      METH_NOARGS,
        tclayer_standout_doc},
        
    {"nostandout",  (PyCFunction)tclayer_nostandout,    METH_NOARGS,
        tclayer_nostandout_doc},

    {"cleanup",     (PyCFunction)tclayer_cleanup,       METH_NOARGS,
        tclayer_cleanup_doc},
        
    {"fileno",      (PyCFunction)tclayer_fileno,        METH_NOARGS,
        tclayer_fileno_doc},
        
    {"got_SIGWINCH",(PyCFunction)tclayer_got_SIGWINCH,  METH_NOARGS,
        tclayer_got_SIGWINCH_doc},
        
    {"doRead",      (PyCFunction)tclayer_doRead,        METH_NOARGS,
        tclayer_doRead_doc},
        
    {"timeout",     (PyCFunction)tclayer_timeout,       METH_NOARGS,
        tclayer_timeout_doc},

    {NULL,          NULL}
};



PyDoc_STRVAR(tclayer_doc,
"tclayer(infd, outfd, reactor, [terminaltype, [termencoding]])\n\
 -> termios/termcap based terminal I/O layer attached to the reactor\n\
\n\
Only one instance may be created due to POSIX API limitations\n\
\n\
'infd' and 'outfd' are file descriptors for input and output.\n\
'reactor' is a Twisted-type reactor (or TMACS's \"untwisted\" alternative).\n\
'terminaltype' is the terminal kind, defaulting to the value of $TERM.\n\
'termencoding' is the encodding, defaulting to utf8.");


static PyTypeObject tclayer_type = {
    PyObject_HEAD_INIT(NULL)
    0,                                      /*ob_size*/
    "tmacs.termioscap._tclayer",            /*tp_name*/
    sizeof(tclayer),                        /*tp_basicsize*/
    0,                                      /*tp_itemsize*/
    /* methods */
    (destructor)tclayer_dealloc,            /*tp_dealloc*/
    0,                                      /*tp_print*/
    0,                                      /*tp_getattr*/
    0,                                      /*tp_setattr*/
    0,                                      /*tp_compare*/
    0,                                      /*tp_repr*/
    0,                                      /*tp_as_number*/
    0,                                      /*tp_as_sequence*/
    0,                                      /*tp_as_mapping*/
    0,                                      /*tp_hash*/
    0,                                      /*tp_call*/
    0,                                      /*tp_str*/
    0,                                      /*tp_getattro*/
    0,                                      /*tp_setattro*/
    0,                                      /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
    tclayer_doc,                            /*tp_doc*/ 
    0,                                      /*tp_traverse*/ 
    0,                                      /*tp_clear*/   
    0,                                      /*tp_richcompare*/
    0,                                      /*tp_weaklistoffset*/
    0,                                      /*tp_iter*/ 
    0,                                      /*tp_iternext*/
    tclayer_methods,                        /*tp_methods*/
    tclayer_members,                        /*tp_members*/
    0,                                      /*tp_getset*/
    0,                                      /*tp_base*/
    0,                                      /*tp_dict*/
    0,                                      /*tp_descr_get*/ 
    0,                                      /*tp_descr_set*/
    0,                                      /*tp_dictoffset*/
    (initproc)tclayer_init,                 /*tp_init*/
    PyType_GenericAlloc,                    /*tp_alloc*/
    tclayer_new,                            /*tp_new*/
    _PyObject_Del,                          /*tp_free*/
    0,                                      /*tp_is_gc*/
};




PyMODINIT_FUNC
init_tclayer(void)
{
    PyObject *m, *d;

    if (PyType_Ready(&tclayer_type) < 0)
        return;

    m = Py_InitModule3("_tclayer", _tclayerMethods, "termcap/termios terminal interface layer for reactor");
    
    Py_INCREF(&tclayer_type);
    PyModule_AddObject(m, "_tclayer", (PyObject *)&tclayer_type);
}
