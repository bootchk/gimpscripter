#!/usr/bin/env python

'''
Macros: generally, text templates with substitutions.
Here specifically, Python code that is a seq of or a nesting of calls to Gimp PDB procedures.

This includes :
- support for macros
- macro definitions themselves

A author-user COULD write their own macros by altering this file.

Notes for writing macros:
Use double quotes outside, single quotes inside a macro.
Use "ephemera.top(PF_FOO)" to refer to the currently active object of type PF_FOO
Use $foo, $bar, etc. for placeholders for parameters foo, bar, ... Note the placeholder names
should be the same as the parameter names in the parameter def (ParamDef).

Copyright 2010  Lloyd Konneker

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

from gimpfu import *  # for PF types

''' A macro definition comprises:
"macro-name" :              # use dash or underbar, usually name matches an entry in map_procedures.py
("text",                    # quoted Python code text with $placeholders (macro parameters)
  (                          # a tuple of one or more...
    (type, parameterName, desc), ... # ParamDef
  ),
  "blurb"                      # quoted blurb
)

!!! Note the comma after the first ParamDef is always needed else it is not a tuple!!!
!!! Note placeholders must start with a $ and then a valid Python identifier e.g. starting with a letter
!!! A placeholder name can appear in many places in the body.
!!! and the placeholders should match the parameterName
!!! Any sequence should have proper indentation (2 spaces) between statements (after a newline) NOT inside a raw string.
!!! Any procedure names should use underbar, not dash
!!! Any procedure names should be prefixed with "pdb."

'''

from string import Template

# Create a new channel named bar from red channel
macros = { \
"macro-channel-new" : ("pdb.gimp_image_add_channel(ephemera.top(PF_IMAGE), pdb.gimp_channel_new_from_component(ephemera.top(PF_IMAGE), 0, $channelName ), 1)", # macro text
((PF_STRING, 'channelName', 'The name to give to the channel'), ),  # macro pdef tuple
"Create new channel and add it to image."), # macro blurb
"macro-layer-copy" : ("pdb.gimp_layer_copy(ephemera.top(PF_LAYER), $addAlpha)\n  pdb.gimp_displays_flush()", ((PF_INT32, 'addAlpha', 'Add an alpha channel?'), ),
"Copy layer and add it to image BROKEN?"),
# Add layer from visible then nested add to image.  User must name the layer
"macro-layer-new-visible" : ("pdb.gimp_image_add_layer(ephemera.top(PF_IMAGE), pdb.gimp_layer_new_from_visible(ephemera.top(PF_IMAGE), ephemera.top(PF_IMAGE), $layerName), 0)", 
((PF_STRING, 'layerName', 'Layer name'), ),
"Create layer from visible and add it to image on top."),
# I also tried to lookup the layer later, but it is not in ephemera unless it is attached to image.
# Add layer blank then nested add to image.  User must name the layer.
# Note the mode comes from the active layer, not image?  Opacity 100, combination mode 0 for normal
"macro-layer-new-blank-attached" : ("pdb.gimp_image_add_layer(ephemera.top(PF_IMAGE), pdb.gimp_layer_new(ephemera.top(PF_IMAGE), ephemera.top(PF_IMAGE).width, ephemera.top(PF_IMAGE).height, ephemera.top(PF_LAYER).mode, $layerName, 100, 0), 0)", 
((PF_STRING, 'layerName', 'Layer name'), ),
"Create blank layer like the image and add it to image on top."),
# New display then flush. Justification: rarely a reason to create a  display without flushing it.
"macro-display-new" : ("pdb.gimp_display_new(ephemera.top(PF_IMAGE))\n  pdb.gimp_displays_flush()", 
(), # Empty pdefs
"Create new display from current image and flush it so user can see it."),
# Context set brush with chooser.  
# !!! This upconverts the parameter type:
# at generation time and runtime, author-user or user sees a brushChooser widget instead of a stringEntry
"macro-context-choose-brush" : ("pdb.gimp_context_set_brush($brush)", 
((PF_BRUSH, 'brush', 'Brush'), ),
"Create layer from visible and add it to image on top."),
}

"""
Work in progress
# Paste as new layer  (not available in PDB?)
# Internal buffer to named buffer
# New layer size of internal buffer
# Add new layer to image
# Paste named buffer into layer
# Anchor
"macro-paste-as-new-layer" : ("pdb.gimp_edit_named_paste('temp')\n  pdb.gimp_image_add_layer(ephemera.top(PF_IMAGE), pdb.gimp_layer_new(ephemera.top(PF_IMAGE), pdb.gimp_buffer_get_width('temp'), pdb.gimp_buffer_get_height('temp'), pdb.gimp_buffer_get_height('temp'), pdb.gimp_buffer_get_image_type('temp'), $layerName, 100, 0), 0)\n  pdb.gimp_edit_paste()\n  pdb.gimp_floating_sel_anchor()", 
((PF_STRING, 'layerName', 'Layer name'), ),
"Paste into a new anchored layer and add it to image on top."),
"""

# pdb.gimp_image_add_layer(ephemera.top(PF_IMAGE), ephemera.top(PF_LAYER), 1)

def is_macro(name):
  return macros.has_key(name)
  

# Getters
# TODO class for macros

def get_pdefs_for(name):
  result = macros[name][1]  # second field is list of pdefs
  if not isinstance(result, tuple):
    raise RuntimeError("The pdefs for a GimpScripter macro must be a tuple")
  return result

def get_blurb(name):
  return macros[name][2]
  
def template_for(name):
  ''' Return the template for macro name '''
  return Template(macros[name][0])  # 0 is the text
  

  
