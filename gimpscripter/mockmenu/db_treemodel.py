#!/usr/bin/env python

'''
This understands the db, viewspecs, gtk.treemodel.
IE how to load a gtk.treemodel from the db according to the viewspec for an inspector app.

Similar to classical views on a database: different ways of organizing, viewing the same data.

The viewspec tells which attributes of objects in the db are paths, types, categories (sets of types).
'''

# Does not need: from gimpfu import * 
# Hide that the db was loaded from gimp or any other specific source.

import pygtk
pygtk.require("2.0")
import gtk

import types
import string # for maketrans

# our own sub module, must be installed alongside
from gimpscripter.mockmenu import path_treemodel  # load tree by set of paths



# Constants defining the types of views
VIEW_TYPE_LIST = "List" # list view on name (no attribute from the dict value)
VIEW_TYPE_TYPE = "Type" # hierarchal view on attribute that is a type having elementary values
VIEW_TYPE_SLASHPATH = "SlashPath" # hierarchal view on attribute having values that are slash delimited paths
VIEW_TYPE_CATEGORY = "Category" # hierarchal view on attribute having values that name sets of types
# TBD use these


class ViewSpec():
  '''
  A specification of a GUI treeview of a db.
  Many treeviews per db.
  '''
  def __init__(self, viewname, attrname, attrtype, typedict, db, filterdict):
    # TBD sanity checking, types are StringType and DictType
    self.viewname = viewname  # Displayed name of the view
    self.attrname = attrname  # Attribute of objects in db.  Attribute values populate treemodel of treeview.
    self.type = attrtype  # Type of the attribute (and thus of the treeview)
    self.typedict = typedict  # Dictionary of unique values in the attribute, maps to a string for display in treeview.
    self.db = db  # Dictionary of objects to be browsed/inspected
    self.filterdict = filterdict  # db and its filter dict one-to-one


class MyModel():
  '''
  Wrapper for treemodel with other attributes: 
    a spec for a view
    a dict for filtering (in the viewspec)
  '''
  def __init__(self, name, viewspec):
    # all treemodels have the same structure: three columns of type string
    self.treemodel = gtk.TreeStore(str, str, str)
    # all sorted same way
    self.treemodel.set_sort_column_id(0, gtk.SORT_ASCENDING)
    self.viewspec = viewspec
    
  def rebuild(self, pattern):
    '''
    Search string changed.
    Rebuild filterdict and repopulate model.
  
    Performance Note: No special measures (disconnecting treeview from treemodel, or setting sort funct to None)
    since this seems fast enough.
    I tried treeview fixed_height_mode yes on row height, it didn't work.
    '''
    self.viewspec.filterdict.filter(self.viewspec.db, pattern)
    _populateModel(self)   

  def len(self):
    ''' The filtered length: count leaf rows: what user can select '''
    return self.viewspec.filterdict.values().count(True)



class TreeModelDictionary(dict):
  '''
  A read only dictionary of gtk.treemodels
  Initializes itself with data passed in a dictofviews and you can't setitem.
  '''
  
  def __init__(self, dictofviews):
    
    # Base class init
    dict.__init__(self)
   
    '''
    Fill self with data
    Build (populate) and initialize sorting of several treestore models
    (all of same signature for one view).
    These are the base models of the filtered models.
    Models are specified by dictofviews.
    '''
    for key, viewspec in dictofviews.iteritems():
      model = MyModel(key, viewspec)
      _populateModel(model)
      # put model in a dictionary by name of model
      dict.__setitem__(self, key, model)


    
  def __setitem__(self):
    raise RuntimeError, "TreeModelDictionary is read-only"


