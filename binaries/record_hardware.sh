#!/bin/bash 

EVENT_GROUPS=(
"cycles,instructions,inst_retired,inst_spec,stall_frontend,stall_backend"
"branches,branch-misses,br_pred,br_mis_pred,br_retired,br_mis_pred_retired"
"l1d_cache,l1d_cache_rd,l1d_cache_wr,l1d_cache_refill,l1i_cache,l1i_cache_refill"
"l2d_cache,l2d_cache_rd,l2d_cache_wr,l2d_cache_refill"
"l1d_tlb,l1d_tlb_refill,l1i_tlb,l1i_tlb_refill,l2d_tlb,l2d_tlb_refill"
"mem_access,mem_access_rd,mem_access_wr,ld_spec,st_spec,ase_spec,vfp_spec"
)

mkdir -p ./FFT/stats/hardware
mkdir -p ./GEMM/stats/hardware

iterations=10

for size in 128 256 512 1024 2048 4096 8192; do
    for t in 1 2 3 4; do
        for i in "${!EVENT_GROUPS[@]}"; do
            mkdir -p ./FFT/stats/hardware/"$size"/"t${t}"
            perf stat -x, -o "FFT/stats/hardware/${size}/t${t}/group${i}.csv" -r 5 \
            -e task-clock,duration_time,user_time,system_time \
            -e "${EVENT_GROUPS[$i]}" \
            -- ./FFT/fft-arm -n "$t" -f "$size" -i "$iterations"
        done
        ./FFT/fft-arm -n "$t" -f "$size" -i "$iterations" > "FFT/stats/hardware/${size}/t${t}/runtime.txt"
    done
done

for size in 64 128 256 512 1024; do
    for t in 1 2 3 4; do
        for i in "${!EVENT_GROUPS[@]}"; do
            mkdir -p ./GEMM/stats/hardware/"$size"/"t${t}"
            perf stat -x, -o "GEMM/stats/hardware/${size}/t${t}/group${i}.csv" -r 5 \
            -e task-clock,duration_time,user_time,system_time \
            -e "${EVENT_GROUPS[$i]}" \
            -- ./GEMM/gemm-arm -n "$t" -l "$size" -i "$iterations"
        done
        ./GEMM/gemm-arm -n "$t" -l "$size" -i "$iterations" > "GEMM/stats/hardware/${size}/t${t}/runtime.txt"
    done
done