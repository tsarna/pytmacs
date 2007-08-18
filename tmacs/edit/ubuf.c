/* $Id: ubuf.c,v 1.10 2007-08-18 21:38:10 tsarna Exp $ */

/* 6440931 */

#include <Python.h>
#include <structmember.h>

#include "ubuf.h"

PyObject *ReadOnlyBufferError = NULL;
extern PyTypeObject marker_type;


#if 0
#define D(x) x
#else
#define D(x) /*x*/
#endif

/* prototypes for static functions */

static int ubuf_set_encoding(ubuf *self, PyObject *value, void *closure);
static void ubuf_dealloc(ubuf *self);
static PyObject *ubuf_new(PyTypeObject *type, PyObject *args, PyObject *kdws);
static int ubuf_init(ubuf *self, PyObject *args, PyObject *kwds);
/* get/set methods */
static int ubuf_set_err_notallowed(ubuf *self, PyObject *value, void *closure);
static PyObject *ubuf_get_changed(ubuf *self, void *closure);
static int ubuf_set_changed(ubuf *self, PyObject *value, void *closure);
static PyObject *ubuf_get_encoding(ubuf *self, void *closure);
static int ubuf_set_encoding(ubuf *self, PyObject *value, void *closure);
static PyObject *ubuf_get_gapsize(ubuf *self, void *closure);
static PyObject *ubuf_get_gapstart(ubuf *self, void *closure);
static PyObject *ubuf_get_loaned(ubuf *self, void *closure);
static PyObject *ubuf_get_read_only(ubuf *self, void *closure);
static int ubuf_set_read_only(ubuf *self, PyObject *value, void *closure);
/* mapping methods */
static Py_ssize_t ubuf_mp_length(PyObject *self);
static PyObject *ubuf_mp_subscript(PyObject *selfo, PyObject *o);
static int ubuf_mp_ass_subscript(PyObject *selfo, PyObject *k, PyObject *v);
/* basic methods */
static PyObject *ubuf_repr(PyObject *self);
static PyObject *ubuf_iter(PyObject *self);
/* file-like methods */
/* add-on methods */
static PyObject *ubuf_append(PyObject *selfo, PyObject *args);
static PyObject *ubuf_borrow(ubuf *self, PyObject *args);

/* Begin ubuf create/delete methods */

static void
ubuf_dealloc(ubuf *self)
{
    marker *cur, *next;
    
    /* XXX need to point uobj to the full memory */

    /* unlink all markers */
    cur = self->markers;
    while (cur) {
        next = cur->next;
        cur->next = NULL;
        cur->buffer = NULL;
        cur = next;
    }
    self->markers = NULL;
    
    Py_XDECREF(self->uobj);
    Py_XDECREF(self->encoding);
    
    self->ob_type->tp_free((PyObject *)self);
}



static PyObject *
ubuf_new(PyTypeObject *type, PyObject *args, PyObject *kdws)
{
    ubuf *self;
    
    self = (ubuf *)(type->tp_alloc(type, 0));
    if (self) {
        self->uobj = NULL;
        self->markers = NULL;
        self->flags = 0;
        self->length = self->gapstart = self->gapsize = 0;
    }
    
    return (PyObject *)self;
}



static int
ubuf_init(ubuf *self, PyObject *args, PyObject *kwds)
{
    PyObject *v = NULL, *enc = NULL, *tobefreed = NULL;
    Py_UNICODE *u1, *u2;
    Py_ssize_t l1, l2;

    static char *kwlist[] = {"text", "encoding", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OO:ubuf", kwlist, &v, &enc)) {
        goto fail_new;
    }

    if (enc) {
        if (ubuf_set_encoding(self, enc, NULL) < 0) {
            goto fail_new;
        }
    } else {
        self->encoding = PyString_FromString("utf8");
        if (!self->encoding) {
            goto fail_new;
        }
    }

    if (!ubuf_parse_textarg(self, v, &tobefreed, &u1, &l1, &u2, &l2)) {
        goto fail_new;
    }

    if (u1) {
        self->uobj = PyUnicode_FromUnicode(u1, l1);
    } else {
        self->uobj = PyUnicode_FromUnicode(NULL, 0);
    }
    
    if (!self->uobj) {
        goto fail_new;
    }

    self->str = PyUnicode_AS_UNICODE(self->uobj);
    self->gapstart = self->length = PyUnicode_GetSize(self->uobj);

    if (u2) {
        /* XXX */
    }
    
    Py_XDECREF(tobefreed);

    return 0;

fail_new:
    Py_XDECREF(tobefreed);
    
    ubuf_dealloc(self);

    return -1;
}



