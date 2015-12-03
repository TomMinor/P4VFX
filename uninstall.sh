#!/bin/bash

_P4CONFIG=".p4config"
_P4CONFIGPATH="$HOME/$_P4CONFIG"
_P4CONFIGPATH_RC="\$HOME/$_P4CONFIG"

# Remove P4Python (Maya)
rm -f $HOME/maya/scripts/P4.py
rm -f $HOME/maya/scripts/P4API.so

# Remove P4Python (Nuke)
rm -f $HOME/.nuke/P4.py
rm -f $HOME/.nuke/P4API.so

# Remove Maya plugin
rm -f $HOME/maya/plug-ins/P4Maya.py
rm -rf $HOME/maya/scripts/Perforce



