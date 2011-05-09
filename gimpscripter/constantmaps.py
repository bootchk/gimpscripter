#!/usr/bin/env python

'''
Mappings of constants.
Derived from gimpfu.py.
'''
from gimpfu import *

'''
Here I started an elegant way to create the mapping, but gave up on it.
How do you instantiate a type without knowing what parameters __call__ takes??
_instance_mapping = { }
for (typeconstant, type) in gimpfu._obj_mapping.items():
  _instance_mapping[typeconstant] = type.__call__()
  
'''

'''
Map parameter type to don't care instance of that parameter type.
Used for actual values to a plugin call, might be type checked 
(not by Python but possibly by Pygimp?)
but ignored because it is RUN_LAST_VAL.
!!! Use None for ephemeral types.
'''
_instance_map = {
    PF_INT8        : 0,
    PF_INT16       : 0,
    PF_INT32       : 0,
    PF_FLOAT       : 0.0,
    PF_STRING      : "foo",  # At shortcut time: a don't care string (can't be empty.)
    PF_COLOR       : (0,0,0), # a don't care color
    PF_DISPLAY     : None,
    PF_IMAGE       : None,
    PF_LAYER       : None,
    PF_CHANNEL     : None,
    PF_DRAWABLE    : None,
    PF_VECTORS     : None,
    PF_BOOL        : True,
    
    PF_BRUSH       : "foo", # TODO the rest of the upconverted types
}

'''
Map parameter type to default instance of that parameter type.
There is some logic here, 1 is better than 0 as a default for most plugins parameters?
Note this might go away if we can determine the actual defaults for wrapped plugins.
!!! Use common names for ephemeral types, since we are defaulting a string widget.
'''
_default_map = {
    PF_INT8        : 1,
    PF_INT16       : 1,
    PF_INT32       : 1,
    PF_FLOAT       : 5.0,
    PF_STRING      : "bar",  # At shortcut time: a don't care string (can't be empty.)
    PF_COLOR       : (37,37,37), # a don't care color
    PF_DISPLAY     : None,  # ???
    PF_IMAGE       : "Untitled",
    PF_LAYER       : "Clipboard",
    PF_CHANNEL     : "Alpha",
    PF_DRAWABLE    : "Clipboard",
    PF_VECTORS     : "Path",
    PF_BOOL        : "True",
    
    PF_BRUSH       : "Circle (05)"
}


'''
For hidden parameters, map parameter type to an actual parameter.
Actual parameters are references to stacks of ephemera.
Used to generate a call string.
'''
_hidden_actual_map = {
    PF_IMAGE       : "ephemera.top(PF_IMAGE)", 
    PF_DRAWABLE    : "ephemera.top(PF_DRAWABLE)",
    PF_LAYER       : "ephemera.top(PF_LAYER)",
    PF_CHANNEL     : "ephemera.top(PF_CHANNEL)",
    PF_VECTORS     : "ephemera.top(PF_VECTORS)",
}

'''
Map numeric parameter type PDB to name in Python.

Note, we have lost information: the PDB doesn't know the original types,
that also described the widget for entering it, such as PF_SLIDER for PF_FLOAT.
'''
_type_to_string_map = {
    PF_INT8        : "PF_INT8",
    PF_INT16       : "PF_INT16",
    PF_INT32       : "PF_INT32",
    PF_FLOAT       : "PF_FLOAT",
    PF_STRING      : "PF_STRING",
    PF_COLOR       : "PF_COLOR",
    PF_DISPLAY     : "PF_DISPLAY",
    PF_IMAGE       : "PF_IMAGE",
    PF_LAYER       : "PF_LAYER",
    PF_CHANNEL     : "PF_CHANNEL",
    PF_DRAWABLE    : "PF_DRAWABLE",
    PF_VECTORS     : "PF_VECTORS",
    PF_BOOL        : "PF_BOOL",
    
    PF_BRUSH       : "PF_BRUSH",
}
