/* $Id: marker.c,v 1.16 2007-08-18 19:05:44 tsarna Exp $ */

#include <Python.h>
#include <structmember.h>

#include "ubuf.h"

#ifndef max
#define max(x,y) ((x) > (y) ? (x) : (y))
#define min(x,y) ((x) < (y) ? (x) : (y))
#endif

extern PyObject *ReadOnlyBufferError;
extern PyTypeObject ubuf_type;
static PyTypeObject marker_type;

#define D(x) /*x*/

/* prototypes for static functions */

static void marker_dealloc(marker *self);
static PyObject *marker_new(PyTypeObject *type, PyObject *args, PyObject *kdws);
static int marker_init(marker *self, PyObject *args, PyObject *kwds);
/* link/unlink */
static void marker_link_buffer(marker *self, ubuf *buf);
static void marker_unlink_buffer(marker *self);
/* internal */
static int marker_to(marker *self, Py_ssize_t v);
static int marker_start(marker *self, Py_ssize_t v);
static int marker_end(marker *self, Py_ssize_t v);
static ubuf *marker_makewriteable(marker *self);
/* get/set */
static PyObject *marker_get_buffer(marker *self, void *closure);
static int marker_set_buffer(marker *self, PyObject *value, void *closure);
static PyObject *marker_get_changed(marker *self, void *closure);
static int marker_set_changed(marker *self, PyObject *value, void *closure);
static PyObject *marker_get_end(marker *self, void *closure);
static int marker_set_end(marker *self, PyObject *value, void *closure);
static PyObject *marker_get_start(marker *self, void *closure);
static int marker_set_start(marker *self, PyObject *value, void *closure);
/* sequence protocol */
static Py_ssize_t marker_sq_length(PyObject *self);
static int marker_sq_contains(PyObject *self, PyObject *other);
/* numeric protocol */
static PyObject *marker_nb_add(PyObject *self, PyObject *other);
static PyObject *marker_nb_subtract(PyObject *self, PyObject *other);
static PyObject *marker_nb_negative(PyObject *self);
static int marker_nb_coerce(PyObject **pv, PyObject **pw);
static PyObject *marker_nb_int(PyObject *self);
static PyObject *marker_nb_long(PyObject *self);
static PyObject *marker_nb_float(PyObject *self);
static PyObject *marker_nb_inplace_add(PyObject *self, PyObject *other);
static PyObject *marker_nb_inplace_subtract(PyObject *self, PyObject *other);
/* basic methods */
static PyObject *marker_repr(PyObject *self);
static PyObject *marker_richcompare(PyObject *v, PyObject *w, int op);
/* file-like methods */
static PyObject *marker_seek(marker *self, PyObject *args);
static PyObject *marker_tell(marker *self, PyObject *args);
static PyObject *marker_write(marker *self, PyObject *args);
static PyObject *marker_writelines(marker *self, PyObject *args);


/* Begin marker create/delete methods */

static void
marker_dealloc(marker *self)
{
    marker_unlink_buffer(self);
    
    self->ob_type->tp_free((PyObject *)self);
}



static PyObject *
marker_new(PyTypeObject *type, PyObject *args, PyObject *kdws)
{
    marker *self;
    
    self = (marker *)(type->tp_alloc(type, 0));
    if (self) {
        self->start = self->end = 0;
        self->flags = 0;
        self->buffer = NULL;
        self->next = NULL;
    }
    
    return (PyObject *)self;
}



static int
marker_init(marker *self, PyObject *args, PyObject *kwds)
{
    ubuf *b = NULL;
    Py_ssize_t s = 0, e = 0;

    static char *kwlist[] = {"buffer", "start", "end", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|Onn:marker", kwlist,
    &b, &s, &e)) {
        goto fail_new;
    }

    if (b) {
        if (!ubuf_check(b)) {
            PyErr_SetString(PyExc_TypeError,
                "buffer must be a ubuf subclass");
            goto fail_new;
        }
        marker_link_buffer(self, (ubuf *)b);

        if (s > b->length) {
            s = b->length;
        }
        if (s < 0) {
            s += b->length;
        }
        if (s < 0) {
            s = 0;
        }

        if (e > b->length) {
            e = b->length;
        }
        if (e < 0) {
            e += b->length;
        }
        if (e < 0) {
            e = 0;
        }
        
        if (e < s) {
            e = s;
        }
            
        self->start = s;
        self->end = e;
    }

    return 0;