/* Begin ubuf get/set methods */

static int
ubuf_set_err_notallowed(ubuf *self, PyObject *value, void *closure)
{
    PyErr_SetString(PyExc_AttributeError, "attribute is not writeable");

    return 1;
}



static PyObject *
ubuf_get_changed(ubuf *self, void *closure)
{
    if (UBUF_IS_CHANGED(self)) {
        Py_RETURN_TRUE;
    }
    
    Py_RETURN_FALSE;
}



static int
ubuf_set_changed(ubuf *self, PyObject *value, void *closure)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the changed attribute");
            return -1;
    }
    if (PyObject_IsTrue(value)) {
        UBUF_SET_CHANGED(self);
    } else {
        UBUF_CLEAR_CHANGED(self);
    }

    return 0;
}



static PyObject *
ubuf_get_encoding(ubuf *self, void *closure)
{
    Py_INCREF(self->encoding);
    
    return self->encoding;
}



static PyObject *
ubuf_get_gapsize(ubuf *self, void *closure)
{
    return PyInt_FromSsize_t(self->gapsize);
}



static PyObject *
ubuf_get_gapstart(ubuf *self, void *closure)
{
    return PyInt_FromSsize_t(self->gapstart);
}



static int
ubuf_set_encoding(ubuf *self, PyObject *value, void *closure)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the encoding attribute");
            return -1;
    }
    if (!PyString_Check(value)) {
        PyErr_SetString(PyExc_TypeError,
            "The encoding attribute value must be a string");
        return -1;
    }
    
    Py_XDECREF(self->encoding);
    Py_INCREF(value);
    self->encoding = value;

    return 0;
}



static PyObject *
ubuf_get_loaned(ubuf *self, void *closure)
{
    if (UBUF_IS_LOANED(self)) {
        Py_RETURN_TRUE;
    }
    
    Py_RETURN_FALSE;
}



static PyObject *
ubuf_get_read_only(ubuf *self, void *closure)
{
    if (UBUF_IS_READONLY(self)) {
        Py_RETURN_TRUE;
    }
    
    Py_RETURN_FALSE;
}



static int
ubuf_set_read_only(ubuf *self, PyObject *value, void *closure)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the read_only attribute");
            return -1;
    }
    if (PyObject_IsTrue(value)) {
        UBUF_SET_READONLY(self);
    } else {
        UBUF_CLEAR_READONLY(self);
    }

    return 0;
}



/* Begin ubuf internal functions */

int
ubuf_makewriteable(ubuf *self)
{
    if (!UBUF_CAN_WRITE(self)) {
        if (UBUF_IS_READONLY(self)) {
            PyErr_SetString(ReadOnlyBufferError, "buffer is read-only");
            
            return 0;
        }
        
        /* see if we can recover a loaned buffer */
        if (((PyObject *)self)->ob_refcnt == 1) {
            self->flags &= ~UBUF_F_LOANED;   
        } else {
            PyErr_SetString(PyExc_RuntimeError, "Loaned Buffer Still Outstanding");
            
            return 0;
        }
    }
    
    return 1;
}



int
ubuf_gap_to(ubuf *self, Py_ssize_t i)
{
    /* assumes buffer is writeable! */
    
   if (self->gapstart != i) {
        if (i > self->length) {
            PyErr_SetString(PyExc_IndexError, "index out of range");
            
            return 0;
        }
        
        if (i > self->gapstart) {
D(fprintf(stderr, "\nGAP FORWARDS TO %d\n", i);)
            /* moving gap forwards */
            if (self->gapsize) {
D(fprintf(stderr, "memmove %d %d %d\n", self->gapstart, self->gapstart + self->gapsize, i - self->gapstart);)
                memmove(
                    &(self->str[self->gapstart]),
                    &(self->str[self->gapstart + self->gapsize]),
                    (i - self->gapstart) * sizeof(Py_UNICODE)
                );
            }
        } else {
D(fprintf(stderr, "\nGAP BACKWARDS TO %d@%d\n", self->gapsize, i);)
            /* moving gap backwards */
            if (self->gapsize) {
D(fprintf(stderr, "memmove %d %d %d\n", i + self->gapsize, i, self->gapstart - i);)
                memmove(
                    &(self->str[self->gapsize + i]),
                    &(self->str[i]),
                    (self->gapstart - i) * sizeof(Py_UNICODE)
                );
            }
        }

        self->gapstart = i;
    }
    
    return 1;
}



