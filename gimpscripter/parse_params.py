
'''
Determine hidden parameters from a list of parameter definitions.

Hidden parameters are always a leading prefix.
Here we determine them by simple parsing.

BNF:

Version 1:
  This version is inadequate: it hides second drawable parameters that shouldn't be hidden.
  For example, in Color/Map/Sample Colorize.
  
  <hidden_prefix> ::= ["run-mode"] [<IDL>*]
  <IDL> ::= image-type | drawable-type | layer-type

  In other words, the optional run-mode parameter is identified by name,
  and the other hidden parameters are identified by type (not name).
  
Version 2:
  
  <hidden_prefix> ::= ["run-mode"] [<Image>] [<Drawable>] [<Layer>] [<Channel>] [<Path>]
  
  [] means 0 or 1.  IOW the types are in a certain order.
  When a type is seen that is not in the order,
  or when a second parameter of the same type is seen,
  counting stops.

Examples:
  Image returns 1
  Drawable returns 1
  Image, Image returns 1
  Image, Drawable returns 2
  Image, Layer returns 2
  Image, Channel returns 2
  Image, Drawable, Drawable returns 2
  Image, Drawable, Layer returns 3
  Image, Drawable, Layer, Channel returns 4

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

class paramlistScanner(object):
  ''' 
  Simple lexical scanner of param list by type attribute.
  Safe to scan with scannee empty: count() returns 0
  '''
  def __init__(self, paramlist):
    self.token = 0
    self.count = 0
    self.scannee = paramlist
  
  def get_next_type(self):
    if self.token >= len(self.scannee):
      return None # !!! None will not match anything
    else:
      return self.scannee[self.token].type
  
  def advance(self):
    self.token += 1
    self.count += 1
  
  def skip(self):
    self.token += 1 # !!! But don't increment count
    
  def get_count(self):
    return self.count



      
def count_hidden_params(paramlist):
  '''
  Parse and count hidden params from a list of Params.
  '''
  scanner = paramlistScanner(paramlist)
  
  if len(paramlist) < 1 :
    return 0 
    
  # Zero or one pdefs with name equal run-mode
  if paramlist[0].name == 'run-mode':
    scanner.advance()
  if scanner.get_next_type() == PF_IMAGE:
    scanner.advance()
  if scanner.get_next_type() == PF_DRAWABLE:
    scanner.advance()
  if scanner.get_next_type() == PF_LAYER:
    scanner.advance()
  if scanner.get_next_type() == PF_CHANNEL:
    scanner.advance()
  if scanner.get_next_type() == PF_VECTORS:
    scanner.advance()
  print "Count hidden params is ", scanner.get_count()
  return scanner.get_count()


def count_nonrunmode_hidden_params(paramlist):
  ''' Parse and count hidden params that are NOT run-mode from a list of Params .'''
  if len(paramlist) < 1 :
    return 0
  
  scanner = paramlistScanner(paramlist) 

  # Zero or one params with name equal run-mode
  if paramlist[0].name == 'run-mode':
    scanner.skip()  # !!! don't count
  if scanner.get_next_type() == PF_IMAGE:
    scanner.advance()
  if scanner.get_next_type() == PF_DRAWABLE:
    scanner.advance()
  if scanner.get_next_type() == PF_LAYER:
    scanner.advance()
  if scanner.get_next_type() == PF_CHANNEL:
    scanner.advance()
  if scanner.get_next_type() == PF_VECTORS:
    scanner.advance()
  print "Count hidden params is ", scanner.get_count()
  return scanner.get_count() 

  
def has_runmode(params):
  ''' Does this ParamList start with a Param of type runmode?'''
  return len(params) > 0 and params[0].name == 'run-mode'
