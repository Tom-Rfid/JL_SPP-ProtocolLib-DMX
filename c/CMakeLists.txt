cmake_minimum_required(VERSION 3.15)
project(jlspp_dmx C)

set(CMAKE_C_STANDARD 99)

# Library: frames + fixture helpers (no dependency, no I/O).
add_library(jlspp_dmx STATIC
    src/jlspp_dmx.c
    src/jlspp_tables.c
    src/jlspp_mindi_spider.c
    src/jlspp_chauvet_spot260x.c)
target_include_directories(jlspp_dmx PUBLIC include PRIVATE src)

# Tests against spec/test_vectors.json (tests/test_vectors.h is generated).
enable_testing()
add_executable(test_jlspp_dmx tests/test_jlspp_dmx.c)
target_include_directories(test_jlspp_dmx PRIVATE tests)
target_link_libraries(test_jlspp_dmx PRIVATE jlspp_dmx)
add_test(NAME test_jlspp_dmx COMMAND test_jlspp_dmx)

# Example: blink test on a serial port (Win32 or POSIX).
add_executable(blink examples/blink.c)
target_link_libraries(blink PRIVATE jlspp_dmx)
