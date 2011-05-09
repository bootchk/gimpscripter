#!/usr/bin/env python

'''
Glue between Makeshortcut plugin and pygimp pdb.

Derived from inspector.inspectpdb.py (see it for more notes.)

Reimplement pdb from pygimp:
  Make it iterable (a full dictionary)
  Add __repr__ method that documents a procedure
  Add extra attributes.
  Limit it to plugins.

Also define views on the db, for use by the app.

The general API for glue objects between a treeview and its data:
  dictofviews object a dictionary of viewspecs on a db object,
  dictionary of objects with attributes and repr method (referred to as the db.)
  a filter dictionary: boolean valued with same keys as the db
Many viewspecs can all refer to the same dictionary of objects

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


import gimpfu
import gimp
import gimpenums  # for proctypes
import types
import time

# our own submodules
from gimpscripter.mockmenu import db_treemodel
from gimpscripter.mockmenu import map_procedures
from gimpscripter import macros


# Dictionaries of types in the conceptual model

'''
This used to map integer types to strings on loading from the PDB.
Programming surprise: some docs say constants are like PROC_PLUG_IN, others say GIMP_PLUG_IN
Constants defined by gimpenums are same as in libgimp but without prefix GIMP_ e.g. GIMP_EXTENSION -> EXTENSION
'''
proctypedict = {
  gimpenums.PLUGIN : "Plugin",
  gimpenums.EXTENSION : "Extension",
  gimpenums.TEMPORARY : "Temporary",
  gimpenums.INTERNAL : "Internal",
  -1 : "Unknown"   # Hope this doesn't conflict or change
  }




class Procedure:
  '''
  Procedures in the Gimp PDB.
  Mimics the attributes exposed by the PDB.
  Unifies ALL the exposed attributes of any type of procedure.
  Even attributes that aren't readily available from Gimp.
  Implements repr for str()
  '''
  # TBD catch ValueError on decode ?
  
  # Note it is important to properly default those attributes that we build views on
  def __init__(self, name, accel, loc, time, menupath = "<Unknown>", imagetype="<Unknown>",
      blurb="missing", help="", author="", copyright="", date="", proctype=-1 ):
      
    # global proctypedict
    
    # attributes returned by gimp_plugin_query
    self.name = name
    self.menupath = menupath
    self.accel = accel
    self.loc = loc
    self.imagetype = imagetype
    self.time = time
    # attributes returned by gimp_procedural_db_proc_info
    self.blurb = blurb
    self.help = help
    self.author = author
    self.copyright = copyright
    self.date = date
    self.type = proctypedict[proctype]
    # other attributes that can be discerned, eg by inference or parsing source files
    self.filename = "Unknown"
    self.language = "Unknown"
    
  
  def __repr__(self):
    '''
    Return text describing procedure.
    
    Future: different formats for different types
    Future: formatted
    Future: highlight the search hits
    '''
    # print self.__dict__
    text = ""
    for attrname, attrvalue in self.__dict__.iteritems():
      if attrvalue is None: # Don't know why pygimp didn't do this earlier?
        attrvalue = ""  # Must be a string
      if not isinstance(attrvalue, types.StringType) :
        print "Non string value for attr:", attrname, "of:", self.name
        attrvalue = "***Non string error***"

      text = text + attrname + ': ' + attrvalue + "\n"
    return text

    
  def update(self, blurb, help, author, copyright, date, thetype):
    '''
    TBD generalize 
    '''
    self.blurb = blurb
    self.help = help
    self.author = author
    self.copyright = copyright
    self.date = date
    self.type = proctypedict[thetype]


def standardize_menu_path(path):
  # Delete <> from the menupath
  result = path.translate(None, '<>')
  # Strip leading "Image/"
  # Since for our use, that is implied
  if result.startswith("Image/"):
    result = result.replace("Image/", "", 1)
  return result


class Pdb(dict):
  '''
  A read only dictionary of objects of type Procedure mimicing the Gimp PDB.
  For now, it initializes itself with data.
  You can also add items.
  '''
  
  def __init__(self):
    
    # Base class init
    dict.__init__(self)
   
    # Fill self with data from Gimp PDB
    
    # Query the plugins, which have different attributes exposed.
    # !!! Here we want the menupath.
    # Empty search string means get all.  Returns count, list, ...
    c1, menupath, c2, accel, c3, loc, c4, imagetype, c5, times, c6, name = gimp.pdb.gimp_plugins_query("")
    
    for i in range(0,len(name)):

      # Create new procedure object
      procedure = Procedure(name[i],  accel[i], loc[i],
        time.strftime("%c", time.localtime(times[i])),  # format time.  TBD convert to UTF8
        standardize_menu_path(menupath[i]),
        imagetype[i],
        blurb = gimpfu.pdb[name[i]].proc_blurb )  # Additional fields directly from gimpfu.pdb
        # Note the attr in the gimpfu.pdb are named proc_foo.
        
      # Note about future development:
      # pygimp wraps pdb.gimp_procedural_db_get_data as gimp.pygimp_get_data(name[i])
      # data will be the default parameters for plugins written in C.
        
      dict.__setitem__(self, name[i], procedure)
    
  def __setitem__(self, key, value):
    # This allows the Pdb to be supplemented
    dict.__setitem__(self, key, value)
    # raise RuntimeError, "Pdb does not allow adding procedures"
  
  # iterator methods, and all other special methods, inherited from base
  # No overriding is necessary.



def append_gimp_internal_procedures(plugindb):
  '''
  Supplement given dictionary with a subset of gimp internal procedures.
  Subset is: only those most useful to plugin creators.
  
  Cases for whether internal procedure have menupath presence in Gimp menus:
  
  - No : we fabricate a menu item.
  - Yes: no programmatic way to discern, we hand coded corresponding Gimp menu item.
  
  Minimal procedure descriptors: having at least:
  
  - the attribute declared in viewspec: menupath
  - imagetype
  
  Pygimp pdb does not expose the imagetype as attribute of a PDB function.
  gimp-procedural-db-query also does not return the imagetype.
  Imagetype blank or "*" means available for all image types.
  TODO decide whether some internal procedures have imagetype contraints.
  gimp-flatten does not apply when there IS no alpha, and throws an exception?
  '''
  for menupath, procname in map_procedures.menu_to_procname.items():
    if procname in plugindb :
      print "Supplemental menu ", menupath, " is duplicate path to plugin ", procname
      # But go ahead and add it

    if macros.is_macro(procname):
      plugindb[procname] = Procedure(procname, 
        "bar", "bar", "bar", # accel, loc, time all unknown
        menupath, # <= from the map
        imagetype="", # unknown
        blurb = macros.get_blurb(procname) # lookup
        )
    else: # Gimp internal procedure
      # Many fields unknown for PDB procedures that are not plugins
      plugindb[procname] = Procedure(procname, 
        "bar", "bar", "bar", # accel, loc, time all unknown
        menupath, # <= from the map
        imagetype="", # unknown
        blurb = gimpfu.pdb[procname].proc_blurb # lookup
        )
    


'''
This is the meat of this glue module:
define views on an augmented PDB.
'''
# make a dictionary of plugin descriptors, keyed by name
plugindb = Pdb() # db of plugins, exported, a main product
append_gimp_internal_procedures(plugindb) 

# TODO the rest of this should be in another module

# A map that defines what rows appear in the gtk.treeview
# TBD make it show only plugins that are not shortcuts !
# ie no need for a shortcut to a shortcut.
pluginfilterdict = {}
for name, value in plugindb.iteritems():
  pluginfilterdict[name] = True # show all

dictofviews = {}  # Exported, a main product


dictofviews["Procedures by menu path"] = db_treemodel.ViewSpec("Procedures by menu path", "menupath", "SlashPath", None, plugindb, pluginfilterdict)


if __name__ == "__main__":
  # test
  # Currently, this doesn't work: abort at wire to gimp
  # That is, gimp must be running.
  import sys
  
  # gimp module is .so in /usr/lib/gimp/2.0/python
  # gimpfu.py in /usr/lib/gimp/2.0/plug-ins
  sys.path.append('/usr/lib/gimp/2.0/python')
  import gimp
  
  # test 
  mypdb = Pdb()
  
      
    
