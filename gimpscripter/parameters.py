#!/usr/bin/env python

'''
Parameters of a plugin, both formal and actual.

Understands various views and slices:
  hidden and nonhidden parameters
  deferred parameters
  formal (paramdefs) versus actual (entered) parameters
This class hides knowledge about how parameter sets are sliced.

Typical state transition for this object:
  new(), init_for_procname(), preset(), [one or more repeats of init or preset], access slices

Formal parameters are available as soon as this created.
Actual parameters are available after user has used a dialog
for entering actual and deferring parameters.
The deferring action slices both formal and actual parameters.

Hidden: 
Two meanings:
- pygimp gimpfu module hides them for beginning programmers.  The PDB does NOT hide them.
- hidden from the user by GimpScripter, i.e. never presented in a dialog.

userentered: actual parameter values returned by dialog with user, but only non-hidden parameters
    The user may not have actually touched them, but accepted the initial (default) values.
    
defers: sequence of booleans telling which params user deferred, from the dialog
    deferred is shorter than non-hidden is shorter than all.
    defers is same length as userentered.

Example:
  Formal params, as from the PDB:   run-mode, image, drawable, tweak, color
  Hidden formal:  run-mode, image, drawable
  
  Python paramdefs:
      [   (PF_INT, tweak, "Speed of fitering", 37),
          (PF_COLOR, color, "Color to filter", (125,10,20) )
      ]
          (type, name, desc, default, optional)
  
  User entered: [int instance, color instance]
  Deferred: [True, False]     (boolean, same length as user entered.)
          
!!! Note that from the PDB, paramdefs are only (type, name, desc)

Unique names:
Over a set of sets of paramdefs, names are not unique.
We show the names from the paramdefs to the user: they can cope with duplicate names.
When generating code, we uniquify names to distinguish references.
Unique names are used:
  in formal params to wrapper
  in registration of wrapper
  in wrapper's calls to wrapped

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

from gimpfu import *
import gimpcolor

from gimpscripter import constantmaps
from gimpscripter import parse_params




class Param(object):
  '''
  A parameter definition and declaration, i.e. formal and actual.
  More attributes than a Gimp ParamDef, but encloses same named attributes (name, type, desc)
  '''
  
  def __init__(self, gimp_pdef, hidden):
    '''
    Initialize from a Gimp ParamDef
    
    hiddenness depends on order in a list, can't be computed just from the gimp_pdef
    '''
    # Formal attributes
    self.type = gimp_pdef[0]
    self.name = gimp_pdef[1]
    self.desc = gimp_pdef[2]
    # !!! A desc can be very long.  It is a problem for our GUI, but not here.
    self.pdef = gimp_pdef   # Keep it for convenience
    self._hidden = hidden
    # does user see it.  Not computed just from type, but from position.
    
    '''
    Defaults are not available from the PDB.
    Each plugin language (C, Scheme, Python) has its own way of storing defaults (initial values)
    and last values (recently used values).
    This is lowest common denominator: a "typical" value for the type,
    not the same as the initial value (called a default) given in plugin  definitions.
    Future: recover the recently used values.
    '''
    if not hidden:  
      # map parameter type to a typical(canonical) default of the type
      # !!! There are some plugins that raise KeyError eg Image/Colors/Map/Rearrange for INT8ARRAY
      self.default = constantmaps._default_map[gimp_pdef[0]]
    else: 
      self.default = None # Hidden params don't have defaults
    
    # Attributes of actual.  Initially unknown until user interaction
    self.is_deferred = False
    self.value = None
    
    # Attributes computed over an entire list of paramdefs (from more than one procedure)
    # The op to compute these names must be done after all commands are in the sequence
    # and before unique_name is accessed.
    self.unique_name = None
    
  
  def __str__(self):
    return str(self.type) + " " + self.name + " " + self.desc + " " + str(self.value)

  # Getters
  
  def is_ephemeral(self):
    ''' Computed from type. '''
    return is_ephemeral_type(self.type)
  
  def is_hidden(self):
    return self._hidden

  def get_evaluable_value(self):
    '''
    In this app (code generation) need evaluable strings for the userentered params, not objects.
    Hence we repr(value).  Value is an object.  repr(value) is evaluable.
    This is obvious to a Pythonista: thats the definition of repr(), but I want to emphasize.
    Notes:
       values of type string: repr() adds pair of quotes, which is what we want.
       values of type gimpcolor.RGB, the repr is "gimpcolor.RGB(0,0,0,1)", which IS evaluable
    '''
    return repr(self.value)


class ParamList(list):
  '''
  A container of Paramdefs.
  
  Slices are sequences of parameters for a named procedure.
  Slices can be inserted and removed by position or name.
  
  Has a state: whether user entered actual values.
  '''

  def __init__(self):
  
    self.procedure_start_index = [0]
    # List of indexes of first parm of procedures
    # !!! Also used to find the end parm of a procedures
    # so it is post-incremented
    
    
  def delete_params_of(self, procname):
    pass  #TODO

  def insert_params_of(self, command, position):
    '''
    Insert slice of formal parameters of PDB procedure.
    Mainly, copy and convert from Gimp ParamDef to our Param.
    '''
    inparamdefs = command.get_paramdefs()
    # TODO We don't need the return values since we are inferring creation of objects.
    # Scheme scripts don't have return values, and most returned objects are inferrable.
    # returnparamdefs = pdb[procname].return_vals
    
    # Assert start of params for this command position is already captured in procedure_start_index
    # TODO more general, if we insert anywhere but at the end.
    start = self.procedure_start_index[-1]
    
    for x in inparamdefs:
      param = Param(x, hidden=False)  # temporarily hidden is False
      self.append(param)
    
    # Remember end of params for this command position
    self.procedure_start_index.append(len(self))
    end = self.procedure_start_index[-1]
    
    # Determine which params are hidden, a leading prefix.
    # Gimpfu does something similar to hide image, drawable parameters.
    print start, end
    count = parse_params.count_hidden_params(self[start:end])
    for param in self[start: start+count]:
      param._hidden = True  # TODO setter
    
    print "Total count params", len(self)
    # After insert, must uniquify names again


  def _get_range_for_position(self, position):
    ''' Get the range for parameters of command at position. '''
    start, end = self.procedure_start_index[position], self.procedure_start_index[position+1]
    print "Range of parameters for position", position, " is ", start, end
    return start, end
    
  def get_parms_for(self, position):
    ''' Return slice of parms for command at position '''
    # TODO for ease of use, link parm values to earlier parms ???
    start_parm, end_parm = self._get_range_for_position(position)
    return self[start_parm:end_parm]


  def preset(self, userentered, defers, command_index=None):
    '''
    Preset with actual parameters and deferments from a dialog with user.
    Userentered means the user at least reviewed the initial values and possibly entered them.
    Index is the command whose parameters the user changed.
    '''
    print "Validating", userentered, defers
    # Userentered and defers must be the length of nonhidden.
    assert len(userentered) == len(defers)
    
    # In the range of parameters for command_index
    start_parm, end_parm = self._get_range_for_position(command_index)
    
    # Shuffle values from userentered, defers into self
    source_index = 0
    for item in self[start_parm:end_parm]:
      if not item.is_hidden():
        item.is_deferred = defers[source_index]
        item.value = userentered[source_index]  # Note referring to an object, possibly not a string
        source_index += 1
    
    
  def is_take_image(self):
    '''
    Return whether any procedure takes an image as hidden parameter.
    i.e. if its second parameter has type PF_IMAGE (Also, it has the name "image").
    Every procedure takes a run-mode for first parameter.
    If it has a second parameter AND it is PF_IMAGE, then the third parameter is PF_DRAWABLE?
    Note that parametes of type image CAN also exist beyond the second parameter,
    TODO there is more to this, it depends on the type of the procedure.
    '''
    # Iterate by procedure
    for index in self.procedure_start_index:
      second_parameter_index = index + 1
      if second_parameter_index < len(self):
        # TODO and less than the end of the parameters for this procedure
        if self[second_parameter_index].type == PF_IMAGE:
          return True
    return False
    
    
  def has_user_enterable_params(self):
    ''' 
    Does any procedure have nonhidden parameters defined?
    Not whether user entered them yet.
    '''
    # Map takes a function as first parameter, here a getter
    result = not all(map(Param.is_hidden, self))
    # print "Has user params returns ", result
    return result
    
  def has_ephemeral_params(self):
    ''' Does any procedure have ephemeral parameters defined? '''
    return any(map(Param.is_ephemeral, self))
  
  def get_nonhidden_pdefs_for(self, position):
    ''' Return slice of nonhidden pdefs for command at position '''
    start_parm, end_parm = self._get_range_for_position(position)
    return [x.pdef for x in self[start_parm:end_parm] if not x.is_hidden()]
  
  def get_nonhidden_defaults_for(self, position):
    ''' Return slice of nonhidden defaults for command at position '''
    start_parm, end_parm = self._get_range_for_position(position)
    return [x.default for x in self[start_parm:end_parm] if not x.is_hidden()]
    
  def get_nonhidden_values_for(self, position):
    ''' Return slice of nonhidden userentered values for command at position '''
    start_parm, end_parm = self._get_range_for_position(position)
    return [x.value for x in self[start_parm:end_parm] if not x.is_hidden()] 
    
  def get_defers_for(self, position):
    ''' Return is_deferred for slice of nonhidden parameters. '''
    start_parm, end_parm = self._get_range_for_position(position)
    return [x.is_deferred for x in self[start_parm:end_parm] if not x.is_hidden()] 

  def nonhiddenpdefs(self):
    ''' Return slice of pdefs of nonhidden Params 
    Note these are PyGimp pdef structures or fascimiles.
    '''
    return [x.pdef for x in self if not x.is_hidden()]
    
  def nonhiddendefaults(self):
    ''' Return slice of nonhidden defaults '''
    return [x.default for x in self if not x.is_hidden()]
  
  def deferred_unique_names(self):
    ''' Return unique names of slice of deferred '''
    # Note deferred implies not hidden
    return [x.unique_name for x in self if x.is_deferred]

  
  def uniquify_names(self):
    '''
    For a sequence of commands, uniquify names across all paramdefs.
    They might be used for parameters to plug_in main, where they must be unique.
    !!! Also insure names are Pythonic: no dash.
    Note this computes an attribute and must be called before the attribute is accessed.
    
    TODO doctest this
    n, n, n, n_1 => n, n_1, n_2, n_1_1
    n_1, n, n_1 => n_1, n, n_1_1
    '''
    names = {}  # name => count of uses
    
    for param in self:
      original_name = param.pdef[1]
      
      # Since these names will be used in Python code, transliterate dash to underbar
      original_name = original_name.replace("-", "_")
      
      if original_name in names:
        count = names[original_name] + 1
        names[original_name] = count
        # generate unique name, use _
        # Note generated name may clash with name yet to be seen,
        # but the yet to be seen name will get a new name.
        unique_name = original_name + "_" + str(count)
        # !!! Put the unique name in names also
        names[unique_name] = 1  # first use of unique name
      else: # first use
        names[original_name] = 1
        unique_name = original_name
      
      param.unique_name = unique_name # store computed attribute
  
    
    
def any_parms_deferred(parms):
  ''' 
  Are any parms in the given list deferred? 
  This is called when the parm list for a command is already in hand.
  '''
  # reduce(operator.or_, parms.is_deferred, False):
  for item in parms:
    if item.is_deferred:
      return True
  return False

def get_parms_deferred(parms):
  ''' 
  Return deferred parms in the given list? 
  This is called when the parm list for a command is already in hand.
  '''
  return [x for x in parms if x.is_deferred]
  
def get_parms_nonhidden(parms):
  ''' 
  Return nonhidden parms in the given list? 
  This is called when the parm list for a command is already in hand.
  '''
  return [x for x in parms if not x.is_hidden()]
  
def get_parms_hidden(parms):
  ''' Return the hidden parms, including run-mode. '''
  result = [x for x in parms if x.is_hidden()]
  for parm in result:
    print "Hidden parms", parm
  return result 


def is_ephemeral_type(paramtype):
  '''
  Return whether paramtype is that of ephemeral Gimp objects.
  Ephemeral means object set existing at wrapping plugin creation time can differ from 
  set existing at wrapping plugin run time.
  In other words, use the name of the object as a pseudo UID (universal ID) spanning sessions with Gimp.
  '''
  return paramtype in (PF_DISPLAY, PF_IMAGE, PF_LAYER, PF_CHANNEL, PF_DRAWABLE, PF_VECTORS)   
  
def get_return_parms(procname):
  #TODO
  return []
      

      
      

