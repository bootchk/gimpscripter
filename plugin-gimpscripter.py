#!/usr/bin/env python

'''
A GIMP plugin.

Generates another plugin (in Python language). 
Generated plugin is sequence of commands.
A command is a call to:
- a target plugin
- or a PDB procedure
- or a macro builtin to this app.

Generated wrapper plugin can be:
  
- a shortcut (simple renaming and simplification of parameters to one command)
- a sequence (the combined function of a sequence.)

The purpose of wrapping is: 
1) alias or link to target command
2) simplify settings dialog (standard, current, or preset options for the target commands.)
3) automate a sequence
4) hide certain complexities of PDB programming, i.e. change the model slightly
(e.g. always add a new object to the image, unlike in the PDB.)


Help text is in /doc and the .glade file.

Future:
Note that the parameters you choose not to defer for the wrapper DO NOT become the last values
for the target plugin (it is run non-interactive.)
You can't change the not deferred parameters later without editing the wrapper.
The parameters you choose to defer DO become the last values for the wrapper plugin
(they will appear as the initial values the next time you run the wrapper.)

Versions:

beta 0.1 : simple shortcut to one plugin using last values
beta 0.2 2010 : presets: let user enter parameters for target plugin.
beta 0.3 April 2011 : renamed Gimpscripter.  Sequences.  Macros.  Calls to PDB procedures.


To Do:

More functionality:
  defaults for parameters taken from plugins themselves or modify PDB to support
    
User friendliness:
  gui non-modal: Apply/Quit
  let user root wrappers elsewhere in menu tree
  domain i8n
  check if menu item already used?
  Since the menu item is not the same as the filename?
  check if the filename already used
  tell the user we created it but GIMP restart required
  and don't show that message more than once.
  Disallow making wrapper to wrapper?
  Disallow making wrapper to Load/Save?
  Return key in name text entry Apply

Copyright 2010 Lloyd Konneker

License:
  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.
'''


from gimpfu import * 

gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def plugin_main():
    from gimpscripter.gui import main_gui
    
    # Build data that drives the app: dictionary of views on dbs
    # For each kind of db, import the glue module to the db
    # and get the dictofviews from the glue module.
    
    # Here, there is only one view, a treeview on GIMP plugins.
    from gimpscripter.mockmenu import plugindb # glue to the Gimp PDB
    dictofviews = plugindb.dictofviews.copy()
    
    app = main_gui.gimpscripterApp(dictofviews)  # create instance of gtkBuilder app
    app.main()  # event loop for app



if __name__ == "__main__":
    # if invoked from Gimp app as a plugin

    register(
        "python_fu_gimpscripter",
        "Point-and-click create a plugin.",
        "This plugin creates another menu item, a wrapper plugin that calls a sequence of PDB procedures or plugins.  The settings of the created plugin may simplify the settings of the sequence.",
        "Lloyd Konneker",
        "Copyright 2010 Lloyd Konneker",
        "2010",
        N_("Gimpscripter..."),  # menu item
        "", # image types: blank means don't care but no image param
        [], # No parameters
        [], # No return value
        plugin_main,
        menu=N_("<Image>/Filters"), # menupath
        domain=("gimp20-python", gimp.locale_directory))
    
    print "Starting Gimpscripter"
    main()




