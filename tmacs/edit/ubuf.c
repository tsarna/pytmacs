/* $Id: ubuf.c,v 1.22 2007-10-04 16:56:20 tsarna Exp $ */

/* 6440931 */

#include <Python.h>
#include <structmember.h>

#include "ubuf.h"

PyObject *ReadOnlyBufferError = NULL;
extern PyTypeObject marker_type;
PyTypeObject ubuf_type;


#if 0
#define D(x) x
#else
#define D(x) /*x*/
#endif

/* prototypes for static functions */

static int ubuf_set_encoding(ubuf *self, PyObject *value, void *closure);
static void ubuf_dealloc(ubuf *self);
static int ubuf_init(ubuf *self, PyObject *args, PyObject *kwds);
/* get/set methods */
static int ubuf_set_err_notallowed(ubuf *self, PyObject *value, void *closure);
static PyObject *ubuf_get_changed(ubuf *self, void *closure);
static int ubuf_set_changed(ubuf *self, PyObject *value, void *closure);
static PyObject *ubuf_get_encoding(ubuf *self, void *closure);
static int ubuf_set_encoding(ubuf *self, PyObject *value, void *closure);
static PyObject *ubuf_get_gapsize(ubuf *self, void *closure);
static PyObject *ubuf_get_gapstart(ubuf *self, void *closure);
static PyObject *ubuf_get_read_only(ubuf *self, void *closure);
static int ubuf_set_read_only(ubuf *self, PyObject *value, void *closure);
static PyObject *ubuf_get_tabdispwidth(ubuf *self, void *closure);
static int ubuf_set_tabdispwidth(ubuf *self, PyObject *value, void *closure);
/* mapping methods */
static Py_ssize_t ubuf_mp_length(PyObject *self);
static PyObject *ubuf_mp_subscript(PyObject *selfo, PyObject *o);
static int ubuf_mp_ass_subscript(PyObject *selfo, PyObject *k, PyObject *v);
/* basic methods */
static PyObject *ubuf_repr(PyObject *self);
static PyObject *ubuf_iter(PyObject *self);
/* file-like methods */
/* add-on methods */
static PyObject *ubuf_append(PyObject *selfo, PyObject *arg);

/* Begin ubuf create/delete methods */

static void
ubuf_dealloc(ubuf *self)
{
    marker *cur, *next;

    /* unlink all markers */
    cur = self->markers;
    while (cur) {
        next = cur->next;
        cur->next = NULL;
        cur->buffer = NULL;
        cur = next;
    }
    self->markers = NULL;
    
    Py_XDECREF(self->encoding);

    PyMem_Del(self->str);
        
    self->ob_type->tp_free((PyObject *)self);
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

    self->gapstart = self->length = 0;
    self->gapsize = (l1 + l2) + ((l1 + l2) >> 4);

    if (l1 + l2) {
        self->str = PyMem_New(Py_UNICODE, l1 + l2);
        if (self->str) {
            if (!ubuf_assign_slice(self, 0, 0, u1, l1, u2, l2)) {
                goto fail_new;
            }
            
            self->flags = 0;
        } else {
            goto fail_new;
        }
    }

    Py_XDECREF(tobefreed);

    self->tabdispwidth = 8;

    return 0;

fail_new:
    Py_XDECREF(tobefreed);
    
    ubuf_dealloc(self);

    return -1;
}


PyDoc_STRVAR(ubuf_doc,
"ubuf([text, [encoding]]) -> a unicode buffer-gap editing buffer\n\
\n\
'text' is the initial text of the buffer, as a unicode, str\n\
(encoded with the encoding specified in the second argument)\n\
or another ubuf.\n\
\n\
'encoding' is the initial value of the 'encoding' attribute of the\n\
resulting buffer, used to specify the default encoding when converting\n\
to or from byte strings.");


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



static PyObject *
ubuf_get_tabdispwidth(ubuf *self, void *closure)
{
    return PyInt_FromLong(self->tabdispwidth);
}



static int
ubuf_set_tabdispwidth(ubuf *self, PyObject *value, void *closure)
{
    long v;
    
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the tabdispwidth attribute");
            return -1;
    }

    v = PyInt_AsLong(value);
    if (v == -1 && PyErr_Occurred()) {
        return -1;
    }

    if ((v <= 0) || (v > UCHAR_MAX)) {
        PyErr_SetString(PyExc_TypeError, "tabdispwidth must be in range 1-255");
        return -1;
    }
    
    self->tabdispwidth = v;

    return 0;
}



/* Begin ubuf internal functions */

