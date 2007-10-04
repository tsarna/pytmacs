/* $Id: ubuf.h,v 1.15 2007-10-04 16:56:20 tsarna Exp $ */

typedef struct marker marker;

#define ubuf_check(op) PyObject_TypeCheck(op, &ubuf_type)
#define marker_check(op) PyObject_TypeCheck(op, &marker_type)

typedef struct {
    PyObject_HEAD

    Py_UNICODE         *str;
    PyObject           *encoding;
    marker             *markers;
    Py_ssize_t          length;     /* used size */
    Py_ssize_t          gapstart;   /* where gap is */
    Py_ssize_t          gapsize;    /* how much gap is left */
    unsigned int        flags;      /* flags */
#define UBUF_F_CHANGED      0x01
#define UBUF_F_READONLY     0x02
    int                 softspace;
    unsigned char       tabdispwidth;
} ubuf;

#define UBUF_ENCODING(u)     PyString_AsString((u)->encoding)

#define UBUF_IS_CHANGED(u)      ((u)->flags & (UBUF_F_CHANGED))
#define UBUF_SET_CHANGED(u)     ((u)->flags |= UBUF_F_CHANGED)
#define UBUF_CLEAR_CHANGED(u)   ((u)->flags &= ~UBUF_F_CHANGED)

#define UBUF_IS_READONLY(u)     ((u)->flags & (UBUF_F_READONLY))
#define UBUF_SET_READONLY(u)    ((u)->flags |= UBUF_F_READONLY)
#define UBUF_CLEAR_READONLY(u)  ((u)->flags &= ~UBUF_F_READONLY)

#define UBUF_CHARAT(u, i) \
    ((i)>=((u)->gapstart) ? (u)->str[(i)+((u)->gapsize)] : (u)->str[i])

struct marker {
    PyObject_HEAD

    ubuf           *buffer;
    marker         *next;

    Py_ssize_t      start;
    Py_ssize_t      end; 

    unsigned int    flags;      /* flags */
#define MARKER_F_CHANGED        0x01
#define MARKER_F_LASTKILL       0x02

    Py_ssize_t      colseek;
    
    int             softspace;
};

#define MARKER_IS_CHANGED(m)      ((m)->flags & (MARKER_F_CHANGED))
#define MARKER_SET_CHANGED(m)     ((m)->flags |= MARKER_F_CHANGED)
#define MARKER_CLEAR_CHANGED(m)   ((m)->flags &= ~MARKER_F_CHANGED)

#define MARKER_IS_LASTKILL(m)      ((m)->flags & (MARKER_F_LASTKILL))
#define MARKER_SET_LASTKILL(m)     ((m)->flags |= MARKER_F_LASTKILL)
#define MARKER_CLEAR_LASTKILL(m)   ((m)->flags &= ~MARKER_F_LASTKILL)

/* ubuf methods */

int ubuf_makewriteable(ubuf *self);
int ubuf_gap_to(ubuf *self, Py_ssize_t i);
int ubuf_grow(ubuf *self, Py_ssize_t grow_amt, Py_ssize_t gap_to);
static int ubuf_slice_indices(ubuf *self, PyObject *o, Py_ssize_t *s, Py_ssize_t *e);
int ubuf_parse_textarg(ubuf *self, PyObject *v, PyObject **tobefreed, Py_UNICODE **v1, Py_ssize_t *l1, Py_UNICODE **v2, Py_ssize_t *l2);
int ubuf_assign_slice(ubuf *self, Py_ssize_t s, Py_ssize_t e, Py_UNICODE *u1, Py_ssize_t l1, Py_UNICODE *u2, Py_ssize_t l2);
int ubuf_do_truncate(ubuf *self, Py_ssize_t sz);
int ubuf_do_cut(ubuf *self, Py_ssize_t s, Py_ssize_t e, PyObject **cut);
PyObject *ubuf_get_range(ubuf *self, Py_ssize_t s, Py_ssize_t e);
PyObject *ubuf_get_line(ubuf *self, Py_ssize_t *start, Py_ssize_t sz);
Py_ssize_t ubuf_get_line_start(ubuf *self, Py_ssize_t s);
Py_ssize_t ubuf_get_line_end(ubuf *self, Py_ssize_t s);
Py_ssize_t ubuf_get_next_words(ubuf *self, Py_ssize_t s, Py_ssize_t n);
Py_ssize_t ubuf_char_display_width(ubuf *u, Py_UNICODE c);
Py_ssize_t ubuf_get_display_col(ubuf *self, Py_ssize_t p);
Py_ssize_t ubuf_to_display_col(ubuf *self, Py_ssize_t s, Py_ssize_t tocol);


/* shared methods */
PyObject *ubuf_flush(ubuf *self, PyObject *args);

/* marker methods */

void add_marker_type(PyObject *module);
void marker_adjust(marker *self, Py_ssize_t s, Py_ssize_t e, Py_ssize_t l);