int
ubuf_grow(ubuf *self, Py_ssize_t grow_amt, Py_ssize_t gap_to)
{
    Py_UNICODE *newbuf;
#if 1
    /* do it the easy way */
    newbuf = PyMem_Realloc(self->str,
        (self->length + self->gapsize + grow_amt) * sizeof(Py_UNICODE));
    
    if (!newbuf) {
        return 0;
    }
    
    PyUnicode_AS_UNICODE(self->uobj) = self->str = newbuf;
    self->gapsize += grow_amt;
    
    if (!ubuf_gap_to(self, gap_to)) {
        return 0;
    }

    return 1;
#else        
    PyErr_SetString(PyExc_TypeError, "Can't grow buffer!"); /* XXX */
            
    return 0;
#endif
}



static int
ubuf_slice_indices(ubuf *self, PyObject *o, Py_ssize_t *s, Py_ssize_t *e)
{
    Py_ssize_t step, sl;
    
    if (PySlice_Check(o)) {
        if (PySlice_GetIndicesEx((PySliceObject *)o,
        self->length, s, e, &step, &sl)) {
            return 0;
        }

        if ((*e < *s) && (step > 0)) {
            *e = *s;
        }
                
        if (step != 1) {
            PyErr_SetString(PyExc_IndexError, "only a step of 1 is supported");
    
            return 0;
        }
    } else {
        *s = PyInt_AsLong(o);
        if ((*s == -1) && PyErr_Occurred()) {
            return 0;
        } else {
            /* it's an integer */
            
            if (*s < 0) {
                *s += self->length;
            }
        
            if ((*s < 0) || (*s >= self->length)) {
                PyErr_SetString(PyExc_IndexError, "index out of range");
        
                return 0;
            }

            *e = *s + 1;
        }
    }

    return 1;
}


/*
 * ubuf_parse_textarg
 *
 * this handles input arguments for replacement text, which may be:
 *  - NULL, special case deletion for setslice
 *  - a unicode object
 *  - an encodable (normally a str)
 *
 * returns 1 on success, 0 on failure
 */
int
ubuf_parse_textarg(
    ubuf *self, PyObject *v, PyObject **tobefreed,
    Py_UNICODE **v1, Py_ssize_t *l1,
    Py_UNICODE **v2, Py_ssize_t *l2
) {
    *tobefreed = NULL;
    *v1 = *v2 = NULL;
    *l1 = *l2 = 0;
    
    if (!v) {
        /* just leave replacement empty */
    } else if (PyUnicode_Check(v)) {
        *v1 = PyUnicode_AS_UNICODE(v);
        *l1 = PyUnicode_GET_SIZE(v);
    } else {
        *tobefreed = PyUnicode_FromEncodedObject(
            v, UBUF_ENCODING(self), "strict");
        if (*tobefreed) {
            *v1 = PyUnicode_AS_UNICODE(*tobefreed);
            *l1 = PyUnicode_GET_SIZE(*tobefreed);
        } else {
            return 0;
        }
    }

    return 1;
}



int
ubuf_do_cut(ubuf *self, Py_ssize_t s, Py_ssize_t e, PyObject **cut)
{
    /* assumes buffer is writeable */
    
    if (!ubuf_gap_to(self, s)) {
        return 0;
    }

    if (cut) {
        *cut = PyUnicode_FromUnicode(&(self->str[s + self->gapsize]), e - s);
    }
    
    self->gapsize += (e - s);
    
    if (cut && !*cut) {
        return 0;
    }
    
    return 1;
}



int
ubuf_assign_slice(
    ubuf *self,
    Py_ssize_t s, Py_ssize_t e,
    Py_UNICODE *u1, Py_ssize_t l1,
    Py_UNICODE *u2, Py_ssize_t l2
)
{
    Py_ssize_t deleted = e - s;
    Py_ssize_t replen = l1 + l2;
    Py_ssize_t growth = replen - deleted;

D(fprintf(stderr, "\nreplace %d:%d with %d + %d\n", s, e, l1, l2);)
D(fprintf(stderr, "deleted %d replen %d growth %d gapsize %d@%d\n", deleted, replen, growth, self->gapsize, self->gapstart);)
    if (growth <= self->gapsize) {
        if (!ubuf_gap_to(self, s)) {
            return 0;
        }
    } else {
        Py_ssize_t grow_amt = (self->length >> 4) + 64 + (growth - self->gapsize);

        if (!ubuf_grow(self, grow_amt, s)) {
            return 0;
        }
    }

    self->gapsize -= growth;
    self->length += growth;

    if (u1) {
        memcpy(&(self->str[self->gapstart]), u1, l1 * sizeof(Py_UNICODE));
        self->gapstart += l1;
    }
            
    if (u2) {
        memcpy(&(self->str[self->gapstart]), u2, l2 * sizeof(Py_UNICODE));
        self->gapstart += l2;
    }

    UBUF_SET_CHANGED(self);
    
    return 1;
}



