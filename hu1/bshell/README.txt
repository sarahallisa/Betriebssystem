1. Building normal executable

1.1 Build Process:

mkdir build
cd build
cmake ..
make

2. Building without libreadline

mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Nolibreadline ..
make

3. Execution

./shell
