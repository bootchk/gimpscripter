#!/usr/bin/env python

'''
TBD should be renamed: load_treemodel_from_paths
TBD an outer procedure that understand the db contains the paths?

Load tree into gtk.treestore,
where tree given as set of paths for leaves.
In a path, items delimited by slash.
Typically path is menupath or filepath.

This is independent of the application, ie generic.
Augments treemodel with an API for adding paths.

Here, using two or more columns.
All rows except for leaves have column 0 path item, empty column 1, etc.
Leaf rows have empty column 0, column 1 is the internal ID of the object the path leads to.
That is, the path is user strings, but the ID is internal.
If your app doesn't make a distinction, just redundantly use the last item in path for leaf value.
This does NOT allow multiple rows with the same path, and different leaf values.
Column two might well be hidden from user view.
'''

'''
Programming notes:
Another way to do this might use gtk.treerows, something like this search:
(where iterchildren() is different from iter_children since it is a real iterator.)

for row in treemodel: # top level
  if match_row(...)
  
def match_row(rows, value):
    if not rows: return None
        for row in rows:
            if row[0] == value: return row
            result = match_row(row.iterchildren(), value)
            if result: return result
    return None
'''

'''
Programming notes:
!!! Surprise, the root is NOT always there, can be None. 
!!! get_iter_root is the same as get_iter_first, which is better named.
'''

import warnings

# This string constant should be used in the db
# for any paths that are not known
UNKNOWN_PATH_STRING = "<Unknown>"

def add_path(model, leaf, path):
  '''
  Add path to treestore, if not already there.
  Here, the path is a slash delimited string.
  Leaf is an object to added.
  Leaf must have a name attribute.
  Returns True if path was added, False if already exists.
  '''
  # print leaf, path
  items = path.split('/') # parse path into items
  if len(items) < 1:
    warnings.warn("Empty path for leaf " + str(leaf))
    return False
  # Sanity checking for "//" in path
  for item in items:
    if not item:
      warnings.warn("Empty submenu in path: %s" % path)
  # In beginning, don't have a parent.
  return __add_path_from_node(model, None, items, leaf)


def get_path_string(model, iter):
  ''' Get a slash delimited string for a path given by iter, a treeIter. '''
  iter_string = model.get_string_from_iter(iter)
  node_strings = iter_string.split(':')
  slashpath = ""
  pathstring = ""
  for node in node_strings:
    pathstring += node
    path = model.get_iter_from_string(pathstring)
    node_label = model.get_value(path, 0)
    slashpath += node_label
    pathstring += ':'
    slashpath += '/'
  slashpath = slashpath[0:len(slashpath)-1] # elide last slash
  return slashpath

"""
def __model_append(node, values):
  ''' Put a row in the model. This hides the number and type of columns we are adding'''
  in progress refactoring
"""
  
def __add_path_from_node(model, parent, pathitems, leaf):
  '''
  Add path below parent, if not already there.
  This is private, recursive.
  Parent can be None
  Path is a list of items, not a string.
  Leaf is object to add as leaf.
  '''
  if not parent:  # first call in recursion
    iternode = model.get_iter_first()
  else:
    iternode = model.iter_children(parent)
  while iternode:
    if pathitems[0] == model.get_value(iternode, column=0): # if match
      if len(pathitems) <= 1:
        # Found the complete path
        if pathitems[0] == UNKNOWN_PATH_STRING : # if lacking a meaningful path
          # New child here (under <None or Unknow> at top level.)  
          # Note this makes the treeview leaves appear to user as two kinds:
          # 1) real leaf path items, 2) and names of things without path
          model.append(iternode, [leaf.name, leaf.name, leaf.blurb])
          return True
        elif model.get_value(iternode, 1) != leaf.name: # column 2
          # This is a collision, two different things want the same path
          # TBD print a warning only if the viewspec specifies single occupancy
          print "Differing leaf names for same path:", leaf.name, ":", model.get_value(iternode, 1)
          return False
        else:
          # This is a duplicate, the same named thing wants a path item twice.
          # Could be a different version?
          # Whether this is unexpected depends on the conceptual model of things,
          # and on enforcement earlier.
          print "Same leaf value requested path twice", str(leaf)
          return False
      # Else, match but more path to match
      del pathitems[0]  # advance in suffix
      # recurse on suffix of path, matching child
      return __add_path_from_node(model, iternode, pathitems, leaf)
      break
    else: # no match, next sibling
      iternode = model.iter_next(iternode)
  else: # no break (not matched) and iternode is None (no more siblings)
    # Add new path at this level, below parent, with any sibling
    # !!! If tree is empty, parent is None
    __add_path_suffix(model, parent, pathitems, leaf)
    return True
 

def __add_path_suffix(model, parent, pathsuffix, leaf):
  '''
  Add new path suffix to treestore below parent.
  Parent can be None for case: at a row at top level. 
  Path suffix is list of items, not a path string.
  '''
  assert pathsuffix # Pathsuffix CANNOT be empty.
  # Add rows in model for the path
  for item in pathsuffix:
    # parent becomes the new row for next iteration.
    # See gtk doc: append(parent,..) means below parent or at toplevel if parent None.
    # First column the path item, second column empty.
    parent = model.append(parent, [item, "", ""]) 
  # Change row in model for leaf.  
  # Note we just added it above, but with null values
  # Second (hidden?) column holds leaf value.
  model.set_value(parent, 1, leaf.name)  # column 2
  # !!! This is where we make col 3 (which is tooltip) a cat of name and blurb
  # TODO this should be decided elsewhere?
  model.set_value(parent, 2, leaf.name + ": " + leaf.blurb)  # column 3


if __name__ == "__main__":
  # test 
  import pygtk
  pygtk.require("2.0")
  import gtk
  treemodel = gtk.TreeStore(str, str)  # note use Python type, not GTK constant
  add_path(treemodel, "foo/bar", "foo")
  add_path(treemodel, "foo", "foo")
  add_path(treemodel, "bar", "foo")
  print treemodel
  

  