/* Begin ubuf mapping protocol methods */

static Py_ssize_t
ubuf_mp_length(PyObject *self)
{
    return ((ubuf *)self)->length;
}



static PyObject *
ubuf_mp_subscript(PyObject *selfo, PyObject *o)
{
    Py_ssize_t s, e;
    ubuf *self = (ubuf *)selfo;
    
    if (!ubuf_slice_indices(self, o, &s, &e)) {
        return 0;
    }

    if ((s >= self->gapstart) && (e > self->gapstart)) {
        s += self->gapsize;
        e += self->gapsize;
    } else if (e > self->gapstart) {
        /* straddling the gap */
D(fprintf(stderr, "\nstraddling %d\n", e);)
        if (UBUF_IS_LOANED(self)) {
            PyErr_SetString(PyExc_AssertionError, "gap should not be in middle while loaned");

            return 0;
        }
        
        if (!ubuf_gap_to(self, e)) {
            return 0;
        }
    }

    return PyUnicode_FromUnicode(&(self->str[s]), e - s);
}



static int
ubuf_mp_ass_subscript(PyObject *selfo, PyObject *k, PyObject *v)
{
    ubuf *self = (ubuf *)selfo;
    Py_ssize_t s, e;
    Py_UNICODE *u1, *u2;
    Py_ssize_t l1, l2;
    PyObject *tobefreed;
        
    if (!ubuf_makewriteable(self)) {
        return -1;
    }

    if (!ubuf_parse_textarg(self, v, &tobefreed, &u1, &l1, &u2, &l2)) {
        return -1;
    }

D(fprintf(stderr, "\nLENS %d %d\n", l1, l2);)
    if (!ubuf_slice_indices(self, k, &s, &e)) {
        return -1;
    }

    if (!ubuf_assign_slice(self, s, e, u1, l1, u2, l2)) {
        Py_XDECREF(tobefreed);
        return -1;
    }

    Py_XDECREF(tobefreed);
    
    return 0;
}



/* Begin ubuf basic methods */

static PyObject *
ubuf_repr(PyObject *self)
{
    ubuf *u = (ubuf *)self;
    
    return PyString_FromFormat("<ubuf len %ld at %p>",
        u->length, u
    );
}



static PyObject *
ubuf_iter(PyObject *self)
{
    return PyEval_CallFunction((PyObject *)(&marker_type), "(O)", self);
}



/* Begin ubuf file-like methods */

PyObject *
ubuf_flush(ubuf *self, PyObject *args)
{
    Py_RETURN_NONE;
}
    
    
        
/* Begin ubuf add-on methods */

static PyObject *
ubuf_append(PyObject *selfo, PyObject *args)
{
    ubuf *self = (ubuf *)selfo;
    Py_UNICODE *u1, *u2;
    PyObject *v, *tobefreed;
    Py_ssize_t l1, l2;
        
    if (!PyArg_ParseTuple(args, "O", &v)) {
        return 0;
    }

    if (!ubuf_makewriteable(self)) {
        return 0;
    }

    if (!ubuf_parse_textarg(self, v, &tobefreed, &u1, &l1, &u2, &l2)) {
        return 0;
    }

    if (!ubuf_assign_slice(self, self->length, self->length, u1, l1, u2, l2)) {
        Py_XDECREF(tobefreed);
        return 0;
    }

    Py_XDECREF(tobefreed);

    Py_RETURN_NONE;
}



static PyObject *
ubuf_borrow(ubuf *self, PyObject *args)
{
    Py_INCREF(self->uobj);

    self->flags |= UBUF_F_LOANED;
        
    return self->uobj;
}



static PyMethodDef ubuf_methods[] = {
    /* file-like methods */
    {"flush",       (PyCFunction)ubuf_flush,            METH_NOARGS},
    {"write",       (PyCFunction)ubuf_append,           METH_VARARGS},
    {"xreadlines",  (PyCFunction)ubuf_iter,             METH_NOARGS},
        
    /* add-on methods */
    {"append",      (PyCFunction)ubuf_append,           METH_VARARGS},
    {"borrow",      (PyCFunction)ubuf_borrow,           METH_NOARGS},

    {NULL,          NULL}
};


