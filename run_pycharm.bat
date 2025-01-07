REM @echo off
REM Change the pathes as required here.
SET QGIS_ROOT=c:\Program Files\QGIS 2.18
SET GRASS_ROOT=%QGIS_ROOT%\apps\grass\grass-7.2.1
SET PYTHONHOME=%QGIS_ROOT%\apps\Python27
SET PYCHARM_ROOT=C:\Program Files\JetBrains\PyCharm Community Edition 2018.1.1

REM No need to change anything below!
SET QGISNAME=qgis
SET QGIS=%QGIS_ROOT%\apps\%QGISNAME%
set QGIS_PREFIX_PATH=%QGIS%

call "%QGIS_ROOT%\bin\o4w_env.bat"
call "%GRASS_ROOT%\etc\env.bat"

SET PATH=%PATH%;%QGIS_ROOT%\apps\qgis\bin;%GRASS_ROOT%\lib;
set PYTHONPATH=%QGIS_PREFIX_PATH%\python;%PYTHONHOME%\Lib;%PYTHONHOME%\Lib\site-packages;%PYTHONPATH%
set PATH=%PYTHONHOME%;%PYTHONHOME%\Scripts;%PATH%
set PATH=%PYCHARM_ROOT%\bin;%PATH%
start "PyCharm aware of Quantum GIS" /B "pycharm64.exe" %*
