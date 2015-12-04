@echo off


set P4_PORT=ssl:52.17.163.3:1666


set HOME=%HOMEDRIVE%%HOMEPATH%


set P4CONFIG=.p4config

set 	P4CONFIGPATH=%HOME%\%P4CONFIG%



type NUL > %P4CONFIGPATH%



:: Install P4Python (Maya)


md "%HOME%\maya\scripts"



echo Copying %cd%\P4API\windows\P4.py...

copy "%cd%\P4API\windows\P4.py" "%HOME%\maya\scripts\P4.py"


echo Copying %cd%\P4API\windows\P4API.pyd...

copy "%cd%\P4API\windows\P4API.pyd" "%HOME%\maya\scripts\P4API.pyd"



:: Install Maya plugin

md "%HOME%\maya\plug-ins"


echo Copying %cd%\Plugins\P4Maya.py...

copy "%cd%\Plugins\P4Maya.py" "%HOME%\maya\plug-ins\P4Maya.py"


echo Copying %cd%\Perforce...

xcopy /E /I /Y /Q "%cd%\Perforce" "%HOME%\maya\scripts\Perforce"



:: Install P4Python (Nuke)
::

md "%HOME%/.nuke/"


::echo Copying %cd%\P4API\windows\P4.py...

::copy "%cd%\P4API\windows\P4.py" "%HOME%\.nuke\P4.py"

::echo Copying %cd%\P4API\windows\P4API.pyd...

::copy "%cd%\P4API\windows\P4API.pyd" "%HOME%\.nuke\P4API.pyd"



setx P4CONFIG %P4CONFIGPATH%



::P4CONFIG Setup

echo.P4PORT=%P4_PORT% >> %P4CONFIGPATH%

pause