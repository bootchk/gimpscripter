'''
Map a menu item to a command.

This helps populate a tree model in the GUI.
Plugins are put into the tree model separately.
Many commands here are PDB procedures.
Some are macros (see macro.py.)

Note that some PDB procedures map to Gimp menu items
but this is NOT a documentation of that map,
which involves a menubar and various pop-up context menus.

We also change the semantics of some PDB procedure name WORDS:
"New" here means new AND added to the image, whereas in some PDB procedures
"New" means new and NOT attached to an image.

This is hand-coded and might not be complete.

Annotation:

- "mismatch" there is a significant difference between the name and the menu path
- "fabricated" there is no menu path in Gimp app itself
- "diff" we changed the menu path from Gimp app itself to GimpScripter mock menus
- "dupe" the command appears in more than one place in our mock menu
- "already included" the command is a plugin and already included in the tree model
'''


menu_to_procname = { \
"Layer/Transform/Offset" : "gimp-drawable-offset",
#
"Edit/Clear" : "gimp-edit-clear",
"Edit/Copy" : "gimp-edit-copy",
"Edit/Copy Visible" : "gimp-edit-copy-visible",
"Edit/Cut" : "gimp-edit-cut",
"Edit/Paste" : "gimp-edit-paste",
"Edit/Paste as/New Image" : "gimp-edit-paste-as-new",  #mismatch,
# TODO "Edit/Paste as/New Layer" : "macro-paste-as-new-layer",   # missing
# Edit/Paste as/ are named to match the similar plugins below
# "Edit/Paste as New/Brush" : "script-fu-paste-as-brush",  # already included
# "Edit/Paste as New/Pattern" : "script-fu-paste-as-pattern",  # already included
"Edit/Fill" : "gimp-edit-fill",
"Edit/Buffer/Copy Named" : "gimp-edit-named-copy",
"Edit/Buffer/Copy Visible Named" : "gimp-edit-named-copy-visible",
"Edit/Buffer/Cut Named" : "gimp-edit-named-cut",
"Edit/Buffer/Paste Named" : "gimp-edit-named-paste",
"Edit/Stroke/Path" : "gimp-edit-stroke-vectors",
#
# TODO the next one is bogus: same as Edit/Paste as/New Image
"File/Create/Acquire/From Clipboard" : "gimp-edit-paste-as-new",
# Because File/Save is already a path, can't name this just File/Save,
# must add 'By Extension'
"File/Save/By extension" : "gimp-file-save",
#
"Image/Mode/Grayscale" : "gimp-image-convert-grayscale",
"Image/Mode/Indexed" : "gimp-image-convert-indexed",
"Image/Mode/RGB" : "gimp-image-convert-rgb",
"Image/Crop/Crop to Selection" : "gimp-image-crop",
"Image/New/Blank" : "gimp-image-new",  # diff File/New
"Image/New/Duplicate" : "gimp-image-duplicate",
"Image/Display" : "gimp-display-new", # fabricated
"Image/Delete" : "gimp-image-delete", # fabricated, requires OS file delete?
"Image/Flatten" : "gimp-image-flatten",
"Image/Resize/Canvas Size" : "gimp-image-resize",
"Image/Resize/Fit Canvas to Layers" : "gimp-image-resize-to-layers",
"Image/Scale" : "gimp-image-scale", # diff Image/Scale Image
"Image/Transform/Flip" : "gimp-image-flip", # mismatch
"Image/Transform/Rotate" : "gimp-image-rotate", # mismatch
"Image/Add Layer" : "gimp-image-add-layer", # fabricated
# Add Layer is not much use if we always add new layers to image
# Image/Transform/Guillotine is a plugin
#
"Colors/Threshold" : "gimp-threshold",
"Colors/Threshold Alpha" : "plug-in-threshold-alpha", # diff
"Colors/Levels" : "gimp-levels",
"Colors/Levels Stretch" : "gimp-levels-stretch",
#
# For now, if a menupath is a prefix of another, it isn't clickable as a command
# So we add "Blank" here
"Layer/New/Blank" : "gimp-layer-new",   # diff
"Layer/New/Blank Attached" : "macro-layer-new-blank-attached",
"Layer/New/From Visible" : "macro-layer-new-visible", # diff
# Omit since it doesn't add the layer to the image: "gimp-layer-new-from-visible"
# !!! gimp-FOO-delete is only useful for a FOO NOT added to an image
# gimp-layer-delete deprecated for gimp-item-delete
"Layer/Delete" : "gimp-image-remove-layer", # mismatch  also, is Layer/Structure/Delete Layer
"Layer/Resize/To Boundary Size" : "gimp-layer-resize",  # diff
"Layer/Resize/To Image Size" : "gimp-layer-resize-to-image-size",  # diff
"Layer/Scale" : "gimp-layer-scale", # mismatch
"Layer/Set Mode" : "gimp-layer-set-mode",
"Layer/Translate" : "gimp-layer-translate",
"Layer/Alpha/Add" : "gimp-layer-add-alpha",
"Layer/Alpha/Remove" : "gimp-layer-flatten",  # mismatch
"Layer/Copy" : "macro-layer-copy", # WAS "gimp-layer-copy",
"Layer/Copy active layer" : "gimp-layer-new-from-drawable",  # mismatch

"Layer/Active/Set" : "gimp-image-set-active-layer", # fabricated
"Layer/Active/Get" : "gimp-image-get-active-layer", # fabricated
"Layer/Anchor" : "gimp-floating-sel-anchor",  # mismatch
#
"Select/All" : "gimp-selection-all",
"Select/Float" : "gimp-selection-float",
"Select/Invert" : "gimp-selection-invert",
"Select/None" : "gimp-selection-none",
"Select/By Color" : "gimp-by-color-select", # mismatch
"Select/Modify/Border" : "gimp-selection-border",
"Select/Modify/Feather" : "gimp-selection-feather",
"Select/Modify/Grow" : "gimp-selection-grow",
"Select/Modify/Sharpen" : "gimp-selection-sharpen",
"Select/Modify/Shrink" : "gimp-selection-shrink",
"Select/Save to Channel" : "gimp-selection-save",
"Select/From path" : "gimp-vectors-to-selection",
"Select/To path" : "plug-in-sel2path",
"Select/Add/Channel" : "gimp-selection-load", #dupe
# Select/To path is a plugin, not internal procedure but the plugin query doesn't get it ???
#
"Drawable/Transform/Flip" : "gimp-drawable-transform-flip-simple",   # mismatch
"Drawable/Transform/Rotate" : "gimp-drawable-transform-rotate-simple",   # mismatch
"Drawable/Fill" : "gimp-drawable-fill","Select/Float" : "gimp-selection-float",

# These have no presence in Gimp menus so we fabricate a menu item
"Context/Pop" : "gimp-context-pop", # fabricated
"Context/Push" : "gimp-context-push",
"Context/Set/FG" : "gimp-context-set-foreground",
"Context/Set/Brush" : "gimp-context-set-brush", # string parameter
"Context/Set/Choose brush" : "macro-context-choose-brush",  # PF_BRUSH parameter
# "Context/Swap FG & BG colors" : "gimp-context-set-brush",
"Channel/New" : "macro-channel-new", # WAS "gimp-channel-new", # fabricated or a context menu?
# TODO we need a macro here pdb.gimp_image_add_channel(image, pdb.gimp_channel_new(FOO), 1)
"Channel/Delete" : "gimp-image-remove_channel",  # mismatch ?????
"Channel/Copy" : "gimp-channel-copy",
"Channel/Add to Selection" : "gimp-selection-load", # mismatch, dupe
"Channel/Activate" : "gimp-image-set-active-channel", # fabricated
#
# We can't do this one until we exclude its parameter from the parameters page
# or make param_widgets have a widget for a Display
#"Display/Delete" : "gimp-display-delete", # fabricated: created by Image/Display
"Display/New Hidden" : "gimp-display-new",  # mismatch
"Display/Flush" : "gimp-displays-flush", # mismatch, extra s
"Display/New" : "macro-display-new",
#
"Path/Remove Named" : "gimp-path-delete", # mismatch, string param
"Path/Remove Active" : "gimp-image-remove-vectors", # mismatch, hidden PF_VECTORS param
"Path/Copy" : "gimp-vectors-copy",
"Path/Import" : "gimp-vectors-import-from-file",
"Path/Export" : "gimp-vectors-export-to-file",
}

