#! /usr/bin/python

'''
GUI to ask user for parameters of a plugin.

Differs from the normal dialog (done by gimpfu):
-doesn't run the plugin on OK button
-adds a toggle button to each parameter, meaning defer entry till later
-not necessarily in a dialog

Returns:
-tuple of actual parameters that the user entered (or the initial values.)
-tuple of toggle states (boolean) for each parameter

If the user declines to enter a value for a parameter,
the initial value is returned.

Note the initial values are not the "default" values of the plugin,
or the last values used,
since for now, is hard to get for all but Python plugins.

(I suppose this is general enough that the toggle could mean something else.)

Largely derived from gimpfu.py.
They should be unified.

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

# This program can NOT be called standalone: depends on GIMP environment.

from gimp import locale_directory
from gimpenums import *
# certain param types: their widgets require special treatment
from gimpfu import *

import pygtk
pygtk.require('2.0')

import gimpui
import gtk
import operator   # for not_

from gimpscripter.gui import param_widgets    # Future refactoring: should be shared with gimpfu, verbatim.



import gettext
t = gettext.translation('gimp20-python', locale_directory, fallback=True)
_ = t.ugettext



# From gimpfu but not needed? class error(RuntimeError): pass

# Raised by dialog
class CancelError(RuntimeError): pass



'''
def get_defaults(proc_name):
   
    import gimpshelf
    (blurb, help, author, copyright, date,
     label, imagetypes, plugin_type,
     params, results, function, menu, domain,
     on_query, on_run) = _registered_plugins_[proc_name]

    key = "python-fu-save--" + proc_name

    if gimpshelf.shelf.has_key(key):
        return gimpshelf.shelf[key]
    else:
        # return the default values
        return [x[3] for x in params]
