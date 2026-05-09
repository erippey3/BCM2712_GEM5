#!/usr/bin/env bash
set -u

MAX_CONCURRENCY=8
ITERATION="${1:-i1}"

GEM5="/opt/gem5/build/ALL_w_l3l4/gem5.opt"
ITERS=10

case "$ITERATION" in
    i1)
        GEM5_SCRIPT="architectures/iteration1/Basic_O3_ARM.py"
        ITERATION_NAME="i1"
        ;;
    i2)
        GEM5_SCRIPT="architectures/iteration2/run_system_emulation.py"
        ITERATION_NAME="i2"
        ;;
    *)
        echo "Unknown iteration: $ITERATION"
        echo "Usage: $0 [i1|i2]"
        exit 1
        ;;
esac

FAIL_LOG="gem5_failed_runs_${ITERATION}.log"
: > "$FAIL_LOG"

run_test() {
    local suite="$1"        # FFT or GEMM
    local binary="$2"       # binaries/FFT/fft-arm
    local size_flag="$3"    # -f or -l
    local size="$4"
    local threads="$5"

    local outdir="binaries/${suite}/stats/gem5/${ITERATION_NAME}/${size}/t${threads}"

    mkdir -p "$outdir"

    echo "[START] $suite size=$size threads=$threads out=$outdir"

    "$GEM5" \
        -d "$outdir" \
        "$GEM5_SCRIPT" \
        "$binary" \
        -n "$threads" \
        "$size_flag" "$size" \
        -i "$ITERS" &> "$outdir/stdout_dump.txt"

    local status=$?

    if [[ $status -ne 0 ]]; then
        echo "[FAIL] $suite size=$size threads=$threads status=$status" | tee -a "$FAIL_LOG"
        return "$status"
    fi

    echo "[DONE]  $suite size=$size threads=$threads"
}

wait_for_slot() {
    while [[ "$(jobs -rp | wc -l)" -ge "$MAX_CONCURRENCY" ]]; do
        wait -n
    done
}

# FFT tests
for threads in 1 2 3 4; do
    for fft_size in 128 256 512 1024 2048 4096 8192; do
        wait_for_slot
        run_test "FFT" "binaries/FFT/fft-arm" "-f" "$fft_size" "$threads" &
    done
done

# GEMM tests
for threads in 1 2 3 4; do
    for n in 64 128 256 512 1024; do
        wait_for_slot
        run_test "GEMM" "binaries/GEMM/gemm-arm" "-l" "$n" "$threads" &
    done
done

for threads in 1; do
    for n in 512 1024 2048 4096 8192 16384; do 
        wait_for_slot
        run_test "BFS" "binaries/BFS/bfs-arm" "-l" "$n" "$threads" &
    done
done

wait

echo "All queued runs completed."
echo "Failed runs, if any, are listed in: $FAIL_LOG"