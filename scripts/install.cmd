@echo off

set P4_PORT=ssl:52.17.163.3:1666

set HOME="%HOMEDRIVE%%HOMEPATH%"
set P4CONFIG=.p4config
set P4CONFIGPATH="%HOME%\%P4CONFIG%"

type NUL > %P4CONFIGPATH%

:: Install P4Python (Maya)
md "%HOME%\My Documents\maya\scripts"
mklink /H "%HOME%\My Documents\maya\scripts\P4.py" "%cd%\..\P4API\windows\P4.py"
mklink /H "%HOME%\My Documents\maya\scripts\P4API.pyd" "%cd%\..\P4API\windows\P4API.pyd"

:: Install Maya plugin
md "%HOME%\My Documents\maya\plug-ins"
mklink /H "%HOME%\My Documents\maya\plug-ins\P4Maya.py" "%cd%\..\Plugins\P4Maya.py" 
mklink /J /D "%HOME%\My Documents\maya\scripts\Perforce" "%cd%\..\Perforce"

:: Install P4Python (Nuke)
md "%HOME%/.nuke/"
mklink /H "%HOME%\.nuke\P4.py" "%cd%\..\P4API\windows\P4.py"
mklink /H "%HOME%\.nuke\P4API.pyd" "%cd%\..\P4API\windows\P4API.pyd"

setx P4CONFIG %P4CONFIGPATH%

::P4CONFIG Setup
echo.P4PORT=%P4_PORT% >> %P4CONFIGPATH%
