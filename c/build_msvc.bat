@echo off
rem Builds the library, the tests and the example with MSVC (no CMake needed), then runs the tests.
rem Run it from a "Developer Command Prompt" or after vcvars64.bat.
setlocal
cd /d "%~dp0"
if not exist build mkdir build
set SOURCES=src\jlspp_dmx.c src\jlspp_tables.c src\jlspp_mindi_spider.c src\jlspp_chauvet_spot260x.c
cl /nologo /W4 /O2 /Iinclude /Isrc /Itests /Fobuild\ /Febuild\test_jlspp_dmx.exe tests\test_jlspp_dmx.c %SOURCES% || exit /b 1
cl /nologo /W4 /O2 /Iinclude /Isrc /Fobuild\ /Febuild\blink.exe examples\blink.c %SOURCES% || exit /b 1
build\test_jlspp_dmx.exe
