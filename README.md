# P4VFX: A Perforce Toolset for VFX Software

## Description
P4VFX is a toolset that is intended to make working with Perforce from within VFX content creation applications simple and intuitive for artists. It achieves this by stripping out complex features such as branching and only providing the tools an artist actually needs to checkout assets, submit/manage changelists, view local and remote file history and revert work as necessary.

![Alt text](images/image01.png?raw=true "Perforce for Maya Changelist Interface")

Supported functionality:
* Depot/Client browser to clearly show what files are to be added, edited or removed (can also view deleted files for restore).
* Visual progress bar feedback on changelist submission and sync, ideal for when large/numerous assets are shared amongst the team.
* Submit changes, choose exactly which files you want to submit and add a description.
* Find an older scene revision in the depot browser, temporarily save it to disk and preview it in Maya with one button.
* Revert to older versions of assets without deleting history at the click of a button

As this was developed for an actual project, various pipeline functions were added to support a complex pipeline structure:
* On scene save and reference operations, ensure all filepaths are relative to an environment variable pointing to the root of the project. This ensures that relative paths to references and assets work on every artist's machine.
* Automatically strip out the student flag from saved Maya scenes (handy!)
* Asset and shot creation wizards to simplify the process of ensuring everything follows a consistent structure

It uses [QtPy](https://github.com/spyder-ide/qtpy) to allow use in both Qt4/Qt5 applications and the [P4Python API](https://www.perforce.com/downloads/helix#product-54).

## Install

The installation process is now automated by **install.py**, it will support all out of the box plugins (Maya, Nuke, etc) as they are added. It handles symlinking the module files to the places necessary for each app, and creating/updating P4CONFIG if necessary.

To use it, simply call it like so:
```python install.py```

(For convenience, P4Python is bundled within the repo.)

**Note: The Mac P4Python library isn't bundled within the repo yet, but it is just a case of placing it in appropriate PATH so the application can find it.**

## Configuring

When possible the default Perforce functionality is used for determining the environment.

This typically involves setting a P4CONFIG env var to something like '.p4config', Perforce will then search the current directory and it's parents for the existence of this file. This behaviour allows you to determine which workspace is used depending on where the p4config file is placed, typically in the settings folder for your app of 


## License

This project is licensed under the MIT license.