'''
'''
I think that _registered_plugins_ only contains the set of plugins
registered during this execution of the plugin.py file.
gimpshelf can contain the last parameters for any prior invocation of the plugin,
since the life of the shelf.
When is the shelf renewed, and what if a procedure's parameter signature has changed?
'''
    
def get_defaults(proc_name, paramdefs):
    '''
    What it is:
    the 4th column of the registration (only available in the original, Python plugin.)
    
    What it should be:
    More generally, for any plugin, not just Python plugins.
    Gets the persisted parameter values changed by user on previous interaction,
    else the standard parameter values declared at plugin creation.
    '''
    return [x[3] for x in paramdefs]


 
def interact(proc_name, paramdefs):
    '''
    This is a test harness.
    
    paramdefs are the paramdefs from the PDB, not from Pygimp.
    !!! Thus, they don't have the default (initial) values.
    '''

    def run_script(run_params, toggles):
        print "Result", run_params, toggles

    # short circuit for no parameters ...
    if len(paramdefs) == 0:
        print "Don't call if no params"
        return
    
    '''
    Here, defaults is the len of non-hidden params.
    Gimpfu.py does something different.
    '''
    defaults = get_defaults(proc_name, paramdefs)

    # Build the dialog
    dialog = parameter_dialog(proc_name, 
        run_script,
        paramdefs,
        defaults,
        blurb = "blurb",
        is_use_toggles=True,
        is_use_progress=False)
        
    gtk.main()

    if hasattr(dialog, 'res'):
        res = dialog.res
        dialog.destroy()
        return res
    else:
        dialog.destroy()
        raise CancelError


'''
Verbatim from gimpfu.interact().
Would import them, but they are hidden in a nested scope.
'''
def warning_dialog(parent, primary, secondary=None):
    # MODAL means parent can't be canceled to kill both
    # DESTROY_WITH_PARENT means parent CAN be canceled to kill both
    # ??? would the warning reappear and prevent user from exiting?
    dlg = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, # gtk.DIALOG_DESTROY_WITH_PARENT,
                                    gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE,
                                    primary)
 
    def response(widget, id):
        widget.destroy()

    dlg.connect("response", response)
    dlg.show()
    # gimpfu.py used: dlg.run(), dlg.destroy()



def error_dialog(parent, proc_name):
    import sys, traceback

    exc_str = exc_only_str = _('Missing exception information')

    try:
        etype, value, tb = sys.exc_info()
        exc_str = ''.join(traceback.format_exception(etype, value, tb))
        exc_only_str = ''.join(traceback.format_exception_only(etype, value))
    finally:
        etype = value = tb = None

    title = _("An error occured running %s") % proc_name
    dlg = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                                    gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                                    title)
    dlg.format_secondary_text(exc_only_str)

    alignment = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
    alignment.set_padding(0, 0, 12, 12)
    dlg.vbox.pack_start(alignment)
    alignment.show()

    expander = gtk.Expander(_("_More Information"));
    expander.set_use_underline(True)
    expander.set_spacing(6)
    alignment.add(expander)
    expander.show()

    scrolled = gtk.ScrolledWindow()
    scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scrolled.set_size_request(-1, 200)
    expander.add(scrolled)
    scrolled.show()


    label = gtk.Label(exc_str)
    label.set_alignment(0.0, 0.0)
    label.set_padding(6, 6)
    label.set_selectable(True)
    scrolled.add_with_viewport(label)
    label.show()
    
    def response(widget, id):
        widget.destroy()

    dlg.connect("response", response)
    dlg.set_resizable(True)
    dlg.show()
'''
End of verbatim from gimpfu.interact()
'''


class GimpParamWidget(object):
  '''
  Hides a widget that lets user set and defer actual parameters to a Gimp plugin.
  This widget holds many parameters (this widget a GtkTable.)
  '''    
 
  def __init__(self, 
    packable_box,  # a packable widget i.e. vbox or hbox
    parentwindow, # a window to parent error dialog, parent of packable_box
    paramdefs, 
    defaults, # initial values of widgets
    advance_callback, # callback to caller to enable user advances in the GUI state machine
    is_use_toggles=False,
    toggle_label="Use",
    toggle_initial_values=[] # initial value of toggles
    ):
    
    '''
    Build a Table widget of Gimp parameter editing widgets.
    Pack the table into packable_box, nested in parentwindow.
    Takes a callback to be called with Boolean whenever the validity of the table changes.
    Used to set sensitive widgets in the parent.
    '''
    self.advance_callback = advance_callback
    self.is_use_toggles = is_use_toggles
    
    # Validation differs from gimpfu
    # Note we validate again later.
    def _validate_entry(wid):
      try:
        wid.get_value()
        self.advance_callback(True)  # not quite right, might still exist invalid values
        return True
      except param_widgets.EntryValueError:
        warning_dialog(parentwindow, _("Invalid input for '%s'") % wid.desc)
        self.advance_callback(False)  # to inhibit advance in GUI flow
        return False
    
    def focus_out_validate_entry(wid, id):
      '''
      Callback when focus leaves parameter editing widget.
      We don't rip the focus back if invalid.
      '''
      _validate_entry(wid)
    
    def changed_validate_entry(wid):
      ''' Callback on a change to value (keystroke, cut, etc.) '''
      _validate_entry(wid)
       
       
    '''
    def toggle_callback(toggle):
      # !!! Against Gnome GUI Guidelines to flip the label
      pass
    '''
    
    if is_use_toggles:
        columncount = 3
    else :
        columncount = 2
    
    # a GtkTable widget for each parameter, with several columns
    self.table_wid = gtk.Table(len(paramdefs), columncount, False)
    self.table_wid.set_row_spacings(6)
    self.table_wid.set_col_spacings(6)
    # Pack the table widget into parent box
    packable_box.pack_start(self.table_wid, expand=False)
    self.table_wid.show()

    self.edit_wids = []
    self.toggle_wids = []
    for i in range(len(paramdefs)):
        pf_type = paramdefs[i][0]
        name = paramdefs[i][1]
        desc = paramdefs[i][2]
        # lkk Truncate the desc since it is not wrapping
        if len(desc) > 60 :
          desc = desc[0:60]
        def_val = defaults[i]
        
        label = gtk.Label(desc)
        label.set_use_underline(True)
        label.set_alignment(0.0, 0.5)
        self.table_wid.attach(label, 1, 2, i, i+1, xoptions=gtk.FILL)
        label.show()
        
        # certain types have additional field in paramdef, a range
        if pf_type in (PF_SPINNER, PF_SLIDER, PF_RADIO, PF_OPTION):
            wid = param_widgets._edit_mapping[pf_type](def_val, paramdefs[i][4])
        else:
            wid = param_widgets._edit_mapping[pf_type](def_val)
            
        # !!! connect after so default handler gets signal first
        # certain types are validated each keystroke
        if pf_type not in (PF_COLOR, PF_LAYER, PF_CHANNEL, PF_FONT , 
            PF_FILE, PF_FILENAME, PF_DIRNAME, PF_BRUSH, PF_PATTERN, PF_GRADIENT, PF_PALETTE):
          wid.connect_after("changed", changed_validate_entry) # validate each keystroke 
        else:
          # these widgets have no changed signal
          wid.connect_after("focus-out-event", focus_out_validate_entry) # validate on focus change
        
        label.set_mnemonic_widget(wid)

        self.table_wid.attach(wid, 2,3, i,i+1, yoptions=0)

        if pf_type != PF_TEXT:
            wid.set_tooltip_text(desc)
        else:
            #Attach tip to TextView, not to ScrolledWindow
            wid.viewset_tooltip_text(desc)
        wid.show()

        wid.desc = desc
        self.edit_wids.append(wid)
        
        if is_use_toggles:
            toggle = gtk.CheckButton(label=toggle_label, use_underline=False)
            self.table_wid.attach(toggle, 3, 4, i, i+1, xoptions=gtk.FILL)
            # toggle.connect("toggled", toggle_callback)
            toggle.show()
            toggle.set_active(not toggle_initial_values[i])   # Initial toggle setting !!! Invert
            self.toggle_wids.append(toggle)
            
    print "Built widgets: ", len(self.edit_wids)
    self.table_wid.show()

  
  def validate(self):
    '''
    Validate what the user entered, massage and return the data.
    Raise exception if any invalid values for their types.
    '''
    params = []
    toggles = []

    i=0
    for wid in self.edit_wids:
        params.append(wid.get_value())
        if self.is_use_toggles:
            toggles.append(self.toggle_wids[i].get_active())
        i += 1
    # Any widget can raise param_widgets.EntryValueError:
    
    '''
    !!! Invert sense of toggles.
    The widgets are labeled "Constants" but the rest of this treats them as "Defers"
    which is inverted, i.e. "Not constant"
    '''
    toggles = map(operator.not_, toggles)
    return params, toggles
   
  '''
  Implement parts of the widget API
  '''
  def destroy(self):
    self.table_wid.destroy()
    
  def set_sensitive(self, truth):
    self.table_wid.set_sensitive(truth)
    

  

def parameter_dialog(
        proc_name, 
        run_func,   # on OK button clicked, call with actual params
        paramdefs,  # tuple, definitions of formal parameters
        defaults,   # tuple of initial values: last used (persistent) or standard values
                    # defaults is a misnomer, but commonly used.
        blurb = None,   # displays blurb of plugin at top of dialog
        is_use_toggles=False,
        is_use_progress=True
        ):
    '''
    Builds dialog to ask user for parameters.
    Runs inside a gtk event loop.
    
    Largely copied from gimpfu.interact() .
    Should be unified.
    
    Changes:
        made it a function with parameters
        added optional toggle button in each control (row of table)
        made the action func a parameter
        changed certain names: dialog => dlg (same widget, different names)
        changed certain names: params => paramdefs (more descriptive, formal parameter defs)
        made the progress bar optional
        Busted out table into separate class, taking tooltips with it.
    '''

    '''
    This is a call to libgimpui, via _gimpui.so (the Python binding), not gimpui.py.
    Uses libgimpui so that the dialog follows the Gimp theme, help policy, progress policy, etc.
    See libgimp/gimpui.c etc.
    '''
    dialog = gimpui.Dialog(proc_name, 'python-fu', None, 0, None, proc_name,
                           (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                            gtk.STOCK_OK, gtk.RESPONSE_OK))

    dialog.set_alternative_button_order((gtk.RESPONSE_OK, gtk.RESPONSE_CANCEL))

    dialog.set_transient()

    vbox = gtk.VBox(False, 12)
    vbox.set_border_width(12)
    dialog.vbox.pack_start(vbox)
    vbox.show()
    
    # part 1: blurb
    if blurb:
        # see gimpfu.py for excised domain i8n code
        box = gimpui.HintBox(blurb)
        vbox.pack_start(box, expand=False)
        box.show()

    # part 2: table of parameters
    
    # added from gimpfu
    def enable_OK(direction):
      dialog.set_response_sensitive(gtk.RESPONSE_OK, direction)
      
    table = GimpParamWidget(vbox, dialog, paramdefs, defaults, is_use_toggles, enable_OK)

    # part 3: progress
    if is_use_progress:
        progress_vbox = gtk.VBox(False, 6)
        vbox.pack_end(progress_vbox, expand=False)
        progress_vbox.show()

        progress = gimpui.ProgressBar()
        progress_vbox.pack_start(progress)
        progress.show()
    
      
    def response(dlg, id):
        if id == gtk.RESPONSE_OK:
            dlg.set_response_sensitive(gtk.RESPONSE_OK, False)
            dlg.set_response_sensitive(gtk.RESPONSE_CANCEL, False)

            try:
              dialog.res = run_func(table.validate())
            except param_widgets.EntryValueError:
              warning_dialog(dlg, _("Invalid input")) # WAS wid.desc here
              # dialog continues with OK and CANCEL insensitive?
            except Exception:
              dlg.set_response_sensitive(gtk.RESPONSE_CANCEL, True)
              error_dialog(dlg, proc_name)
              raise

        dlg.hide()

    dialog.connect("response", response)
    dialog.show()
    return dialog


