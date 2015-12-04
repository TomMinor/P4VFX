@echo off



set HOME=%HOMEDRIVE%%HOMEPATH%


echo %HOME%maya\scripts


:: Remove P4Python (Maya)

del %HOME%maya\scripts\P4.py
del %HOME%maya\scripts\P4API.pyd


:: Remove Maya plugin


del %HOME%maya\plug-ins\P4Maya.py
rmdir /s /q %HOME%maya\scripts\Perforce


:: Remove P4Python (Nuke)

del %HOME%.nuke\P4.py
del %HOME%.nuke\P4API.pyd