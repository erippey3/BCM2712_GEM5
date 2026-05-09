# BCM2712 GEM5
This repository aims to simulate the BCM2712 SoC. In particular, the CPU, and surrounding memory hierarchy. The goal is to be able to achieve comparable performance results to a physical BCM2712 found in Raspberry Pi 5 and Raspberry Pi Compute Module 5 devices.

## Requirements 
In order to run any of this code, you will need a built version of gem5 that 
contains ARM.

In order to run the code, there are two important directories 

- architectures: locations of gem5 files.
- binaries: location of binaries loaded by the gem5 program

## Architectures
Architectures is split into two directories. iteration1 is the baseline ArmO3CPU 
implementation that does has few fine tuned parameters. In order to run iteration1, 
run 
```bash
/path/to/ARM/gem5.opt architectures/iteration1/Basic_O3_ARM.py /path/to/arm/binary
```

iteration2 is the CPU implementation that has fine tuned parameters for the 
Arm Cortex-A76. To run iteration2, run 
```bash
/path/to/ARM/gem5.opt architectures/iteration2/run_system_emulation.py /path/to/arm/binary
```

## Binaries
Within binaries, there are three directories, one for each algorithm. Within BFS, 
FFT, and GEMM, there are c++ files bfs.cpp, fft.cpp, and gemm.cpp respectively. 
This is the source code for each. Additionally there are makefiles to make each 
of the source codes, however, in order to successfully compile bfs, fft, and gemm, 
you will need the header files for GraphBLAS, FFTW3, and OpenBLAS respectively. 
Instead, there is a precompiled version of each binary as defined using 
```
make arm
```
This would compile each binary using the respective static library present in the 
folder. 

For each binary, there are flags that can be passed into the program to change 
problem size, thread count etc
### BFS
For bfs, -n sets the number of threads, -l sets the number of vertices, -d changes 
the average degree of each vertex, -i changes the number of iterations bfs is run for, 
-s changes the source node, and -r changes the seed used to generate the graph.

### FFT
For fft, -n sets the number of threads, -f sets the fft size, which must be a power of two, 
and -i sets the number of iterations the forward FFT is run.

### GEMM
For gemm, -n sets the number of threads, -l sets the number of rows and columns in the square matrix, 
and -i sets the number of iterations the gemm kernel is run. 

## Putting it all together 
Say you want to run GEMM on a 512 x 512 matrix 15 times with 2 threads using 
the fine tuned Arm CPU. You would run 
```bash 
/path/to/ARM/gem5.opt architectures/iteration2/run_system_emulation.py binaries/GEMM/gemm-arm -n 2 -l 512 -i 15
```