setlocal enabledelayedexpansion

:: check REPO_HOME variable
if "%REPO_HOME%" == "" (
	echo "REPO_HOME variable must be set before publishing"
	goto FIN
)
echo %REPO_HOME%

:: call publisher.exe with IDE specific program arguments
set /p ide=<%1
set ide=!ide:REPO_HOME=%REPO_HOME%!
echo %ide%
publisher.exe %ide%

:FIN