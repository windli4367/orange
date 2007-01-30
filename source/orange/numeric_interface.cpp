#ifndef NO_NUMERIC

#include "numeric_interface.hpp"
#include "errors.hpp"

bool importarray_called = false;

PyObject *moduleNumeric = NULL, *moduleNumarray = NULL, *moduleNumpy = NULL;
PyObject *numericMaskedArray = NULL, *numarrayMaskedArray = NULL, *numpyMaskedArray = NULL;
PyTypeObject *PyNumericArrayType = NULL, *PyNumarrayArrayType = NULL, *PyNumpyArrayType = NULL;

void initializeNumTypes()
{
  PyObject *ma;
  
  moduleNumeric = PyImport_ImportModule("Numeric");
  if (moduleNumeric) {
    PyNumericArrayType = (PyTypeObject *)PyDict_GetItemString(PyModule_GetDict(moduleNumeric), "ArrayType");
    
    ma = PyImport_ImportModule("MA");
    if (ma)
      numericMaskedArray = PyDict_GetItemString(PyModule_GetDict(ma), "MaskedArray");
  }
  
  moduleNumarray = PyImport_ImportModule("numarray");
  if (moduleNumarray) {
    PyNumarrayArrayType = (PyTypeObject *)PyDict_GetItemString(PyModule_GetDict(moduleNumarray), "ArrayType");

    ma = PyImport_ImportModule("numarray.ma");
    if (ma)
      numarrayMaskedArray = PyDict_GetItemString(PyModule_GetDict(ma), "MaskedArray");
  }

  moduleNumpy = PyImport_ImportModule("numpy");
  if (moduleNumpy) {
    PyObject *mdict = PyModule_GetDict(moduleNumpy);
    PyNumpyArrayType = (PyTypeObject *)PyDict_GetItemString(mdict, "ndarray");
    
    ma = PyDict_GetItemString(mdict, "ma");
    if (ma)
      numpyMaskedArray = PyDict_GetItemString(PyModule_GetDict(ma), "MaskedArray");
  }
    
  importarray_called = true;
//  import_array();
}


// avoids unnecessarily importing the numeric modules
bool isSomeNumeric_wPrecheck(PyObject *args) {
  static char *numericNames[] = {"array", "numpy.ndarray", "ndarray", "numarray.numarraycore.NumArray", "NumArray", 0};
  for(char **nni = numericNames; *nni; nni++)
    if (!strcmp(args->ob_type->tp_name, *nni))
      return isSomeNumeric(args);
  return false;
}


bool isSomeNumeric(PyObject *obj)
{
  if (!importarray_called)
    initializeNumTypes();
    
  return     PyNumericArrayType && PyType_IsSubtype(obj->ob_type, PyNumericArrayType)
          || PyNumarrayArrayType && PyType_IsSubtype(obj->ob_type, PyNumarrayArrayType)
          || PyNumpyArrayType && PyType_IsSubtype(obj->ob_type, PyNumpyArrayType);
}
  

char getArrayType(PyObject *args)
{
  PyObject *res = PyObject_CallMethod(args, "typecode", NULL);
  if (!res)
    return -1;
  char cres = PyString_AsString(res)[0];
  Py_DECREF(res);
  return cres;
}


void numericToDouble(PyObject *args, double *&matrix, int &columns, int &rows)
{
  prepareNumeric();

  if (!isSomeNumeric(args))
    raiseErrorWho("numericToDouble", "invalid type (got '%s', expected 'ArrayType')", args->ob_type->tp_name);

  PyArrayObject *array = (PyArrayObject *)(args);
  if (array->nd != 2)
    raiseErrorWho("numericToDouble", "two-dimensional array expected");

  const char arrayType = getArrayType(array);
  if (!strchr(supportedNumericTypes, arrayType))
    raiseErrorWho("numericToDouble", "ExampleTable cannot use arrays of complex numbers or Python objects", NULL);

  columns = array->dimensions[1];
  rows = array->dimensions[0];
  matrix = new double[columns * rows];
 
  const int &strideRow = array->strides[0];
  const int &strideCol = array->strides[1];
  
  double *matrixi = matrix;
  char *coli, *cole;

  for(char *rowi = array->data, *rowe = array->data + rows*strideRow; rowi != rowe; rowi += strideRow) {
    #define READLINE(TYPE) \
      for(coli = rowi, cole = rowi + columns*strideCol; coli != cole; *matrixi++ = double(*(TYPE *)coli), coli += strideCol); \
      break;

    switch (arrayType) {
      case 'c':
      case 'b': READLINE(char)
      case 'B': READLINE(unsigned char)
      case 'h': READLINE(short)
      case 'H': READLINE(unsigned short)
      case 'i': READLINE(int)
      case 'I': READLINE(unsigned int)
      case 'l': READLINE(long)
      case 'L': READLINE(unsigned long)
      case 'f': READLINE(float)
      case 'd': READLINE(double)
    }

    #undef READLINE
  }
}


void numericToDouble(PyObject *args, double *&matrix, int &rows)
{
  prepareNumeric();

  if (!isSomeNumeric(args))
    raiseErrorWho("numericToDouble", "invalid type (got '%s', expected 'ArrayType')", args->ob_type->tp_name);

  PyArrayObject *array = (PyArrayObject *)(args);
  if (array->nd != 1)
    raiseErrorWho("numericToDouble", "one-dimensional array expected");

  const char arrayType = getArrayType(array);
  if (!strchr(supportedNumericTypes, arrayType))
    raiseError("numericToDouble", "ExampleTable cannot use arrays of complex numbers or Python objects", NULL);

  rows = array->dimensions[0];
  matrix = new double[rows];
 
  const int &strideRow = array->strides[0];
  
  double *matrixi = matrix;
  char *rowi, *rowe;

  #define READLINE(TYPE) \
    for(rowi = array->data, rowe = array->data + rows*strideRow; rowi != rowe; *matrixi++ = double(*(TYPE *)rowi), rowi += strideRow); \
    break;

  switch (arrayType) {
      case 'c':
      case 'b': READLINE(char)
      case 'B': READLINE(unsigned char)
      case 'h': READLINE(short)
      case 'H': READLINE(unsigned short)
      case 'i': READLINE(int)
      case 'I': READLINE(unsigned int)
      case 'l': READLINE(long)
      case 'L': READLINE(unsigned long)
      case 'f': READLINE(float)
      case 'd': READLINE(double)
  }

  #undef READLINE
}
#endif