fail_new:
    marker_dealloc(self);

    return -1;
}



/* Begin marker buffer link/unlink */

static void
marker_link_buffer(marker *self, ubuf *buf)
{
    /* add to linked list */
    self->next = buf->markers;
    buf->markers = self;

    /* and point to the buffer */ 
    self->buffer = buf;

    /* reset changed and buffer pointers */
    self->start = self->end = 0;
    self->flags = 0;
}



static void
marker_unlink_buffer(marker *self)
{
    ubuf *buf;

    buf = self->buffer;
    if (buf) {
        self->buffer = NULL;

        if (buf->markers == self) {
            buf->markers = self->next;
        } else {
            marker *cur = buf->markers;
            while (cur->next != self) {
                cur = cur->next;
            }
            cur->next = self->next;
        }
        
        self->next = NULL;
    }

    self->start = self->end = 0;
    self->flags = 0;
}


/* Begin marker internal methods */

static int
marker_to(marker *self, Py_ssize_t v)
{
    if (self->buffer == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot modify when not linked to a buffer");
        return 0;
    }
    
    if (v > self->buffer->length) {
        v = self->buffer->length;
    } else if (v < 0) {
        v = 0;
    }            

    self->start = self->end = v;
    
    return 1;
}



static int
marker_start(marker *self, Py_ssize_t v)
{
    if (self->buffer == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot modify when not linked to a buffer");
        return 0;
    }
    
    if (v > self->buffer->length) {
        v = self->buffer->length;
    } else if (v < 0) {
        v += self->buffer->length;
    }
    if (v < 0) {
        v = 0;
    }            

    if (v > self->end) {
        self->end = v;
    }
    
    self->start = v;
                
    return 1;
}



static int
marker_end(marker *self, Py_ssize_t v)
{
    if (self->buffer == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot modify when not linked to a buffer");
        return 0;
    }
    
    if (v > self->buffer->length) {
        v = self->buffer->length;
    } else if (v < 0) {
        v += self->buffer->length;
    }
    if (v < 0) {
        v = 0;
    }            

    if (v < self->start) {
        v = self->start;
    }

    self->end = v;
                
    return 1;
}



static ubuf *
marker_makewriteable(marker *self)
{
    ubuf *u = self->buffer;
    
    if (!u) {
        PyErr_SetString(PyExc_TypeError, "Cannot modify when not linked to a buffer");
        return 0;
    }
    
    if (!ubuf_makewriteable(self->buffer)) {
        return 0;
    }
    
    return u;
}



/* Begin marker get/set methods */

static PyObject *
marker_get_buffer(marker *self, void *closure)
{
    if (self->buffer) {
        Py_INCREF(self->buffer);
    
        return (PyObject *)self->buffer;
    } else {
        Py_RETURN_NONE;
    }
}



static int
marker_set_buffer(marker *self, PyObject *value, void *closure)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the buffer attribute");
            return -1;
    }
    if (!ubuf_check(value)) {
        PyErr_SetString(PyExc_TypeError,
            "The buffer attribute value must be a ubuf subclass");
        return -1;
    }
    
    marker_unlink_buffer(self);
    marker_link_buffer(self, (ubuf *)value);

    return 0;
}



static PyObject *
marker_get_changed(marker *self, void *closure)
{
    if (MARKER_IS_CHANGED(self)) {
        Py_RETURN_TRUE;
    }
    
    Py_RETURN_FALSE;
}



