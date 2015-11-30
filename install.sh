#!/bin/bash

# Install P4Python (Maya)
mkdir -p $HOME/maya/scripts
ln -s $(pwd)/P4API/linux/P4.py $HOME/maya/scripts/P4.py
ln -s $(pwd)/P4API/linux/P4API.so $HOME/maya/scripts/P4API.so

# Install P4Python (Nuke)
mkdir -p $HOME/.nuke/scripts
ln -s $(pwd)/P4API/linux/P4.py $HOME/.nuke/P4.py
ln -s $(pwd)/P4API/linux/P4API.so $HOME/.nuke/P4API.so

# Install Maya plugin
mkdir -p $HOME/maya/plug-ins
ln -s $(pwd)/Plugins/P4Maya.py $HOME/maya/plug-ins/P4Maya.py
ln -s $(pwd)/Perforce/ $HOME/maya/scripts/Perforce

# Fix for Nuke SSL error
echo "alias goNuke=\"LD_PRELOAD=/usr/lib64/libstdc++.so.6:/lib64/libgcc_s.so.1 goNuke\"" >> ~/.bashrc
echo "export P4EDITOR=gedit" >> ~/.bashrc