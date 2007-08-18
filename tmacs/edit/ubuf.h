/* $Id: ubuf.h,v 1.4 2007-08-18 18:11:00 tsarna Exp $ */

typedef struct marker marker;

#define ubuf_check(op) PyObject_TypeCheck(op, &ubuf_type)
#define marker_check(op) PyObject_TypeCheck(op, &marker_type)

typedef struct {
    PyObject_HEAD

    Py_UNICODE         *str;
    PyObject           *uobj;
    PyObject           *encoding;
    marker             *markers;
    Py_ssize_t          length;     /* used size */
    Py_ssize_t          gapstart;   /* where gap is */
    Py_ssize_t          gapsize;    /* how much gap is left */
    unsigned int        flags;      /* flags */
#define UBUF_F_CHANGED      0x01
#define UBUF_F_LOANED       0x02
#define UBUF_F_READONLY     0x04
} ubuf;

#define UBUF_ENCODING(u)     PyString_AsString((u)->encoding)

#define UBUF_CAN_WRITE(u)    (!((u)->flags & (UBUF_F_READONLY|UBUF_F_LOANED)))

#define UBUF_IS_CHANGED(u)      ((u)->flags & (UBUF_F_CHANGED))
#define UBUF_SET_CHANGED(u)     ((u)->flags |= UBUF_F_CHANGED)
#define UBUF_CLEAR_CHANGED(u)   ((u)->flags &= ~UBUF_F_CHANGED)

#define UBUF_IS_LOANED(u)       ((u)->flags & (UBUF_F_LOANED))
#define UBUF_SET_LOANED(u)      ((u)->flags |= UBUF_F_LOANED)
#define UBUF_CLEAR_LOANED(u)    ((u)->flags &= ~UBUF_F_LOANED)

#define UBUF_IS_READONLY(u)     ((u)->flags & (UBUF_F_READONLY))
#define UBUF_SET_READONLY(u)    ((u)->flags |= UBUF_F_READONLY)
#define UBUF_CLEAR_READONLY(u)  ((u)->flags &= ~UBUF_F_READONLY)


struct marker {
    PyObject_HEAD

    ubuf           *buffer;
    marker         *next;

    Py_ssize_t      start;
    Py_ssize_t      end; 

    unsigned int    flags;      /* flags */
#define MARKER_F_CHANGED        0x01
    int             softspace;
};

#define MARKER_IS_CHANGED(m)      ((m)->flags & (MARKER_F_CHANGED))
#define MARKER_SET_CHANGED(m)     ((m)->flags |= MARKER_F_CHANGED)
#define MARKER_CLEAR_CHANGED(m)   ((m)->flags &= ~MARKER_F_CHANGED)

/* ubuf methods */

int ubuf_makewriteable(ubuf *self);
int ubuf_gap_to(ubuf *self, Py_ssize_t i);
int ubuf_grow(ubuf *self, Py_ssize_t grow_amt, Py_ssize_t gap_to);
static int ubuf_slice_indices(ubuf *self, PyObject *o, Py_ssize_t *s, Py_ssize_t *e);
int ubuf_parse_textarg(ubuf *self, PyObject *v, PyObject **tobefreed, Py_UNICODE **v1, Py_ssize_t *l1, Py_UNICODE **v2, Py_ssize_t *l2);
int ubuf_do_cut(ubuf *self, Py_ssize_t s, Py_ssize_t e, PyObject **cut);
int ubuf_assign_slice(ubuf *self, Py_ssize_t s, Py_ssize_t e, Py_UNICODE *u1, Py_ssize_t l1, Py_UNICODE *u2, Py_ssize_t l2);
/* shared methods */
PyObject *ubuf_flush(ubuf *self, PyObject *args);

/* marker methods */

void add_marker_type(PyObject *module);