def _populateModel(model):
  '''
  Populate according to the type.
  These type names are hardcoded, used in the viewspec.
  This understands which types use which building method.
  Future: some types might need parsing into slashed paths during building.
  '''
  # Model is empty, put in a single row telling empty.
  if not model.len():
    model.treemodel.clear()
    db = model.viewspec.db
    model.treemodel.append(None, ["<None>", ""])   # second, hidden column empty so not clickable
    return
    
  if model.viewspec.type == "List":
    _build_list_tree(model)
  elif model.viewspec.type == "Type":
    _build_type_tree(model)
  elif model.viewspec.type == "SlashPath":
    _build_path_tree(model)
  elif model.viewspec.type == "Category":
    _build_type_tree(model)  
  else:
    raise RuntimeError, "Unknown model type: " + model.viewspec.type


def _build_list_tree(model):
  '''
  Build a gtk.treemodel from a dictionary of objects.
  The treemodel is a list (a tree with only one level).
  Each row in the treemodel is a key from the dictionary.
  '''
  model.treemodel.clear()
  db = model.viewspec.db
  for name in db.keys():
    if model.viewspec.filterdict[name]:  # is filtered out by search string?
      # append to treemodel in order, no parents
      piter = model.treemodel.append(None, [name, name])   # second, hidden column non-empty so clickable


  
