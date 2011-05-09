#! /usr/bin/python

'''

lloyd konneker 2010

Derived from gimpfu.py.
Here I broke out the widgets for entering parameters to Gimp plugins.
They were hidden inside interact().
More are in gimpui.py, see the mapping below.
'''

from gimp import locale_directory

import pygtk
pygtk.require('2.0')

import gimpui
import gtk



import gettext
t = gettext.translation('gimp20-python', locale_directory, fallback=True)
_ = t.ugettext


'''
These copied verbatim from gimpfu.py.
Too laborius to import gimpfu and use eg gimpfu.PF_INT8 .
!!! Keep them the same if gimpfu changes.
'''
from gimpfu import *


# Raised by widgets
class EntryValueError(Exception):
    pass


# widgets for entering params for Gimp plugins

class StringEntry(gtk.Entry):
    def __init__(self, default=''):
        gtk.Entry.__init__(self)
        self.set_text(str(default))

    def get_value(self):
        return self.get_text()

class TextEntry(gtk.ScrolledWindow):
    def __init__ (self, default=''):
        gtk.ScrolledWindow.__init__(self)
        self.set_shadow_type(gtk.SHADOW_IN)

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_size_request(100, -1)

        self.view = gtk.TextView()
        self.add(self.view)
        self.view.show()

        self.buffer = self.view.get_buffer()

        self.set_value(str(default))

    def set_value(self, text):
        self.buffer.set_text(text)

    def get_value(self):
        return self.buffer.get_text(self.buffer.get_start_iter(),
                                    self.buffer.get_end_iter())

class IntEntry(StringEntry):
    def get_value(self):
        try:
            return int(self.get_text())
        except ValueError, e:
            raise EntryValueError, e.args

class FloatEntry(StringEntry):
        def get_value(self):
            try:
                return float(self.get_text())
            except ValueError, e:
                raise EntryValueError, e.args

#    class ArrayEntry(StringEntry):
#            def get_value(self):
#                return eval(self.get_text(), {}, {})


def precision(step):
    # calculate a reasonable precision from a given step size
    if math.fabs(step) >= 1.0 or step == 0.0:
        digits = 0
    else:
        digits = abs(math.floor(math.log10(math.fabs(step))));
    if digits > 20:
        digits = 20
    return int(digits)

class SliderEntry(gtk.HScale):
    # bounds is (upper, lower, step)
    def __init__(self, default=0, bounds=(0, 100, 5)):
        step = bounds[2]
        self.adj = gtk.Adjustment(default, bounds[0], bounds[1],
                                    step, 10 * step, 0)
        gtk.HScale.__init__(self, self.adj)
        self.set_digits(precision(step))

    def get_value(self):
        return self.adj.value

class SpinnerEntry(gtk.SpinButton):
    # bounds is (upper, lower, step)
    def __init__(self, default=0, bounds=(0, 100, 5)):
        step = bounds[2]
        self.adj = gtk.Adjustment(default, bounds[0], bounds[1],
                                    step, 10 * step, 0)
        gtk.SpinButton.__init__(self, self.adj, step, precision(step))

class ToggleEntry(gtk.ToggleButton):
    def __init__(self, default=0):
        gtk.ToggleButton.__init__(self)

        self.label = gtk.Label(_("No"))
        self.add(self.label)
        self.label.show()

        self.connect("toggled", self.changed)

        self.set_active(default)

    def changed(self, tog):
        if tog.get_active():
            self.label.set_text(_("Yes"))
        else:
            self.label.set_text(_("No"))

    def get_value(self):
        return self.get_active()

class RadioEntry(gtk.VBox):
    def __init__(self, default=0, items=((_("Yes"), 1), (_("No"), 0))):
        gtk.VBox.__init__(self, homogeneous=False, spacing=2)

        button = None

        for (label, value) in items:
            button = gtk.RadioButton(button, label)
            self.pack_start(button)
            button.show()

            button.connect("toggled", self.changed, value)

            if value == default:
                button.set_active(True)
                self.active_value = value

    def changed(self, radio, value):
        if radio.get_active():
            self.active_value = value

    def get_value(self):
        return self.active_value

class ComboEntry(gtk.ComboBox):
    def __init__(self, default=0, items=()):
        store = gtk.ListStore(str)
        for item in items:
            store.append([item])

        gtk.ComboBox.__init__(self, model=store)

        cell = gtk.CellRendererText()
        self.pack_start(cell)
        self.set_attributes(cell, text=0)

        self.set_active(default)

    def get_value(self):
        return self.get_active()

def FileSelector(default=''):
    if default and default.endswith('/'):
        selector = DirnameSelector
        if default == '/': default = ''
    else:
        selector = FilenameSelector
    return selector(default)

class FilenameSelector(gtk.FileChooserButton):
    def __init__(self, default='', save_mode=False):
        gtk.FileChooserButton.__init__(self,
                                        _("Python-Fu File Selection"))
        self.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        if default:
            self.set_filename(default)

    def get_value(self):
        return self.get_filename()

class DirnameSelector(gtk.FileChooserButton):
    def __init__(self, default=''):
        gtk.FileChooserButton.__init__(self,
                                        _("Python-Fu Folder Selection"))
        self.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        if default:
            self.set_filename(default)

    def get_value(self):
        return self.get_filename()

# Define a mapping of param types to edit objects ...
# Used to build a table of widgets in the dialog for a plugin
'''
!!! This has been altered for Gimpscripter:
At generate time, for ephemera, we let user enter a string.
We DO NOT let user choose from a list of ephemera existing at generate time.
At runtime, if the parameter is deferred, we DO let user choose...
'''

_edit_mapping = {
        PF_INT8        : IntEntry,
        PF_INT16       : IntEntry,
        PF_INT32       : IntEntry,
        PF_FLOAT       : FloatEntry,
        PF_STRING      : StringEntry,
        #PF_INT8ARRAY   : ArrayEntry,
        #PF_INT16ARRAY  : ArrayEntry,
        #PF_INT32ARRAY  : ArrayEntry,
        #PF_FLOATARRAY  : ArrayEntry,
        #PF_STRINGARRAY : ArrayEntry,
        PF_COLOR       : gimpui.ColorSelector,
        # These are ephemerals, doesn't make sense to show a chooser at generation time
        PF_IMAGE       : StringEntry, # at runtime is: gimpui.ImageSelector,
        PF_LAYER       : StringEntry, # at runtime is: gimpui.LayerSelector,
        PF_CHANNEL     : StringEntry, # at runtime is: gimpui.ChannelSelector,
        PF_DRAWABLE    : StringEntry, # at runtime is: gimpui.DrawableSelector,
        PF_VECTORS     : StringEntry, # at runtime is: gimpui.VectorsSelector,

        PF_TOGGLE      : ToggleEntry,
        PF_SLIDER      : SliderEntry,
        PF_SPINNER     : SpinnerEntry,
        PF_RADIO       : RadioEntry,
        PF_OPTION      : ComboEntry,

        PF_FONT        : gimpui.FontSelector,
        # Next three also ephemeral?
        PF_FILE        : FileSelector,
        PF_FILENAME    : FilenameSelector,
        PF_DIRNAME     : DirnameSelector,
        PF_BRUSH       : gimpui.BrushSelector,
        PF_PATTERN     : gimpui.PatternSelector,
        PF_GRADIENT    : gimpui.GradientSelector,
        PF_PALETTE     : gimpui.PaletteSelector,
        PF_TEXT        : TextEntry
}


