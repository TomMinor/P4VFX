#!/bin/bash

_P4CONFIG=".p4config"
_P4CONFIGPATH="$HOME/$_P4CONFIG"
_P4CONFIGPATH_RC="\$HOME/$_P4CONFIG"
touch _P4CONFIGPATH

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


# Try and setup fish if it's installed
if type fish >/dev/null 2>&1; then
	_FISHCONFIG="$HOME/.config/fish/config.fish"

	# Setup config (Fish)
	echo "Configuring for fish shell"
	
	echo "set -gx P4CONFIG $_P4CONFIGPATH_RC" >> $_FISHCONFIG	
	echo "alias goNuke \"LD_PRELOAD=/usr/lib64/libstdc++.so.6:/lib64/libgcc_s.so.1 goNuke\"" >> $_FISHCONFIG
fi

# Setup config (Bash)
echo "Configuring for bash"

echo "export P4CONFIG=$_P4CONFIGPATH" >> ~/.bashrc
# Fix for Nuke SSL error
echo "alias goNuke=\"LD_PRELOAD=/usr/lib64/libstdc++.so.6:/lib64/libgcc_s.so.1 goNuke\"" >> ~/.bashrc

#P4CONFIG Setup
echo "P4EDITOR geany" >> $_P4CONFIGPATH