static int
marker_set_changed(marker *self, PyObject *value, void *closure)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the changed attribute");
            return -1;
    }
    if (PyObject_IsTrue(value)) {
        MARKER_SET_CHANGED(self);
    } else {
        MARKER_CLEAR_CHANGED(self);
    }

    return 0;
}



static PyObject *
marker_get_end(marker *self, void *closure)
{
    return PyInt_FromSsize_t(self->end);
}



static int
marker_set_end(marker *self, PyObject *value, void *closure)
{
    Py_ssize_t v;
    
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the end attribute");
            return -1;
    }
    v = PyNumber_AsSsize_t(value, PyExc_IndexError);
    if (v == -1 && PyErr_Occurred()) {
        return -1;
    }
    
    if (!marker_end(self, v)) {
        return -1;
    }

    return 0;
}



static PyObject *
marker_get_start(marker *self, void *closure)
{
    return PyInt_FromSsize_t(self->start);
}



static int
marker_set_start(marker *self, PyObject *value, void *closure)
{
    Py_ssize_t v;
    
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the start attribute");
            return -1;
    }
    v = PyNumber_AsSsize_t(value, PyExc_IndexError);
    if (v == -1 && PyErr_Occurred()) {
        return -1;
    }
    
    if (!marker_start(self, v)) {
        return -1;
    }

    return 0;
}



/* Begin marker sequence methods */

static Py_ssize_t
marker_sq_length(PyObject *self)
{
    marker *m = (marker *)self;
    
    return m->end - m->start;
}




static int
marker_sq_contains(PyObject *self, PyObject *other)
{
    marker *m = (marker *)self;
    Py_ssize_t v;
    
    if (marker_check(other)) {
        marker *o = (marker *)other;
        
        if ((o->start >= m->start)
        &&  (o->start <= m->end)
        &&  (o->end >= m->start)
        &&  (o->end <= m->end)) {
            return 1;
        }
    } else {
        v = PyNumber_AsSsize_t(other, PyExc_TypeError);
        if (v == -1 && PyErr_Occurred()) {
            return -1;
        }
        
        if ((v >= m->start) && (v <= m->end)) {
            return 1;
        }
    }
    
    return 0;
}



/* Begin marker numeric methods */

static PyObject *
marker_nb_add(PyObject *self, PyObject *other)
{
    marker *m = (marker *)self, *o = (marker *)other;
    
    return PyInt_FromSsize_t(m->start + o->start);
}



static PyObject *
marker_nb_subtract(PyObject *self, PyObject *other)
{
    marker *m = (marker *)self, *o = (marker *)other;
    
    return PyInt_FromSsize_t(m->start - o->start);
}



static PyObject *
marker_nb_negative(PyObject *self)
{
    return PyInt_FromSsize_t(- (((marker *)self)->start));
}



static int
marker_nb_coerce(PyObject **pv, PyObject **pw)
{
    marker *m = (marker *)(*pv);

    if (PyInt_Check(*pw)) {
        *pv = PyInt_FromSsize_t(m->start);
        Py_INCREF(*pw);
        return 0;
    }
    else if (PyLong_Check(*pw)) {
        *pv = PyLong_FromLong(m->start);
        Py_INCREF(*pw);
        return 0;
    }
    else if (PyFloat_Check(*pw)) {
        *pv = PyFloat_FromDouble((double)(m->start));
        Py_INCREF(*pw);
        return 0;
    }

    return 1; /* Can't do it */
}



static PyObject *
marker_nb_int(PyObject *self)
{
    return PyInt_FromSsize_t(((marker *)self)->start);
}



static PyObject *
marker_nb_long(PyObject *self)
{
    return PyLong_FromLong((long)(((marker *)self)->start));
}



static PyObject *
marker_nb_float(PyObject *self)
{
        return PyFloat_FromDouble((double)(((marker *)self)->start));
}