def _build_type_tree(model):
  '''
  Build a gtk.treemodel from a dictionary of objects.
  Branch rows in the treemodel will be the set of types 
  taken from the dictionary's object's attribute that is conceptually (to the user) a type 
  (having string values from a small set).
  Leaf rows in the treemodel will be keys from the dictionary
  (which usually are the same as the ID or name attr of objects in the dictionary.)
  
  Also, the object's attribute can be a list of types (categories).
  That is, we build the same tree structure for viewtype: Type and viewtype: Category.
  For viewtype Category, a thing can appear in more than one row of the treeview.
  '''
  model.treemodel.clear()
  
  # tree structure: one level: type names, second level: leaves, names of objects having that type
  # for example, a tree whose leaves are PDB procedure names and whose branches are procedure types.
  # EG, as an image of the displayed treeview, where ^ is an icon that collapses the branch
  # treeview:   typedict:       [db[].thing.name, .ztype]:     viewspec:
  # ^Integer    (1: Integer)      foo, 1                    ("Type and Name", "ztype", "Type", typedict)
  #   foo       (2: Char)         bar, 1
  #   bar                         zed, 2
  # ^Char
  #   zed
  #
  # ^Integer    (1: Integer)      foo,  Integer,Char        ("Type and Name", "ztype", "Category", typedict)
  #   foo       (2: Char)         bar,  Integer
  #   bar                         zed,  Char
  # ^Char
  #   foo *appears in two types
  #   zed
 
  db = model.viewspec.db
  
  type_to_row = {}
  SEP = string.maketrans(',', ' ')
  
  # add parent rows to treemodel, remembering the tree path.
  # treerowreferences are persistent, treeiters and treepaths are not, so convert back and forth
  # do parents first, then children, so can raise exceptions for missing parents.
  for parent in model.viewspec.typedict.keys():  # for each unique value of the type
    # Parent means parent row in the treemodel.
    # Translate to friendly displayed string, different from type strings in the db
    displayedtype = model.viewspec.typedict[parent]
    piter = model.treemodel.append(None, [displayedtype, ""])   # second, hidden column empty
    row = gtk.TreeRowReference(model.treemodel, model.treemodel.get_path(piter))
    type_to_row[parent] = row
  # add child rows to treemodel, looking up parent tree path
  for name, thing in db.iteritems(): # EG key is name, value is an object with an attribute that is a type.
    if not model.viewspec.filterdict[name]:  # is filtered out by search string?
      continue
    # Get the value of the thing's attribute.  The value is 'of the type'.
    # The name of the attribute is given in the viewspec for the model.
    value = eval("thing." + model.viewspec.attrname)
    # !!! Value can be a list of type names (a category)
    if model.viewspec.type == "Category":
      # For now, categories cannot be encoded, must be str
      # list words in commma OR whitespace delimited string
      # First translate commas to whitespace, then split on any whitespace
      valuelist = value.translate(SEP).split()
      if len(valuelist) < 1:
        valuelist = ["NA"]  # the type of an empty category
        # Note that it is better to insure the db has no empty category values, substitue "NA" at load time
      for avalue in valuelist:
        try:
          parentrow = type_to_row[avalue]
          piter = model.treemodel.get_iter(parentrow.get_path())
          model.treemodel.append(piter, [name, name]) # second use is as ID of procedure   
        except KeyError:
          print "Key error: type not found in viewspec.typedict: ", avalue
    else: # viewtype is Type. 
      try:
        parentrow = type_to_row[value]
        piter = model.treemodel.get_iter(parentrow.get_path())
        model.treemodel.append(piter, [name, name]) # second use is as ID of procedure   
      except KeyError:
        print "Key error: type not found in viewspec.typedict"
 

        
  ''' OLD
  # outer loop on unique values of the type, inner loop on the entire db
  for parent in model.viewspec.typedict.keys():  # for each unique value of the type
    # Parent means parent row in the treemodel.
    # Translate to friendly displayed string, different from type strings in the db
    displayedtype = model.viewspec.typedict[parent]
    piter = model.treemodel.append(None, [displayedtype, ""])   # second, hidden column empty
    # for each thing in the db by name
    print "Type: ", parent
    for name, thing in db.iteritems(): # EG key is name, value is an object with an attribute that is a type.
      if not model.viewspec.filterdict[name]:  # is filtered out by search string?
        continue
      # Get the value of the thing's attribute.  The value is 'of the type'.
      # The name of the attribute is given in the viewspec for the model.
      value = eval("thing." + model.viewspec.attrname)
      # !!! Value can be a list of type names (a category)
      if model.viewspec.type == "Category":
        valuelist = value.split(',')  # list words in commma delimited string
        # For now, categories cannot be encoded, must be str
        # !!! TBD No exception if some or all of the types in the category are not in the typedict.
        if parent in valuelist:
          # Put the name of the thing in the view, second hidden column is as an ID
          model.treemodel.append(piter, [name, name])
      else: # viewtype is Type. 
        # If there is a mapping of types to other (friendly?) strings
        #if model.viewspec.typedict :
          # Decode numeric (or otherwise) values to strings
          # KeyError exception raised if not in typedict
        #  value = model.viewspec.typedict[value]
        # If it matches the type of the outer loop (branch of the treemodel)
        print "Value: ", value
        if  value == parent:
          print "Adding row"
          model.treemodel.append(piter, [name, name]) # second use is as ID of procedure
'''

def _build_path_tree(model):
  '''
  Understands:
  tree is path tree
  tree is given as a db of things having paths
  thing names installed at the path tree leaves (alternative).
  '''
  print "Building path tree model"
  model.treemodel.clear()
  db = model.viewspec.db
  count = 0
  
  # For each (name, thing) in the db
  # Load tree from db[name].attrname.menupath
  for name, thing in db.iteritems():
    if model.viewspec.filterdict[name]:  # is filtered in by search string?
      if model.viewspec.attrname: # names are unique and attribute gives a path
        try:
          pathvalue = eval("thing." + model.viewspec.attrname)
        except:
          # Likely source of configuration errors, print more info.
          print "Inspect db must contain objects having repr method and attribute holding a path" 
          raise
      else:
        pathvalue = name  # the name itself is a path 
      assert pathvalue != ""  # !!! Each must have a path, even if just <Unknown>
      
      # Add thing to the treemodel
      # Formerly,we just adding the name of the thing.
      # Now we pass the thing along, and extract thing.name and more attributes, later
      if not path_treemodel.add_path(model.treemodel, thing, pathvalue):
        print "Duplicate path:", pathvalue, "to ID:", name
        # raise RuntimeError
      else:
        count += 1
  print "Count path tree model: ", count

