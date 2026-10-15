#define PY_SSIZE_T_CLEAN
#include <Python.h>
/* Calls a Python callable n times while keeping many values live across the call,
   so that with -fomit-frame-pointer the compiler spills into rbp. */
static PyObject *call_many(PyObject *self, PyObject *args) {
    PyObject *f; long n;
    if (!PyArg_ParseTuple(args, "Ol", &f, &n)) return NULL;
    long a = 1, b = 2, c = 3, d = 5, e = 7, g = 11, h = 13;
    for (long i = 0; i < n; i++) {
        PyObject *r = PyObject_CallNoArgs(f);
        if (!r) return NULL;
        long v = PyLong_AsLong(r);
        Py_DECREF(r);
        a += v ^ i; b += a * 3; c ^= b + i; d += c >> 1; e -= d ^ a; g += e * b; h ^= g + c;
    }
    return PyLong_FromLong(a + b + c + d + e + g + h);
}
static PyMethodDef methods[] = {{"call_many", call_many, METH_VARARGS, NULL}, {NULL}};
static struct PyModuleDef mod = {PyModuleDef_HEAD_INIT, NAME, NULL, -1, methods};
#define CAT2(a,b) a##b
#define CAT(a,b) CAT2(a,b)
PyMODINIT_FUNC CAT(PyInit_, MODNAME)(void) { return PyModule_Create(&mod); }