static PyObject *
marker_nb_inplace_add(PyObject *self, PyObject *other)
{
    marker *m = (marker *)self;
    Py_ssize_t v;
    
    v = PyNumber_AsSsize_t(other, PyExc_IndexError);
    if (v == -1 && PyErr_Occurred()) {
        return 0;
    }
    
    if (!marker_to(m, m->start + v)) {
        return 0;
    }
    
    Py_INCREF(self);
    
    return self;
}



static PyObject *
marker_nb_inplace_subtract(PyObject *self, PyObject *other)
{
    marker *m = (marker *)self;
    Py_ssize_t v;
    
    v = PyNumber_AsSsize_t(other, PyExc_IndexError);
    if (v == -1 && PyErr_Occurred()) {
        return 0;
    }
    
    if (!marker_to(m, m->start - v)) {
        return 0;
    }
    
    Py_INCREF(self);
    
    return self;
}



/* Begin marker basic methods */

static PyObject *
marker_repr(PyObject *self)
{
    marker *m = (marker *)self;
    PyObject *r, *br = NULL;
    char *bufrep = NULL;
    
    if (m->buffer) {
        br = PyObject_Repr((PyObject *)(m->buffer));
        if (!br) {
            return NULL;
        }
        
        bufrep = PyString_AsString(br);
    } else {
        bufrep = "(no buffer)";
    }
    
    r = PyString_FromFormat("<%schanged marker %ld..%ld %s%s at %p>",
        MARKER_IS_CHANGED(m) ? "" : "un",     
        (long)(m->start), (long)(m->end),
        br ? "of " : "", bufrep, self
    );
    
    Py_XDECREF(br);
    
    return r; 
}



static PyObject *
marker_richcompare(PyObject *v, PyObject *w, int op)
{
    Py_ssize_t vs, ws;
    int cmp;

    if (marker_check(v)) {
        vs = ((marker *)v)->start;
    } else {
        vs = PyNumber_AsSsize_t(v, PyExc_TypeError);
        if (vs == -1 && PyErr_Occurred()) {
            PyErr_Clear();
            Py_INCREF(Py_NotImplemented);
            return Py_NotImplemented;
        }
    }

    if (marker_check(w)) {
        ws = ((marker *)w)->start;
    } else {
        ws = PyNumber_AsSsize_t(w, PyExc_TypeError);
        if (ws == -1 && PyErr_Occurred()) {
            PyErr_Clear();
            Py_INCREF(Py_NotImplemented);
            return Py_NotImplemented;
        }
    }
    
    switch (op) {
        case Py_LT: cmp = vs <  ws; break;
        case Py_LE: cmp = vs <= ws; break;
        case Py_EQ: cmp = vs == ws; break;
        case Py_NE: cmp = vs != ws; break;
        case Py_GT: cmp = vs >  ws; break;
        case Py_GE: cmp = vs >= ws; break;
        default: return NULL; /* cannot happen */
    }
    
    if (cmp) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }
}



/* Begin marker file-like methods */

static PyObject *
marker_seek(marker *self, PyObject *args)
{
    marker *m = (marker *)self;
    Py_ssize_t off;
    int r, whence = 0;
    
    if (!PyArg_ParseTuple(args, "n|i:seek", &off, &whence)) {
        return 0; 
    }
                    
    if ((whence < 0) || (whence > 2)) {
        PyErr_SetString(PyExc_IOError, "invalid whence argument value");
        return 0;
    }
    
    switch (whence) {
    case 0:
        r = marker_to(m, off);
        break;
    case 1:
        r = marker_to(m, m->start + off);
        break;
    case 2:
        if (m->buffer == NULL) {
            PyErr_SetString(PyExc_TypeError, "Cannot modify when not linked to a buffer");
            r = 0;
        } else {
            r = marker_to(m, m->buffer->length + off);
        }
        break;
    }
    
    if (r) {
        Py_RETURN_NONE;
    } else {
        return 0;
    }
}



static PyObject *
marker_tell(marker *self, PyObject *args)
{
    return PyInt_FromSsize_t(((marker *)self)->start);
}



