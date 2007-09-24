#include <Python.h>

#include <term.h>
#include <termios.h>
#include <unistd.h>

#include <sys/ioctl.h>


#define MAXINHOLD       16      /* max length of encoded input seq */
#define OBUFSIZ         64

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

    struct termios old_termios;
    struct termios new_termios;
    
    char tcstrs[1024];
    char *CL, *CM, *CE, *SE, *TI, *TE, *SO, *BL;

    unsigned char inhold[MAXINHOLD];
    int inholdlen;

    char obuf[OBUFSIZ];
    int obuflen;
    
    int li, co;
    
    int fd;
    int enclen;
} TCLayerObject;



static TCLayerObject *layer = NULL;




static void putpad(TCLayerObject *, const char *);




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



static void
tclayer_dealloc(TCLayerObject *self)
{
    Py_XDECREF(self->map);
    
    self->ob_type->tp_free((PyObject *)self);
    
    if (layer == self) {
        layer = NULL;
    }
}



static int
window_size(TCLayerObject *self)
{
    PyObject *ret = NULL;
    struct winsize ws;
    Py_UNICODE uc = TCKEYSYM_WindowResize;
    
    ws.ws_row = self->li;
    ws.ws_col = self->co;
    
    ioctl(self->fd, TIOCGWINSZ, &ws);

    ret = PyObject_CallMethod((PyObject *)self, "postevent", "((u#(ii)))",
        &uc, 1, ws.ws_col, ws.ws_row);
    
    if (ret) {
        Py_DECREF(ret);

        return 1;
    } else {
        return 0;
    }
}



static void
reset_input(TCLayerObject *self)
{
    self->curmap = self->map;
    self->enclen = 0;
    self->inholdlen = 0;
}



static int
illegal_sequence(TCLayerObject *self)
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
decode_and_send(TCLayerObject *self)
{
    PyObject *o = NULL, *args = NULL, *ret = NULL;
    
    o = PyUnicode_Decode((char *)self->inhold, self->inholdlen, "utf8", "strict");
    if (o) {
        ret = PyObject_CallMethod((PyObject *)self, "postevent", "((Os))",
            o, NULL);
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
termcap_arrow_hack(TCLayerObject *self, int okind, int bkind)
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
termcap_init(TCLayerObject *self, char *term, char *termenc)
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
    
    return 1;
}



static int
termios_init(TCLayerObject *self)
{
    if (isatty(self->fd)) {
        tcgetattr(self->fd, &(self->old_termios));

        self->new_termios = self->old_termios;
        cfmakeraw(&(self->new_termios));
    
        tcsetattr(0, TCSASOFT | TCSAFLUSH, &(self->new_termios));
    }
    
    return 1;
}



static int
output_init(TCLayerObject *self)
{
    putpad(self, self->TI);

    return window_size(self);
}



static int
termios_cleanup(TCLayerObject *self)
{
    tcsetattr(0, TCSASOFT | TCSAFLUSH, &(self->old_termios));
}



static int
output_cleanup(TCLayerObject *self)
{
    putpad(self, self->TE);
}



static PyObject *
tclayer_new(PyTypeObject *type, PyObject *args, PyObject *kdws)
{
    TCLayerObject *self;
    char *term = NULL, *termenc = NULL;

    if (layer) {
        PyErr_SetString(PyExc_OSError,
            "only one instance allowed due to termcap");

        return NULL;
    }

    layer = self = (TCLayerObject *)type->tp_alloc(type, 0);
    if (!self) {
        return NULL;
    }

    self->map = self->reactor = NULL;
    
    if (!PyArg_ParseTuple(args, "iO|zz",
        &(self->fd), &(self->reactor), &term, &termenc)) {

        goto failnew;
    }
    
    term = term ? term : getenv("TERM");
    termenc = termenc? termenc : "utf8";

    if (termcap_init(self, term, termenc)) {
        if (termios_init(self)) {
            if (output_init(self)) {
                return (PyObject *)self;
            }
        }
    }

failnew:
    tclayer_dealloc(self);

    return NULL;
}



/* Output Functions */



static int
ttputc(int c)
{
    if (layer->obuflen < OBUFSIZ) {
        layer->obuf[layer->obuflen++] = c;
    } else {
        exit(7);
    }
}



static void
putpad(TCLayerObject *self, const char *str)
{
    int r;
    
    tputs(str, 1, ttputc);
    
    write(self->fd, layer->obuf, layer->obuflen);

    layer->obuflen = 0;
}



static PyObject *
TCLayer_moveto(TCLayerObject *self, PyObject *args)
{
    int x, y;
    
    if (!PyArg_ParseTuple(args, "ii:moveto", &x, &y)) {
        return NULL;
    } 

    putpad(self, tgoto(self->CM, x, y));
    
    Py_RETURN_NONE;
}



static PyObject *
TCLayer_eeol(TCLayerObject *self, PyObject *args)
{
    putpad(self, self->CE);
    
    Py_RETURN_NONE;
}



static PyObject *
TCLayer_eeop(TCLayerObject *self, PyObject *args)
{
    putpad(self, self->CL);
    
    Py_RETURN_NONE;
}



static PyObject *
TCLayer_beep(TCLayerObject *self, PyObject *args)
{
    putpad(self, self->BL);
    
    Py_RETURN_NONE;
}



/* Begin TCLayerObject methods */



static PyObject *
TCLayer_cleanup(TCLayerObject *self, PyObject *args)
{
    PyObject *o = NULL, *a = NULL, *ret = NULL;

    output_cleanup(self);
    termios_cleanup(self);

    o = PyObject_GetAttrString(self->reactor, "stop");
    if (o && PyCallable_Check(o)) {
        a = PyTuple_New(0);
        if (a) {
            ret = PyObject_CallObject(o, a);
        }
    }

    Py_XDECREF(o);
    Py_XDECREF(a);
    Py_XDECREF(ret);
    
    if (!ret) {
        return NULL;
    }

    Py_RETURN_NONE;
}



static PyObject *
TCLayer_fileno(TCLayerObject *self, PyObject *args)
{
    return Py_BuildValue("i", self->fd);
}



static PyObject *
TCLayer_getmap(TCLayerObject *self, PyObject *args)
{
    Py_INCREF(self->map);
    
    return self->map;
}



static PyObject *
TCLayer_got_SIGWINCH(TCLayerObject *self, PyObject *args)
{
    window_size(self);
    
    Py_RETURN_NONE;
}



static PyObject *
TCLayer_reactor(TCLayerObject *self, PyObject *args)
{
    Py_INCREF(self->reactor);
    
    return self->reactor;
}



static PyObject *
TCLayer_feed(TCLayerObject *self, PyObject *args)
{
    PyObject *o, *ret;
    unsigned char *inbuf;
    size_t inlen;
    
    if (!PyArg_ParseTuple(args, "s#:feed", (char *)&inbuf, &inlen)) {
        return NULL;
    } 

    while (inlen) {
        self->inhold[self->inholdlen++] = *inbuf; 

        if (self->inholdlen >= MAXINHOLD) {
            if (!illegal_sequence(self)) {
                return NULL;
            }
        } else if (self->enclen == self->inholdlen) {
            if (!decode_and_send(self)) {
                return NULL;
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
                        return NULL;
                    }                  
                } else {
                    /* move to next map */

                    self->curmap = o;
                }
            } else if (o == Py_None) {
                self->inholdlen--;
                if (!decode_and_send(self)) {
                    return NULL;
                }

                continue;   /* retry */
            } else if (PyInt_CheckExact(o)) {
                self->enclen = PyInt_AS_LONG(o);
            }
        }

        inbuf++; inlen--;
    }

    Py_RETURN_NONE;
}



