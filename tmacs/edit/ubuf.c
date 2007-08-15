#include <Python.h>


/* functions defined in the module */

static PyMethodDef ubufMethods[] = {
#if 0
    {"system",  spam_system, METH_VARARGS, "Execute a shell command."},
#endif

    {NULL, NULL, 0, NULL}
};


typedef struct {
    PyObject_VAR_HEAD

    Py_UNICODE     *buf;
    PyObject       *ustr;
    size_t          gapstart;
    size_t          gapsize;
} UBuf;



static void
ubuf_dealloc(UBuf *self)
{
    self->ob_type->tp_free((PyObject *)self);
}



static PyObject *
ubuf_new(PyTypeObject *type, PyObject *args, PyObject *kdws)
{
    UBuf *self;

    self = (UBuf *)type->tp_alloc(type, 0);
    if (!self) {
        return NULL;
    }

    if (PyArg_ParseTuple(args, "")) {
         
       
        return (PyObject *)self;
    }
    
    ubuf_dealloc(self);

    return NULL;
}



/* Begin UBuf methods */



static PyObject *
ubuf_foo(UBuf *self, PyObject *args)
{
    Py_RETURN_NONE;
}



static PyMethodDef ubuf_methods[] = {
    {"foo",         (PyCFunction)ubuf_foo,              METH_NOARGS},

    {NULL,          NULL}
};


static PyTypeObject UBuf_Type = {
    /* The ob_type field must be initialized in the module init function
     * to be portable to Windows without using C++. */
    PyObject_HEAD_INIT(NULL)
    0,                      /*ob_size*/
    "UBuf",                 /*tp_name*/
    sizeof(UBuf),           /*tp_basicsize*/
    0,                      /*tp_itemsize*/
    /* methods */
    (destructor)ubuf_dealloc,/*tp_dealloc*/
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
    ubuf_methods,           /*tp_methods*/
    0,                      /*tp_members*/
    0,                      /*tp_getset*/
    0,                      /*tp_base*/
    0,                      /*tp_dict*/
    0,                      /*tp_descr_get*/ 
    0,                      /*tp_descr_set*/
    0,                      /*tp_dictoffset*/
    0,                      /*tp_init*/
    PyType_GenericAlloc,    /*tp_alloc*/
    ubuf_new,               /*tp_new*/
    _PyObject_Del,          /*tp_free*/
    0,                      /*tp_is_gc*/
};




PyMODINIT_FUNC
initubuf(void)
{
    PyObject *m, *d;

    m = Py_InitModule("ubuf", ubufMethods);

    UBuf_Type.ob_type = &PyType_Type;
    d = PyModule_GetDict(m);
    PyDict_SetItemString(d, "UBuf", (PyObject *)&UBuf_Type);

#if 0
    SpamError = PyErr_NewException("spam.error", NULL, NULL);
    Py_INCREF(SpamError);

    PyModule_AddObject(m, "error", SpamError);
#endif
}