static PyObject *
marker_write(marker *self, PyObject *args)
{
    Py_UNICODE *u1, *u2;
    PyObject *v, *tobefreed;
    Py_ssize_t l1, l2, np;
    ubuf *u;
    
    if (!PyArg_ParseTuple(args, "O", &v)) {
        return 0;
    }

    if (!(u = marker_makewriteable(self))) {
        return 0;
    }

    if (!ubuf_parse_textarg(u, v, &tobefreed, &u1, &l1, &u2, &l2)) {
        return 0;
    }

    np = self->start + l1 + l2;
    if (!ubuf_assign_slice(u, self->start, min(np, u->length), u1, l1, u2, l2)) {
        Py_XDECREF(tobefreed);
        return 0;
    }
                                
    Py_XDECREF(tobefreed);

    marker_to(self, np);
        
    Py_RETURN_NONE;
}



static PyObject *
marker_writelines(marker *self, PyObject *args)
{
    Py_UNICODE *u1, *u2;
    PyObject *v, *line = NULL, *tobefreed = NULL, *it = NULL;
    Py_ssize_t l1, l2, np;
    ubuf *u;
    
    if (!PyArg_ParseTuple(args, "O", &v)) {
        goto error;
    }

    it = PyObject_GetIter(v);
    if (!it) {
        PyErr_SetString(PyExc_TypeError, "writelines() requires an iterable argument");
        goto error;
    }

    if (!(u = marker_makewriteable(self))) {
        goto error;
    }

    while (1) {
        line = PyIter_Next(it);
        if (!line) {
            if (PyErr_Occurred()) {
                goto error;
            } else {
                break;
            }
        }

        if (!ubuf_parse_textarg(u, line, &tobefreed, &u1, &l1, &u2, &l2)) {
            goto error;
        }

        np = self->start + l1 + l2;

        if (!ubuf_assign_slice(u, self->start, min(np, u->length), u1, l1, u2, l2)) {
            goto error;
        }

        Py_XDECREF(tobefreed);
        tobefreed = NULL;
        Py_DECREF(line);
        line = NULL;

        marker_to(self, np);
    }
    
    Py_XDECREF(it);
    
    Py_RETURN_NONE;

error:
    Py_XDECREF(line);
    Py_XDECREF(tobefreed);
    Py_XDECREF(it);

    return 0;    
}



/* begin type structures */

static PyMethodDef marker_methods[] = {
    /* file-like methods */
                    /* flush is a no-op so we can share it */
    {"flush",      (PyCFunction)ubuf_flush,             METH_NOARGS},

    {"seek",       (PyCFunction)marker_seek,            METH_VARARGS},
    {"tell",       (PyCFunction)marker_tell,            METH_NOARGS},
    {"write",      (PyCFunction)marker_write,           METH_VARARGS},
    {"writelines", (PyCFunction)marker_writelines,      METH_VARARGS},

    {NULL,          NULL}
};


static PySequenceMethods marker_as_sequence = {   
    marker_sq_length,       /* sq_length */
    0,                      /* sq_concat */
    0,                      /* sq_repeat */
    0,                      /* sq_item */
    0,                      /* sq_slice */
    0,                      /* sq_ass_item */
    0,                      /* sq_ass_slice */
    marker_sq_contains,     /* sq_contains */
    0,                      /* sq_inplace_concat */
    0,                      /* sq_inplace_repeat */
};



static PyMemberDef marker_members[] = {
    {"softspace",  T_INT, offsetof(marker, softspace), 0, NULL},
    
    
    {NULL}
};



static PyGetSetDef marker_getset[] = {
    {"buffer",      (getter)marker_get_buffer,
                    (setter)marker_set_buffer,
                    "buffer this marker is for",
                    NULL},

    {"changed",     (getter)marker_get_changed,
                    (setter)marker_set_changed,
                    "Have changes occured within marked range?",
                    NULL},

    {"end",         (getter)marker_get_end,
                    (setter)marker_set_end,
                    "end of marked range",
                    NULL},

    {"start",       (getter)marker_get_start,
                    (setter)marker_set_start,
                    "end of marked range",
                    NULL},

    {NULL}
};


