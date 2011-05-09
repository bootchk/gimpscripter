#! /usr/bin/python
'''
Gimpscripter main GUI.

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

import pygtk
pygtk.require("2.0")
import gtk

# Our own sub modules, installed in same directory as this file.
# These are independent of db
from gimpscripter.mockmenu import db_treemodel
from gimpscripter.mockmenu import path_treemodel
from gimpscripter import generate
from gimpscripter import specification  # bundle of data drives generation
from gimpscripter.gui import param_dialog



# Make fully qualified path so pygtk finds glade file.
# Get glade file from same directory as this file (must be together)
import os.path
UI_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gimpscripter.glade')



class gimpscripterApp(object): 
  
  def __init__(self, dictofviews):
    
    # Note: use self for all variables accessed across class methods,
    # but not passed into a method, eg in a callback.
    
    self.dictofviews = dictofviews  # dictionary of views that drives this app
    self.currentviewname = dictofviews.keys()[0]  # arbitrarily the first
    
    self.selected_command_index = None
    self.is_settings_valid = True # Initially, nonexistant settings are valid.
    
    '''
    One treemodel, a menu tree of plugins.
    Data driven construction of a set of treemodels as specified by a dictofviews.
    Also populates and sorts treemodels.
    Note: ignore any treestore model from glade, don't: model = builder.get_object("treestore1")
    '''
    self.models = db_treemodel.TreeModelDictionary(self.dictofviews)
    
    self.spec = specification.GimpScripterSpec()
    
    builder = gtk.Builder()
    if not builder.add_from_file(UI_FILENAME):
      raise RuntimeError, "Failed to open glade file."
    
    # Get references to widgets for use in callbacks
    self.mainwidget =     self.safe_build(builder, "dialog1")
    self.OKbutton =       self.safe_build(builder, "button1")
    self.mockmenu =       self.safe_build(builder, "treeview1")
    self.command_seq_listview = self.safe_build(builder, "treeview2")
    self.name_textentry = self.safe_build(builder, "entry1")
    
    # parent of parameter_widgets
    self.parameter_box = builder.get_object("vbox1")
    self.parameter_widgets = []   # built dynamically
    
    # Initial internal GUI state.
    self.OKbutton.set_sensitive(False)
    
    '''
    Selection handling: connect selection event to callback function.
    Note a treeselection object is always part of a treeview: no need to create in glade
    I don't think this is done by connect_signals() above, since selection objects are not in glade?
    '''
    # Mock menu tree
    self.mockmenu.get_selection().connect("changed", self.on_mockmenu_selection_changed)
    # Connect pre-selection event to callback function that determines what can be selected
    self.mockmenu.get_selection().set_select_function(self.filter_select_menu_item)
    
    # Commands list
    self.command_seq_listview.get_selection().connect("changed", self.on_commands_selection_changed)
    self.command_seq_listview.get_selection().set_select_function(self.filter_select_command) # Filtered: any row can be selected except
        
    # Set model of treeview to the treemodel of the current viewspec
    self.mockmenu.set_model(self.models[self.currentviewname].treemodel)
    
    # Set tooltips to be blurb column
    self.mockmenu.set_tooltip_column(2)
    
    builder.connect_signals(self)

  
  def safe_build(self, builder, name):
    ''' 
    Call GTKBuilder to find a GTK widget in the glade file.
    Fail if not found.
    Return reference to the built widget.
    '''
    gtk_object = builder.get_object(name)
    if gtk_object is None:
      raise RuntimeError("GTKBuilder error: glade file mismatches code")
    return gtk_object
    
    
  def main(self):
    self.mainwidget.show_all() # April 2011 WAS show()
    gtk.main()  # event loop
    
    
  '''
  Callbacks.
  
  !!! Note that here assistant is NOT a widget but an enclosing class.
  In callbacks, widget is the assistant.mainwidget.
  '''
  
  def on_buttonOK_clicked(self, widget):
    ''' Save and present summary dialog'''
    print "OK button"
    self.apply()
    
  def on_buttonCancel_clicked(self, widget):
    ''' TODO confirm'''
    gtk.main_quit()
    
  def on_dialog1_close(self, widget):
    ''' TODO confirm'''
    gtk.main_quit()
  
  def message_dialog(self, message):
    ''' Display a modal summary dialog with no parent and no buttons'''
    dialog = gtk.MessageDialog(flags = gtk.DIALOG_MODAL, 
      buttons=gtk.BUTTONS_OK,
      type=gtk.MESSAGE_INFO, 
      message_format=message)
    dialog.run()  # run, not show, to wait for user response
    dialog.destroy()


  def apply(self):
    '''
    Do the main action:
    create a plugin.
    
    GimpScripter should be atomic: don't do anything permanent unless it all can be done.
    That is, no cleanup on cancel.
    '''
    self.validate_and_capture_parameters(self.selected_command_index) # Capture parameters for selected command
    self.spec.wrapping.set_menu_name(self.name_textentry.get_text()) # Put final name in  spec
    print self.spec.commands.param_list
    generate.generate(self.spec)
    self.mainwidget.destroy()
    self.message_dialog(generate.summarize()) # Wrapper is generated, but summarize
      
   
  """
  def create_labels(self):
    for i in range(0, 20):
      # pack a separator in the vbox
      print "Put label in vbox"
      label = gtk.Label("foo")
      #label.set_use_underline(True)
      label.set_alignment(0.1, 0.5)
      label.show()
      self.parameter_box.pack_start(label, expand=False)
      self.parameter_widgets.append(label)
  """  
  
  def destroy_old_parameter_widgets(self):
    ''' Destroy old widgets, really only one, a GtkTable '''
    if self.parameter_widgets:
      for widget in self.parameter_widgets:
        print "Destroy", widget
        widget.destroy()
        self.parameter_widgets.remove(widget)
    
  def create_parameter_widget(self, pdefs, defaults, toggles):
    ''' 
    Create one parameter widget and pack front into a GtkBox. 
    The created widget is usually a GtkTable, one row per parameter.
    This returns a wrapper of the GtkTable.
    '''
    table = param_dialog.GimpParamWidget(
      self.parameter_box, # pack parameter widgets in this box
      self.mainwidget, # parent window, for error dialogs
      pdefs,
      defaults,
      self.set_sensitive_settings_valid, # Callback when user touches a widget
      is_use_toggles = True,
      toggle_label="Constant",
      toggle_initial_values= toggles)
    return table


  def prepare_parameter_page(self, commands, index, is_first_time=False):
    '''
    Prepare  dynamic widgets for  parameter page.
    Dynamic: depends on count and type of parameters.
    Its parent and window is the parameter page (a scrolling window child of assistant)
    Index is the index of the newly selected command.
    is_first_time: whether this is a new command, use defaults instead of user-entered values
    '''
    assert commands # should not get here with empty commands
    
    if self.selected_command_index is not None: # If parameters for some command are displayed
        self.validate_and_capture_parameters(self.selected_command_index) # capture displayed parameters
        self.destroy_old_parameter_widgets()
        
    self.selected_command_index = index

    """
    # Create a set of parameter widgets, one for each command, packed into a vbox.
    for i in range(0, len(commands)):
      command = commands.get_command_for(i)
      print "Param widget for", command.name
      
      # Then: commands.param_list.get_nonhidden_pdefs_for(i)
    """
    
    pdefs = commands.param_list.get_nonhidden_pdefs_for(index)
    if pdefs:
      if is_first_time: # if first time displaying parameters for this command
        values = commands.param_list.get_nonhidden_defaults_for(index)  # Display defaults
        toggles = [False for i in range(len(values))]  # Toggles all initially False, not deferred
      else:
        # Restore widget to previous appearance when user last viewed it
        values = commands.param_list.get_nonhidden_values_for(index) # Display values user entered previously
        toggles = commands.param_list.get_defers_for(index)  # Display previous toggle values
        print "Len toggles", len(toggles)
      # Put nonhidden parameters of indexth command into new widget
      self.parameter_widgets.append(self.create_parameter_widget(pdefs, values, toggles))
    # else no parameters to show
    
    # Must capture parameters before generating in case this is last command and user never touches it



  def validate_and_capture_parameters(self, index):
    '''
    Validate user entered parameters and capture to the spec.
    For the one command whose parameters are displayed.
    !!! But the command might not have any parameters.
    '''
    print "Validating parameters for command ordinal", index
    if self.parameter_widgets:
      self.spec.commands.param_list.preset(*self.parameter_widgets[0].validate(), command_index=index)
 
  
  '''
  Routines to sensitize buttons
  ''' 
  def set_sensitive_settings_valid(self, direction):
    '''
    A callback from parameter widget when touched and loses focus.
    Direction is False if invalid entry.
    '''
    self.is_settings_valid = direction


  def set_sensitive_completion(self):
    ''' Set sensitive buttons if complete '''
    # If:
    # - user entered at least one command 
    # - and named the wrapper
    # - and settings are valid
    is_sensitive = len(self.name_textentry.get_text()) > 0 \
      and len(self.spec.commands) > 0 \
      and self.is_settings_valid
    self.OKbutton.set_sensitive(is_sensitive)


    
  '''
  Callbacks for child or grandchild widgets (widgets in pages of the assistant.)
  '''
  """
  def on_radiobutton_toggled(self, button):
    '''
    Both radiobuttons signal to this handler.
    Grouping handled by gtk/glade.
    Since there are only two buttons, ignore which is calling back.
    '''
    # If user wants to preset parameters instead of use last values
    is_preset = self.radiobutton_usepreset.get_active()
    # Sensitize the parameter widgets / tables
    for widget in self.parameter_widgets:
      widget.set_sensitive(is_preset)
    self.spec.command.set_is_use_last(not is_preset) # the model
  """  
    
  
  def on_entry1_changed(self, widget):
    ''' Signal when user types or deletes a character or pastes, etc. In name TextEntry. '''
    self.set_sensitive_completion()
 
 
  def on_mockmenu_selection_changed(self, theSelection):
    '''
    Callback for mockmenu to choose a target command.
    Treeview widget, signal=selectionChanged on theSelection which is a gtk.TreeSelection 
    Action: keep a GUI state variable showing user has made selection.
    Single selection is enforced by default.
    '''
    
    if not self.is_settings_valid:
      return  # TODO disallow the click beforehand
      
    global is_new_proc_selection
    is_new_proc_selection = True
    
    model, path = theSelection.get_selected()
    # path is a GTK_tree_iter
    if path: # if selection was made
      # Alternative: column 1 (hidden?) drives selection (ie is the model value)
      name = model.get_value(path, 1) # column 1 is procname
      menupath = path_treemodel.get_path_string(model, path)
    else:
      name = None
      menupath = None
      
    if name:
      try:
        # Every click, add a command
        # For now, append
        # TODO insert in position selected in the command list widget
        command = specification.CommandSpec(name, menupath)
        self.spec.commands.append(command)
        # Feed it back
        self.command_seq_listview.get_model().append([menupath])  # tuple of column values
        
        # It is focused in the mock menu.  Unselect anything in the command list.  OR select the newly appended command.
        self.command_seq_listview.get_selection().unselect_all()
        
        # Show parameters, for the first time
        self.prepare_parameter_page(self.spec.commands, len(self.spec.commands)-1, is_first_time = True)
      except:
        '''
        Certain plugins raise KeyError on parameters e.g. image/colors/map/rearrange on INT8ARRAY
        Or for any other exception, disallow proceeding.
        User must choose another plugin, or Cancel.
        '''
        param_dialog.warning_dialog(self.mainwidget, "GimpScripter exception: the item you chose can't be used.")
        raise # Exception to stderr (a property of gtk is to not crash on exceptions.)
      else: # try succeeded
        self.set_sensitive_completion() # Possibly allow user to complete
  
  
  def on_commands_selection_changed(self, theSelection):
    '''
    Callback for commands list to select a target command.
    Treeview widget, signal=selectionChanged on theSelection which is a gtk.TreeSelection 
    Action: show the parameters for this command
    Remember this is a hint, there might not be a selection.
    '''
    model, path = theSelection.get_selected()
    # path is a GTK_tree_iter
    if path: # if selection was made
      # Alternative: column 1 (hidden?) drives selection (ie is the model value)
      menupath = model.get_value(path, 0) # column 0 is command menupath, a string
      intpath = model.get_path(path)  # get [int,int] form of path
      index = intpath[0]  # index of theSelection
    else:
      pass
      
    # unselect in the mock menu
    self.mockmenu.get_selection().unselect_all()
    
    self.prepare_parameter_page(self.spec.commands, index )
     
  
  ''' Callbacks when user clicks in a treeview.  Return whether to allow selection. '''
     
  def filter_select_menu_item(self, path):
    '''
    Callback: return boolean indicating whether selection is allowed.
    Let user select only leaves.
    Filters user's clicks in a mockmenu, and ignores those clicks that are not in leaves.
    !!! Also disallow clicks if settings are invalid.
    '''
    '''
    Note: tree levels without children are a complication.
    The definition of a leaf here is: row with non-empty second, hidden column.
    If search filtering takes out all leaf rows under a tree level row,
    that tree level row has no children.
    If we choose to display tree level rows without children,
    then definition of leaf is not: has no children.
    '''
    if not self.is_settings_valid:
      self.message_dialog("You can't select another command while settings are invalid for the current command.")
    model = self.mockmenu.get_model() # !!! Get treeview's model, which varies in this app.
    return model.get_value(model.get_iter(path), 1) != "" and self.is_settings_valid
    # WAS return not model.iter_has_child(model.get_iter(path)) # no child means leaf
      
      
  def filter_select_command(self, path):
    ''' Disallow selection in command list if settings for current command are invalid '''
    if not self.is_settings_valid:
      self.message_dialog("You can't select another command while settings are invalid for the current command.")
    return self.is_settings_valid

