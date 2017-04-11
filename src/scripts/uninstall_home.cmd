@echo off

set HOME=%HOMEDRIVE%%HOMEPATH%\Documents

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

:: Remove P4Python (Maya)

set INSTALLPATH=%HOME%\Documents

echo Removing %INSTALLPATH%\maya\scripts\P4.py...
del /F %INSTALLPATH%\maya\scripts\P4.py
echo Removing %INSTALLPATH%\maya\scripts\P4API.pyd
del /F %INSTALLPATH%\maya\scripts\P4API.pyd


:: Remove Maya plugin
echo Removing %INSTALLPATH%\maya\plug-ins\P4Maya.py...
del /F "%INSTALLPATH%\maya\plug-ins\P4Maya.py"
echo Removing %INSTALLPATH%\maya\scripts\Perforce...
rmdir /s /q %INSTALLPATH%\maya\scripts\Perforce


:: Remove P4Python (Nuke)

echo Removing %INSTALLPATH%\.nuke\P4.py...
del %INSTALLPATH%\.nuke\P4.py
echo Removing %INSTALLPATH%\.nuke\P4API.pyd...
del %INSTALLPATH%\.nuke\P4API.pyd

pause