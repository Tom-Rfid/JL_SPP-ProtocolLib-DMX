@echo off
rem Compile la librairie, les tests et l'exemple avec MSVC (sans CMake), puis lance les tests.
rem A lancer depuis une "Developer Command Prompt" ou apres vcvars64.bat.
setlocal
cd /d "%~dp0"
if not exist build mkdir build
cl /nologo /W4 /O2 /Iinclude /Itests /Fobuild\ /Febuild\test_jlspp_dmx.exe tests\test_jlspp_dmx.c src\jlspp_dmx.c src\jlspp_tables.c || exit /b 1
cl /nologo /W4 /O2 /Iinclude /Fobuild\ /Febuild\blink.exe examples\blink.c src\jlspp_dmx.c src\jlspp_tables.c || exit /b 1
build\test_jlspp_dmx.exe
