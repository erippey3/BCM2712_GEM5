#!/bin/bash


cd /opt

if [ ! -d "/opt/OpenBLAS" ]; then
    git clone https://github.com/OpenMathLib/OpenBLAS.git
fi

cd /opt/OpenBLAS

make clean

make -j$(nproc) NO_SHARED=1 USE_THREAD=1 NUM_THREADS=$(nproc) DYNAMIC_ARCH=0 NO_AFFINITY=1 CFLAGS="-DGEM5_SE" FCFLAGS="-DGEM5_SE"

make PREFIX=/usr/local/ install