static PyMethodDef ubuf_module_methods[] = {
    {NULL,          NULL}
};


static PyMemberDef ubuf_members[] = {
    {"softspace",  T_INT, offsetof(ubuf, softspace), 0, NULL},

    {NULL}
};
        


static PyGetSetDef ubuf_getset[] = {
    {"changed",     (getter)ubuf_get_changed,
                    (setter)ubuf_set_changed,
                    "has the buffer been modified?",
                    NULL},

    {"encoding",    (getter)ubuf_get_encoding,
                    (setter)ubuf_set_encoding,
                    "encoding to use for this buffer",
                    NULL},

    {"gapsize",     (getter)ubuf_get_gapsize,
                    (setter)ubuf_set_err_notallowed,
                    "size of the gap in the buffer",
                    NULL},

    {"gapstart",    (getter)ubuf_get_gapstart,
                    (setter)ubuf_set_err_notallowed,
                    "location of the start of the gap in the buffer",
                    NULL},

    {"loaned",      (getter)ubuf_get_loaned,
                    (setter)ubuf_set_err_notallowed,
                    "is the buffer loaned out?",
                    NULL},

    {"read_only",   (getter)ubuf_get_read_only,
                    (setter)ubuf_set_read_only,
                    "is the buffer marked read-only?",
                    NULL},

    {NULL}
};


static PyMappingMethods ubuf_as_mapping = {
    ubuf_mp_length,         /* mp_length        */
    ubuf_mp_subscript,      /* mp_subscript     */
    ubuf_mp_ass_subscript,  /* mp_ass_subscript */
};


PyTypeObject ubuf_type = {
    /* The ob_type field must be initialized in the module init function
     * to be portable to Windows without using C++. */
    PyObject_HEAD_INIT(NULL)
    0,                          /*ob_size*/
    "tmacs.edit.ubuf.ubuf",     /*tp_name*/
    sizeof(ubuf),               /*tp_basicsize*/
    0,                          /*tp_itemsize*/
    /* methods */
    (destructor)ubuf_dealloc,   /*tp_dealloc*/
    0,                          /*tp_print*/
    0,                          /*tp_getattr*/
    0,                          /*tp_setattr*/
    0,                          /*tp_compare*/
    ubuf_repr,                  /*tp_repr*/
    0,                          /*tp_as_number*/
    0,                          /*tp_as_sequence*/
    &ubuf_as_mapping,           /*tp_as_mapping*/
    0,                          /*tp_hash*/
    0,                          /*tp_call*/
    0,                          /*tp_str*/
    0,                          /*tp_getattro*/
    0,                          /*tp_setattro*/
    0,                          /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
    0,                          /*tp_doc*/ 
    0,                          /*tp_traverse*/ 
    0,                          /*tp_clear*/   
    0,                          /*tp_richcompare*/
    0,                          /*tp_weaklistoffset*/
    ubuf_iter,                  /*tp_iter*/ 
    0,                          /*tp_iternext*/
    ubuf_methods,               /*tp_methods*/
    ubuf_members,               /*tp_members*/
    ubuf_getset,                /*tp_getset*/
    0,                          /*tp_base*/
    0,                          /*tp_dict*/
    0,                          /*tp_descr_get*/ 
    0,                          /*tp_descr_set*/
    0,                          /*tp_dictoffset*/
    (initproc)ubuf_init,        /*tp_init*/
    PyType_GenericAlloc,        /*tp_alloc*/
    ubuf_new,                   /*tp_new*/
    _PyObject_Del,              /*tp_free*/
    0,                          /*tp_is_gc*/
};




PyMODINIT_FUNC
initubuf(void)
{
    PyObject *m, *d;

    ubuf_type.tp_new = PyType_GenericNew;
    if (PyType_Ready(&ubuf_type) < 0)
        return;
        
    m = Py_InitModule3("ubuf", ubuf_module_methods,
        "Unicode buffer-gap base type");

    Py_INCREF(&ubuf_type);
    PyModule_AddObject(m, "ubuf", (PyObject *)&ubuf_type);

    ReadOnlyBufferError = PyErr_NewException(
        "tmacs.edit.ubuf.ReadOnlyBufferError", NULL, NULL);

    Py_INCREF(ReadOnlyBufferError);
    PyModule_AddObject(m, "ReadOnlyBufferError", ReadOnlyBufferError);

    add_marker_type(m);
}