static PyObject *
TCLayer_timeout(TCLayerObject *self, PyObject *args)
{
    if (self->inholdlen) {
        if (!decode_and_send(self)) {
            return NULL;
        }
    }

    Py_RETURN_NONE;
}



static PyMethodDef TCLayer_methods[] = {
    {"moveto",      (PyCFunction)TCLayer_moveto,        METH_VARARGS},
    {"eeol",        (PyCFunction)TCLayer_eeol,          METH_NOARGS},
    {"eeop",        (PyCFunction)TCLayer_eeop,          METH_NOARGS},
    {"beep",        (PyCFunction)TCLayer_beep,          METH_NOARGS},

    {"cleanup",     (PyCFunction)TCLayer_cleanup,       METH_NOARGS},
    {"fileno",      (PyCFunction)TCLayer_fileno,        METH_NOARGS},
    {"getmap",      (PyCFunction)TCLayer_getmap,        METH_NOARGS},
    {"got_SIGWINCH",(PyCFunction)TCLayer_got_SIGWINCH,  METH_NOARGS},
    {"reactor",     (PyCFunction)TCLayer_reactor,       METH_NOARGS},
    {"feed",        (PyCFunction)TCLayer_feed,          METH_VARARGS},
    {"timeout",     (PyCFunction)TCLayer_timeout,       METH_NOARGS},

    {NULL,          NULL}
};


static PyTypeObject TCLayer_Type = {
    /* The ob_type field must be initialized in the module init function
     * to be portable to Windows without using C++. */    PyObject_HEAD_INIT(NULL)
    0,                      /*ob_size*/
    "_TCLayer",             /*tp_name*/
    sizeof(TCLayerObject),  /*tp_basicsize*/
    0,                      /*tp_itemsize*/
    /* methods */
    (destructor)tclayer_dealloc, /*tp_dealloc*/
    0,                      /*tp_print*/
    0,                      /*tp_getattr*/
    0,                      /*tp_setattr*/
    0,                      /*tp_compare*/
    0,                      /*tp_repr*/
    0,                      /*tp_as_number*/
    0,                      /*tp_as_sequence*/
    0,                      /*tp_as_mapping*/
    0,                      /*tp_hash*/
    0,                      /*tp_call*/
    0,                      /*tp_str*/
    0,                      /*tp_getattro*/
    0,                      /*tp_setattro*/
    0,                      /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
    0,                      /*tp_doc*/ 
    0,                      /*tp_traverse*/ 
    0,                      /*tp_clear*/   
    0,                      /*tp_richcompare*/
    0,                      /*tp_weaklistoffset*/
    0,                      /*tp_iter*/ 
    0,                      /*tp_iternext*/
    TCLayer_methods,        /*tp_methods*/
    0,                      /*tp_members*/
    0,                      /*tp_getset*/
    0,                      /*tp_base*/
    0,                      /*tp_dict*/
    0,                      /*tp_descr_get*/ 
    0,                      /*tp_descr_set*/
    0,                      /*tp_dictoffset*/
    0,                      /*tp_init*/
    PyType_GenericAlloc,    /*tp_alloc*/
    tclayer_new,            /*tp_new*/
    _PyObject_Del,          /*tp_free*/
    0,                      /*tp_is_gc*/
};




PyMODINIT_FUNC
init_tclayer(void)
{
    PyObject *m, *d;

    m = Py_InitModule("_tclayer", _tclayerMethods);

    TCLayer_Type.ob_type = &PyType_Type;
    d = PyModule_GetDict(m);
    PyDict_SetItemString(d, "_TCLayer", (PyObject *)&TCLayer_Type);

#if 0
    SpamError = PyErr_NewException("spam.error", NULL, NULL);
    Py_INCREF(SpamError);

    PyModule_AddObject(m, "error", SpamError);
#endif
}
