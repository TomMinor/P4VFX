@echo off

set HOME=%HOMEDRIVE%%HOMEPATH%\Documents

:: Remove P4Python (Maya)

echo Removing %HOME%\maya\scripts\P4.py...
del %HOME%\maya\scripts\P4.py
echo Removing %HOME%\maya\scripts\P4API.pyd
del %HOME%\maya\scripts\P4API.pyd


:: Remove Maya plugin
echo Removing %HOME%\maya\plug-ins\P4Maya.py...
del %HOME%\maya\plug-ins\P4Maya.py
echo Removing %HOME%\maya\scripts\Perforce...
rmdir /s /q %HOME%\maya\scripts\Perforce


:: Remove P4Python (Nuke)

echo Removing %HOME%\.nuke\P4.py...
del %HOME%\.nuke\P4.py
echo Removing %HOME%\.nuke\P4API.pyd...
del %HOME%\.nuke\P4API.pyd

pause