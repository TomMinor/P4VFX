# Perforce for Maya

**Work in progress**

A minimal Maya Python plugin using the [P4Python API](https://www.perforce.com/downloads/helix#product-54), this toolset is intended to make working with Perforce from within Maya simple for artists. 

![Alt text](images/image01.png?raw=true "Perforce for Maya Changelist Interface")

It supports a subset of Perforce functionality that is typically needed when creating content, but doesn't currently support more advanced features such as branching:
* Depot/Client browser to clearly show what files are to be added, edited or removed (can also view deleted files for restore).
* Visual progress bar feedback on changelist submission and sync, ideal for when large assets are shared amongst the team.
* Submit changes, choose exactly which files you want to submit and add a description.
* Find an older scene revision in the depot browser, temporarily save it to disk and preview it in Maya with one button.
* Revert to older versions of assets without deleting history at the click of a button

As this was developed for an actual project, various pipeline functions were added to support a complex pipeline structure:
* On scene save and reference operations, ensure all filepaths are relative to an environment variable pointing to the root of the project. This ensures that relative paths to references and assets work on every artist's machine.
* Automatically strip out the student flag from saved Maya scenes (handy!)
* Asset and shot creation wizards to simplify the process of ensuring everything follows a consistent structure

## Install

The installation process is now automated by **install.py**, it will support all out of the box plugins (Maya, Nuke, etc) as they are added. It handles symlinking the module files to the places necessary for each app, and creating/updating P4CONFIG if necessary.

To use it, simply call it like so:
```python install.py --p4port ssl:12.34.567.8:1666```

(For convenience, P4Python is bundled within the repo.)

**Note: The Mac P4Python library isn't bundled within the repo yet, but it is just a case of placing it in appropriate PATH so the application can find it.**