static PyNumberMethods marker_as_number = {
    marker_nb_add,              /*nb_add*/   
    marker_nb_subtract,         /*nb_subtract*/
    0,                          /*nb_multiply*/
    0,                          /*nb_divide*/
    0,                          /*nb_remainder*/
    0,                          /*nb_divmod*/
    0,                          /*nb_power*/
    marker_nb_negative,         /*nb_negative*/
    marker_nb_int,              /*nb_positive*/
    marker_nb_int,              /*nb_absolute*/
    0,                          /*nb_nonzero*/
    0,                          /*nb_invert*/
    0,                          /*nb_lshift*/
    0,                          /*nb_rshift*/
    0,                          /*nb_and*/
    0,                          /*nb_xor*/
    0,                          /*nb_or*/
    marker_nb_coerce,           /*nb_coerce*/  
    marker_nb_int,              /*nb_int*/
    marker_nb_long,             /*nb_long*/
    marker_nb_float,            /*nb_float*/   
    0,                          /*nb_oct*/   
    0,                          /*nb_hex*/   
    marker_nb_inplace_add,      /*nb_inplace_add*/
    marker_nb_inplace_subtract, /*nb_inplace_subtract*/
    0,                          /*nb_inplace_multiply*/
    0,                          /*nb_inplace_divide*/
    0,                          /*nb_inplace_remainder*/
    0,                          /*nb_inplace_power*/
    0,                          /*nb_inplace_lshift*/
    0,                          /*nb_inplace_rshift*/
    0,                          /*nb_inplace_and*/
    0,                          /*nb_inplace_xor*/
    0,                          /*nb_inplace_or*/ 
    0,                          /*nb_floor_divide*/  
    0,                          /*nb_true_divide*/
    0,                          /*nb_inplace_floor_divide*/
    0,                          /*nb_inplace_true_divide*/
    marker_nb_int,              /*nb_index*/
};


static PyTypeObject marker_type = {
    /* The ob_type field must be initialized in the module init function
     * to be portable to Windows without using C++. */
    PyObject_HEAD_INIT(NULL)
    0,                          /*ob_size*/
    "tmacs.edit.ubuf.marker",   /*tp_name*/
    sizeof(marker),             /*tp_basicsize*/
    0,                          /*tp_itemsize*/
    /* methods */
    (destructor)marker_dealloc, /*tp_dealloc*/
    0,                          /*tp_print*/
    0,                          /*tp_getattr*/
    0,                          /*tp_setattr*/
    0,                          /*tp_compare*/
    marker_repr,                /*tp_repr*/
    &marker_as_number,          /*tp_as_number*/
    &marker_as_sequence,        /*tp_as_sequence*/
    0,                          /*tp_as_mapping*/
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
    marker_richcompare,         /*tp_richcompare*/
    0,                          /*tp_weaklistoffset*/
    0,                          /*tp_iter*/ 
    0,                          /*tp_iternext*/
    marker_methods,             /*tp_methods*/
    marker_members,             /*tp_members*/
    marker_getset,              /*tp_getset*/
    0,                          /*tp_base*/
    0,                          /*tp_dict*/
    0,                          /*tp_descr_get*/ 
    0,                          /*tp_descr_set*/
    0,                          /*tp_dictoffset*/
    (initproc)marker_init,      /*tp_init*/
    PyType_GenericAlloc,        /*tp_alloc*/
    marker_new,                 /*tp_new*/
    _PyObject_Del,              /*tp_free*/
    0,                          /*tp_is_gc*/
};




void
add_marker_type(PyObject *module)
{
    marker_type.tp_new = PyType_GenericNew;
    if (PyType_Ready(&marker_type) < 0)
        return;
        
    Py_INCREF(&marker_type);
    PyModule_AddObject(module, "marker", (PyObject *)&marker_type);
}
