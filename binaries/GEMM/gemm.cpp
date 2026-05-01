#include <cblas.h>
#include <stdlib.h>
#include <string>

#ifdef ON_HARDWARE
#include <cstdio>
#include <time.h>

/* converts timespec struct to ns timestamp */
static uint64_t to_ns(struct timespec ts) { return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec; }

// Reason I am using this over something line std::chrono is more so for consistency
uint64_t bench_now_ns(void) {
    #ifndef _WIN32
        struct timespec ts;
    #ifdef CLOCK_MONOTONIC_RAW
        clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    #else
        clock_gettime(CLOCK_MONOTONIC, &ts);
    #endif
        return to_ns(ts);
    #else
        LARGE_INTEGER fq, cn;
        QueryPerformanceFrequency(&fq);
        QueryPerformanceCounter(&cn);
        return (uint64_t)((__int128)cn.QuadPart * 1000000000ull / fq.QuadPart);
    #endif
}

#endif

#define N_THREAD_DEFAULT 1
#define N_DEFAULT 512
#define ITERS_DEFAULT 10



int main(int argc, char**argv) {
    
#ifdef ON_HARDWARE
    uint64_t start_ns = bench_now_ns();
#endif

    size_t n_threads = N_THREAD_DEFAULT;
    size_t N = N_DEFAULT;
    size_t iterations = ITERS_DEFAULT;

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];

        if (arg == "-n" || arg == "--n_threads") {
            if (i + 1 < argc) {
                int threads = std::atoi(argv[++i]);
                if (threads > 0) n_threads = static_cast<size_t>(threads);
            }
        }
        else if (arg == "-l" || arg == "--length") {
            if (i + 1 < argc) {
                int n = std::atoi(argv[++i]);
                if (n > 0 && (n & (n - 1)) == 0)
                    N = static_cast<size_t>(n);
            }
        }
        else if (arg == "-i" || arg == "--iterations") {
            if (i + 1 < argc) {
                int iters = std::atoi(argv[++i]);
                if (iters > 0) iterations = static_cast<size_t>(iters);
            }
        }
    }

    openblas_set_num_threads(n_threads);

    float* A = static_cast<float*>(aligned_alloc(1024, N * N * sizeof(float)));
    float* B = static_cast<float*>(aligned_alloc(1024, N * N * sizeof(float)));
    float* C = static_cast<float*>(aligned_alloc(1024, N * N * sizeof(float)));

    if (!A || !B || !C) return 1;

    for (size_t i = 0; i < iterations ; i++)
        cblas_sgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, N, N, N, 1, A, N, B, N, 0, C, N);

#ifdef ON_HARDWARE
    uint64_t end_ns = bench_now_ns();
    uint64_t delta = end_ns - start_ns;
    printf("Elapsed Time: %0.5f seconds\n", delta * 1e-9);
#endif

}