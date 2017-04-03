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

(For convenience, P4Python is bundled within the repo.)

The process is fairly tedious to do by hand, so using the below scripts as a base is recommended. They are based off of the scripts I used when supporting a team of artists with this tool, they make use of symlinks when possible so that the MayaPerforce repo can live in a separate location than the Maya settings directory while still automatically updating it with new changes.

### Linux and Mac

*Note: If on Mac, you will need to download P4Python yourself as it isn't bundled with the repo. Adjust the installation paths accordingly*

```bash

# This assumes that your Maya directory is $HOME/maya, if it is not (such as setting MAYA_APP_DIR)
# then modify as needed.
MAYA_DIR=$HOME/maya

# Point this to your Perforce server
P4_PORT="ssl:12.34.567.8:1666"

_P4CONFIG=".p4config"
# Feel free to move this to another location, such as your workspace root
_P4CONFIGPATH="$HOME/$_P4CONFIG"

# It is highly recommended to set a GUI editor so Maya doesn't hang if Perforce tries to open one
P4EDITOR=geany

# Install P4Python (Maya)
mkdir -p $HOME/maya/scripts
ln -s $PWD/../P4API/linux/P4.py $MAYA_DIR/scripts/P4.py
ln -s $PWD/../P4API/linux/P4API.so $MAYA_DIR/scripts/P4API.so

# Install Maya plugin
mkdir -p $HOME/maya/plug-ins
ln -s $PWD/../Plugins/P4Maya.py $MAYA_DIR/plug-ins/P4Maya.py
ln -s $PWD/../Perforce/ $MAYA_DIR/scripts/Perforce

# Perforce for Maya relies on these variables being set in some form or another
# Setup config (Bash)
echo "export P4CONFIG=$_P4CONFIGPATH" >> ~/.profile

# Setup Perforce
echo "P4PORT=$P4_PORT" >> $_P4CONFIGPATH
echo "P4EDITOR=$P4EDITOR" >> $_P4CONFIGPATH
```

### Windows

*Note: the mklink behaviour isn't necessary and may cause issues if your MayaPerforce repo isn't on the same drive as Maya's settings. It is trivial to replace with an xcopy however*

```Batch
@echo off

set HOME="%HOMEDRIVE%%HOMEPATH%"
:: This assumes that your Maya directory is $HOME/maya, if it is not (such as setting MAYA_APP_DIR)
:: then modify as needed.
set MAYA_DIR=%HOME%\My Documents\maya

:: Point this to your Perforce server
set P4_PORT=ssl:12.34.567.8:1666

set P4CONFIG=.p4config
:: Feel free to move this to another location, such as your workspace root
set P4CONFIGPATH="%HOME%\%P4CONFIG%"

:: Create p4config file if it doesn't exist
type NUL > %P4CONFIGPATH%

:: Install P4Python (Maya)
md "%MAYA_DIR%\scripts"
mklink /H "%MAYA_DIR%\scripts\P4.py" "%cd%\..\P4API\windows\P4.py"
mklink /H "%MAYA_DIR%\scripts\P4API.pyd" "%cd%\..\P4API\windows\P4API.pyd"

:: Install Maya plugin
md "%MAYA_DIR%\plug-ins"
mklink /H "%MAYA_DIR%\plug-ins\P4Maya.py" "%cd%\..\Plugins\P4Maya.py" 
mklink /J /D "%MAYA_DIR%\scripts\Perforce" "%cd%\..\Perforce"

:: P4CONFIG Setup
:: Set an environment variable to .p4config can be found
setx P4CONFIG %P4CONFIGPATH%
echo P4PORT=%P4_PORT% >> %P4CONFIGPATH%
```


## Future Improvements

* Add support for more than Maya, the core functionality is mostly program agnostic and should work with any program that supports PySide and P4Python with minimal effort.
