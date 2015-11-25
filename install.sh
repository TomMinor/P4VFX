#!/bin/bash

ln -s $(pwd)/images $HOME/maya/scripts/

ln $(pwd)/maya/P4API.so $HOME/maya/scripts/P4API.so
ln $(pwd)/maya/P4.py $HOME/maya/scripts/P4.py

ln $(pwd)/PerforceGUI.py $HOME/maya/scripts/PerforceGUI.py

touch $HOME/maya/scripts/userSetup.py

echo "export P4USER=kbishop" >> ~/.bash_profile
echo "export P4PASSWD=contact_dev" >> ~/.bash_profile
echo "export P4PORT=ssl:52.17.163.3:1666" >> ~/.bash_profile

source ~/.bash_profile

echo "import PerforceGUI" >> $HOME/maya/scripts/userSetup.py