int
ubuf_makewriteable(ubuf *self)
{
    if (UBUF_IS_READONLY(self)) {
        PyErr_SetString(ReadOnlyBufferError, "buffer is read-only");
        
        return 0;
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
    newbuf = PyMem_Resize(self->str, Py_UNICODE, 
        self->length + self->gapsize + grow_amt);
    
    if (!newbuf) {
        return 0;
    }
    
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
 *  - a ubuf
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
    ubuf *u;
    
    if (!v) {
        /* just leave replacement empty */
    } else if (PyUnicode_Check(v)) {
        *v1 = PyUnicode_AS_UNICODE(v);
        *l1 = PyUnicode_GET_SIZE(v);
    } else if (ubuf_check(v)) {
        u = (ubuf *)v;
        *v1 = u->str;
        *l1 = u->gapstart;
        *v2 = &(u->str[u->gapstart + u->gapsize]);
        *l2 = u->length - u->gapstart;
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



PyObject *
ubuf_get_range(ubuf *self, Py_ssize_t s, Py_ssize_t e)
{
    if ((s >= self->gapstart) && (e > self->gapstart)) {
        s += self->gapsize;
        e += self->gapsize;
    } else if (e > self->gapstart) {
        /* straddling the gap */
D(fprintf(stderr, "\nstraddling %d\n", e);)
        
        if (!ubuf_gap_to(self, e)) {
            return 0;
        }
    }

    return PyUnicode_FromUnicode(&(self->str[s]), e - s);
}



PyObject *
ubuf_get_line(ubuf *self, Py_ssize_t *start, Py_ssize_t sz)
{
    Py_ssize_t s = *start;

    while ((*start < self->gapstart)
        && (*start < self->length)
        && ((*start - s) < sz)
    ) {
        if (Py_UNICODE_ISLINEBREAK(self->str[(*start)++])) {
            goto done;
        }
    }

    while ((*start < self->length)
        && ((*start - s) < sz)
    ) {
        if (Py_UNICODE_ISLINEBREAK(self->str[(*start)++ + self->gapsize])) {
            break;
        }
    }

done:
    return ubuf_get_range(self, s, *start);
}



Py_ssize_t
ubuf_get_line_start(ubuf *self, Py_ssize_t s)
{
    while ((s > 0) && (s >= self->gapstart)
    && !(Py_UNICODE_ISLINEBREAK(self->str[(s-1) + self->gapsize]))) {
        s--;
    }

    while ((s > 0) && (s < self->gapstart)
    && !(Py_UNICODE_ISLINEBREAK(self->str[s-1]))) {
        s--;
    }

    return s;
}



Py_ssize_t
ubuf_get_line_end(ubuf *self, Py_ssize_t s)
{
    while ((s < self->gapstart) && (s < self->length)
    && !(Py_UNICODE_ISLINEBREAK(self->str[s]))) {
        s++;
    }

    while ((s >= self->gapstart) && (s < self->length)
    && !(Py_UNICODE_ISLINEBREAK(self->str[(s) + self->gapsize]))) {
        s++;
    }

    return s;
}



#define INWORD(u, i) (Py_UNICODE_ISALNUM(UBUF_CHARAT((u), (i))))

Py_ssize_t
ubuf_get_next_words(ubuf *self, Py_ssize_t s, Py_ssize_t n)
{
    if (n > 0) {
        while (n--) {
            while ((s < self->length) && INWORD(self, s)) {
                s++;
            }
            while ((s < self->length) && !INWORD(self, s)) {
                s++;
            }
        }
    } else {
        while (n++ < 0) {
            while ((s > 0) && !INWORD(self, s-1)) {
                s--;
            }
            while ((s > 0) && INWORD(self, s-1)) {
                s--;
            }
        }
    }

    return s;
}



int
ubuf_do_truncate(ubuf *self, Py_ssize_t sz)
{
    if (!ubuf_makewriteable(self)) {
        return 0;
    }

    if (sz < 0) {
        PyErr_SetString(PyExc_IndexError, "can't truncate to negative size");
            
        return 0;
    } else if (sz > self->length) {
        PyErr_SetString(PyExc_IndexError, "can't extend buffer by truncation");
            
        return 0;
    } else if (sz < self->length) {
        return ubuf_assign_slice(self, sz, self->length, NULL, 0, NULL, 0);
    }

    return 1; /* no change */
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
    marker *m;

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

    m = self->markers;
    while (m) {
        marker_adjust(m, s, e, l1+l2);
        m = m->next;
    }
    
    UBUF_SET_CHANGED(self);
    
    return 1;
}



Py_ssize_t
ubuf_char_display_width(ubuf *u, Py_UNICODE c)
{
    /* XXX */
    
    return 1;
}



Py_ssize_t
ubuf_get_display_col(ubuf *self, Py_ssize_t p)
{
    Py_ssize_t s, col = 0;
    Py_UNICODE c;
    
    s = ubuf_get_line_start(self, p);
    
    while (s < p) {
        c = UBUF_CHARAT(self, s);

        if (c == (Py_UNICODE)'\t') {
            col = ((col / self->tabdispwidth) + 1) * self->tabdispwidth;
        } else if (Py_UNICODE_ISLINEBREAK(c)) {
            break;
        } else {
            col += ubuf_char_display_width(self, c);
        }
        
        s++;
    }
    
    return col;
}



Py_ssize_t
ubuf_to_display_col(ubuf *self, Py_ssize_t s, Py_ssize_t tocol)
{
    Py_ssize_t i, col = 0;
    Py_UNICODE c;
    
    while (s < self->length) {
        c = UBUF_CHARAT(self, s);

        if (c == (Py_UNICODE)'\t') {
            col = ((col / self->tabdispwidth) + 1) * self->tabdispwidth;
        } else if (Py_UNICODE_ISLINEBREAK(c)) {
            break;
        } else {
            col += ubuf_char_display_width(self, c);
        }
        
        if (col <= tocol) {
            s++;
        } else {
            break;
        }
    }
    
    return s;
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

    return ubuf_get_range(self, s, e);
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


PyDoc_STRVAR(ubuf_xreadlines_doc,
"This is an alias for iter() on the buffer, for compatability with\n\
the file-like interface. It returns an iterator over lines of the\n\
file.");
    
        

/* Begin ubuf file-like methods */

PyObject *
ubuf_flush(ubuf *self, PyObject *args)
{
    Py_RETURN_NONE;
}

PyDoc_STRVAR(ubuf_flush_doc,
"This is a no-op for file-like interface compatability.");
    
        
/* Begin ubuf add-on methods */

static PyObject *
ubuf_append(PyObject *selfo, PyObject *v)
{
    ubuf *self = (ubuf *)selfo;
    Py_UNICODE *u1, *u2;
    PyObject *tobefreed;
    Py_ssize_t l1, l2;
        
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


PyDoc_STRVAR(ubuf_append_doc,
"Append the text argument (either a unicode, a string the ubuf's\n\
default encoding, or another ubuf) to the buffer. The buffer must\n\
not be read_only.");



static PyMethodDef ubuf_methods[] = {
    /* file-like methods */
    {"flush",       (PyCFunction)ubuf_flush,    METH_NOARGS, ubuf_flush_doc},
    {"write",       (PyCFunction)ubuf_append,   METH_O, ubuf_append_doc},
    {"xreadlines",  (PyCFunction)ubuf_iter,     METH_NOARGS, ubuf_xreadlines_doc},
        
    /* add-on methods */
    {"append",      (PyCFunction)ubuf_append,   METH_O, ubuf_append_doc},

    {NULL,          NULL}
};


static PyMethodDef ubuf_module_methods[] = {
    {NULL,          NULL}
};


static PyMemberDef ubuf_members[] = {
    {"softspace",  T_INT, offsetof(ubuf, softspace), 0,
    "Used by the print statement for bookkeeping"},

    {NULL}
};



static PyGetSetDef ubuf_getset[] = {
    {"changed",         (getter)ubuf_get_changed,
                        (setter)ubuf_set_changed,
                        "Has the buffer been modified?",
                        NULL},

    {"encoding",        (getter)ubuf_get_encoding,
                        (setter)ubuf_set_encoding,
                        "Default encoding to use for this buffer when converting\nto or from byte strings",
                        NULL},

    {"gapsize",         (getter)ubuf_get_gapsize,
                        (setter)ubuf_set_err_notallowed,
                        "The size of the gap in the buffer (mainly intended for debugging).",
                        NULL},

    {"gapstart",        (getter)ubuf_get_gapstart,
                        (setter)ubuf_set_err_notallowed,
                        "The location of the start of the gap in the buffer\n(mainly intended for debugging).",
                        NULL},

    {"read_only",       (getter)ubuf_get_read_only,
                        (setter)ubuf_set_read_only,
                        "Is the buffer marked read-only?",
                        NULL},

    {"tabdispwidth",    (getter)ubuf_get_tabdispwidth,
                        (setter)ubuf_set_tabdispwidth,
                        "How many columns does a tab represent?",
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
    ubuf_doc,                   /*tp_doc*/ 
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
    0,                          /*tp_new*/
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
        "Unicode buffer-gap editing buffer type");

    Py_INCREF(&ubuf_type);
    PyModule_AddObject(m, "ubuf", (PyObject *)&ubuf_type);

    ReadOnlyBufferError = PyErr_NewException(
        "tmacs.edit.ubuf.ReadOnlyBufferError", NULL, NULL);

    Py_INCREF(ReadOnlyBufferError);
    PyModule_AddObject(m, "ReadOnlyBufferError", ReadOnlyBufferError);

    add_marker_type(m);
}
