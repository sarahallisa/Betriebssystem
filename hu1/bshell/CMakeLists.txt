cmake_minimum_required(VERSION 3.10)
project(bshell C)

find_package(BISON)
find_package(FLEX)
find_library(READLINE_LIB readline)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -pedantic")

set(CMAKE_C_FLAGS_NOLIBREADLINE "${CMAKE_C_FLAGS_NOLIBREADLINE} -DNOLIBREADLINE")

include_directories(src)

BISON_TARGET(BSParser src/tokenparser.y ${CMAKE_CURRENT_BINARY_DIR}/tokenparser.c
        DEFINES_FILE ${CMAKE_CURRENT_BINARY_DIR}/tokenparser.h)
FLEX_TARGET(BSScanner src/tokenscanner.l ${CMAKE_CURRENT_BINARY_DIR}/tokenscanner.c)

ADD_FLEX_BISON_DEPENDENCY(BSScanner BSParser)
include_directories(${CMAKE_CURRENT_BINARY_DIR})
add_executable(shell
        src/command.c
        src/helper.c
        src/list.c
        src/execute.c
        src/statuslist.c
        src/shell.c
        src/readlineparsing.c
        src/stringbuffer.c
        ${BISON_BSParser_OUTPUTS}
        ${FLEX_BSScanner_OUTPUTS})

target_link_libraries(shell ${FLEX_LIBRARIES} ${READLINE_LIB})


