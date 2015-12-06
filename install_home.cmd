@echo off

set P4_PORT=ssl:52.17.163.3:1666

set HOME=%HOMEDRIVE%%HOMEPATH%

set HOME=
echo Enter your user folder (the one with Documents in it e.g. C:\Users\USER)
set /p HOME=Document Path : 

if exist %HOME% (
	echo Directory %HOME% is valid
) else (
	echo Directory %HOME% doesn't exist
	pause
	goto: eof	
)

set INSTALLPATH=%HOME%\Documents

set P4CONFIG=.p4config
set P4CONFIGPATH=%INSTALLPATH%\%P4CONFIG%

cd /d %~dp0
Set  StartInDirectory= %cd%

set CURRENTDIR=%StartInDirectory%

echo %CURRENTDIR%

type NUL > %P4CONFIGPATH%

:: Install P4Python (Maya)
md "%HOME%\maya\scripts"

set A=%CURRENTDIR%\P4API\windows\P4.py
set B=%INSTALLPATH%\maya\scripts\P4.py
echo Linking %A% to %B% ...
mklink /H %B% %A%

set A=%CURRENTDIR%\P4API\windows\P4API.pyd
set B=%INSTALLPATH%\maya\scripts\P4API.pyd
echo Linking %A% to %B% ...
mklink /H %B% %A%

:: Install Maya plugin
md "%HOME%\maya\plug-ins"

set A=%CURRENTDIR%\Plugins\P4Maya.py
set B=%INSTALLPATH%\maya\plug-ins\P4Maya.py
echo Linking %A% to %B% ...
mklink /H %B% %A%

set A=%CURRENTDIR%\Perforce
set B=%INSTALLPATH%\maya\scripts\Perforce
echo Linking %A% to %B% ...
mklink /J /D %B% %A%

:: Install P4Python (Nuke)
::md "%HOME%/.nuke/"
::mklink /H /d "%HOME%\.nuke\P4.py" "%CURRENTDIR%\P4API\windows\P4.py"
::mklink /H /d "%HOME%\.nuke\P4API.pyd" "%CURRENTDIR%\P4API\windows\P4API.pyd"

setx P4CONFIG %P4CONFIGPATH%

::P4CONFIG Setup
echo.P4PORT=%P4_PORT% >> %P4CONFIGPATH%

pause