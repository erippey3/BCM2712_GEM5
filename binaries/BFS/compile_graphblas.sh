

cd /opt/GraphBLAS

rm -rf build
mkdir build
cd build

cmake .. -DCMAKE_BUILD_TYPE=Release \
    -DGRAPHBLAS_COMPACT=ON -DGRAPHBLAS_USE_JIT=ON \
    -DGRAPHBLAS_USE_OPENMP=ON -DBUILD_SHARED_LIBS=OFF \
    -DBUILD_STATIC_LIBS=ON -DGRAPHBLAS_COMPACT=ON

make -j4
sudo make install