cmake_minimum_required(VERSION 3.5)
project(vmm C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_BUILD_TYPE Debug)
add_compile_options(-Wall -Wextra)

add_executable(vmm src/vmm.c src/vmm.h src/main.c src/output_utility.h src/output_utility.c)

