@echo off

set P4_PORT=ssl:52.17.163.3:1666

set HOME=%HOMEDRIVE%%HOMEPATH%

set P4CONFIG=.p4config
set P4CONFIGPATH=%HOME%\%P4CONFIG%

cd /d %~dp0
Set  StartInDirectory= %cd%

set CURRENTDIR=%StartInDirectory%

type NUL > %P4CONFIGPATH%

:: Install P4Python (Maya)
md "%HOME%\My Documents\maya\scripts"

set A=%CURRENTDIR%\P4API\windows\P4.py
set B=%HOME%\My Documents\maya\scripts\P4.py
echo Linking %A% to %B% ...
mklink /J /d "%B%" "%A%" 

set A=%CURRENTDIR%\P4API\windows\P4API.pyd
set B=%HOME%\My Documents\maya\scripts\P4API.pyd
echo Linking %A% to %B% ...
mklink /J /d "%B%" "%A%" 

:: Install Maya plugin
md "%HOME%\My Documents\maya\plug-ins"

set A=%CURRENTDIR%\Plugins\P4Maya.py
set B=%HOME%\My Documents\maya\plug-ins\P4Maya.py
echo Linking %A% to %B% ...
mklink /J /d "%B%" "%A%" 

set A=%CURRENTDIR%\Perforce
set B=%HOME%\My Documents\maya\scripts\Perforce
echo Linking %A% to %B% ...
mklink /J /d "%B%" "%A%" 

:: Install P4Python (Nuke)
::md "%HOME%/.nuke/"
::mklink /J /d "%HOME%\.nuke\P4.py" "%CURRENTDIR%\P4API\windows\P4.py"
::mklink /J /d "%HOME%\.nuke\P4API.pyd" "%CURRENTDIR%\P4API\windows\P4API.pyd"

setx P4CONFIG %P4CONFIGPATH%

::P4CONFIG Setup
echo.P4PORT=%P4_PORT% >> %P4CONFIGPATH%

pause