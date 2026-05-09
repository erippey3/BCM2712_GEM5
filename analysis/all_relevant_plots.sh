#!/bin/bash





python3 plot_combined_stats.py i1_i2_comparison.csv \
    --algorithm GEMM \
    --run hardware \
    --run gem5:i1 \
    --run gem5:i2 \
    --x problem_size \
    --y runtime_sec \
    --where threads=1 \
    --series run \
    --output gemm_runtime_compare_t1.png

python3 plot_combined_stats.py i1_i2_comparison.csv \
    --algorithm FFT \
    --run hardware \
    --run gem5:i1 \
    --run gem5:i2 \
    --x problem_size \
    --y runtime_sec \
    --where threads=1 \
    --series run \
    --output fft_runtime_compare_t1.png


python3 plot_combined_stats.py i1_i2_comparison.csv \
    --algorithm GEMM \
    --run hardware \
    --run gem5:i1 \
    --run gem5:i2 \
    --x problem_size \
    --y runtime_sec \
    --where threads=2 \
    --series run \
    --output gemm_runtime_compare_t2.png

python3 plot_combined_stats.py i1_i2_comparison.csv \
    --algorithm FFT \
    --run hardware \
    --run gem5:i1 \
    --run gem5:i2 \
    --x problem_size \
    --y runtime_sec \
    --where threads=2 \
    --series run \
    --output fft_runtime_compare_t2.png


python3 plot_combined_stats.py i1_i2_comparison.csv \
    --algorithm GEMM \
    --run hardware \
    --run gem5:i1 \
    --run gem5:i2 \
    --x problem_size \
    --y runtime_sec \
    --where threads=3 \
    --series run \
    --output gemm_runtime_compare_t3.png

python3 plot_combined_stats.py i1_i2_comparison.csv \
    --algorithm FFT \
    --run hardware \
    --run gem5:i1 \
    --run gem5:i2 \
    --x problem_size \
    --y runtime_sec \
    --where threads=3 \
    --series run \
    --output fft_runtime_compare_t3.png

python3 plot_combined_stats.py i1_i2_comparison.csv \
    --algorithm GEMM \
    --run hardware \
    --run gem5:i1 \
    --run gem5:i2 \
    --x problem_size \
    --y runtime_sec \
    --where threads=4 \
    --series run \
    --output gemm_runtime_compare_t4.png

python3 plot_combined_stats.py i1_i2_comparison.csv \
    --algorithm FFT \
    --run hardware \
    --run gem5:i1 \
    --run gem5:i2 \
    --x problem_size \
    --y runtime_sec \
    --where threads=4 \
    --series run \
    --output fft_runtime_compare_t4.png