@echo off

set HOME="%HOMEDRIVE%%HOMEPATH%"

:: Remove P4Python (Maya)
del "%HOME%\My Documents\maya\scripts\P4.py"
del "%HOME%\My Documents\maya\scripts\P4API.pyd"

:: Remove Maya plugin
del "%HOME%\My Documents\maya\plug-ins\P4Maya.py"
rmdir "%HOME%\My Documents\maya\scripts\Perforce"

:: Remove P4Python (Nuke)
del "%HOME%\.nuke\P4.py"
del "%HOME%\.nuke\P4API.pyd"
