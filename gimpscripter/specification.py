#!/usr/bin/env python

'''
Specifications.  What a user specifies or enters.
Specifies the wrapper plugin.
'''
from gimpfu import *

from gimpscripter import parameters
from gimpscripter import parse_params
from gimpscripter import macros

class GimpScripterSpec(object):
  '''
  Everything the user specified.
  The data passed from the GUI to the generator.
  
  Comprises:
    attributes of wrapping plugin
    attributes of commands use chose
    attributes of parameters user entered
  '''
  
  def __init__(self):
    self.wrapping = WrappingPluginSpec()
    self.commands = Commands()
    # TODO excise this, unused
    self. parameter_results = [None, None] # results of parameter dialog: actual parameters and defers
  
  def set_parameter_results(self, actual, toggles):
    self.parameter_results = [actual, toggles]

  
  
class WrappingPluginSpec(object):
  '''
  A specification for user chosen attributes of a Gimp wrapping plugin.

  wrappingmenuitem: of wrapping plugin, user chose.
  wrappingmenupath: TODO
  '''
  def __init__(self):
    self.menuname = ""
    self.name = "bar"  # TODO User given name
    self.blurb = "zed"  # TODO User given blurb
    
  def set_menu_name(self, name):
    self.menuname = name
    


class Commands(object):
  '''
  A sequence of commands.
  
  The main thing this does is allow access to the aggregate parameters.
  '''
  def __init__(self):
    self.command_list = []
    # list of commands in this seq
    self.param_list = parameters.ParamList()
    # list of all params for all commands in this seq
  
  def __len__(self):
    return len(self.command_list)
  
  def append(self, command):
    ''' Append command to command list '''
    self.param_list.insert_params_of(command, len(self))
    command.position = len(self)
    self.command_list.append(command)
    
  
  # TODO insert, remove
  
  def get_parms_for(self, position):
    ''' Return list of parms for command at position'''
    return self.param_list.get_parms_for(position)
  
  def get_command_for(self, position):
    ''' Return list of parms for command at position'''
    return self.command_list[position]
  
  def has_macros(self):
    ''' Any macros in this command sequence? '''
    return any(map(CommandSpec.is_macro, self.command_list))
    
  def has_in_params(self):
    '''
    Does any command have hidden params that are not run-mode?
    This must be command by command, it can't be just over the aggregate parameter list.
    '''
    for command in self.command_list:
      # Assume all macros access hidden params
      # TODO take all this special case code out, just ask the command and have subclasses.
      if macros.is_macro(command.name):
        return True
      else:
        # Not a macro, look at the params for this command
        # Alternatively we could call the pdb for the pdefs
        if parse_params.count_nonrunmode_hidden_params(self.param_list.get_parms_for(command.position)):
          return True
    return False
    
    
  def is_take_image(self):
    ''' 
    Does any command have image as first parameter?
    If so, the wrapping plugin must take an image.
    '''
    return self.param_list.is_take_image()
  
  
  def deferred_unique_names(self):
    '''
    Return the names of all deferred parameters.
    !!! Uniquified names among separate commands in list.
    '''
    return self.param_list.deferred_unique_names()
  
    
  def has_ephemeral_params(self):
    '''
    Does any command in sequence have ephemeral parameters?
    Or use ephemeral parameters internally to a macro?
    For now, assume all macros use ephemeral parameters internally.
    TODO relax this assumption
    '''
    return self.param_list.has_ephemeral_params() or self.has_macros()
  
  
  def has_user_enterable_params(self):
    ''' Does any command have user enterable parameters?'''
    result = self.param_list.has_user_enterable_params()
    # print "Has params returns ", result, len(self.param_list)
    return result
    


class CommandSpec(object):
  '''
  Specifies a single command and user entered attributes of its use.
  
  Commands are of 3 types:
  - plugin
  - procedure
  - macro of the above
  First two are both defined in the PDB.  Macros are defined here.
  
  name: command name for which user chose menu item
  '''
  def __init__(self, name, pathstring):
    self.name = name
    self.is_use_last = False
    self.position = None
    # position of this command in Commands, set when appended
    self.pathstring = pathstring
    # menupath in our mock menu of commands

  
  def set_is_use_last(self, truth):
    '''
    Some commands can be executed to use the most recent parameters from prior use,
    even prio use outside this wrapping plugin.
    This is a user choice to use the command in that fashion.
    '''
    self.is_use_last = truth

  """ We can't do this without a reference to the parent list of this command
  def get_params(self):
    '''Return the Params of this command.'''
  """
    

  def get_paramdefs(self):
    ''' Get the paramdefs of this command. '''
    if macros.macros.has_key(self.name):
      print "A Macro"
      return macros.get_pdefs_for(self.name)
    else:
      return pdb[self.name].params
      
  def is_macro(self):
    # TODO refactor using classes
    return macros.is_macro(self.name)
    
    
    
"""
class PluginCommandSpec(CommandSpec):
  '''
  A plugin command has:
  
  - a leading run-mode parameter (and can be run with last values.)
  - hidden image and drawable parameters
  '''
  pass
"""
