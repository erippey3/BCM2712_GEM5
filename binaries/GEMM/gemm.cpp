#include <cblas.h>
#include <stdlib.h>
#include <string>

#define N_THREAD_DEFAULT 1
#define N_DEFAULT 1024
#define ITERS_DEFAULT 10



int main(int argc, char**argv) {
    
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

}