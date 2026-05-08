#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#include <iostream>
#include <omp.h>
#include <suitesparse/GraphBLAS.h>

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
#define DEGREE_DEFAULT 8
#define ITERS_DEFAULT 1
#define SOURCE_DEFAULT 0
#define SEED_DEFAULT 0xC0FFEEULL


static uint64_t parse_seed(const char* str)
{
    errno = 0;

    char* end = nullptr;
    unsigned long long value = std::strtoull(str, &end, 0);


    if (errno != 0 || end == str || *end != '\0') {
        std::cerr << "Invalid seed: " << str << "\n";
        std::exit(1);
    }

    return static_cast<uint64_t>(value);
}


static GrB_Info build_graph(GrB_Matrix *A, GrB_Index N, GrB_Index degree, uint64_t seed_val) {
    GrB_Info info = GrB_Matrix_new(A, GrB_BOOL, N, N);
    if (info != GrB_SUCCESS) return info;

    GrB_Index nedges = N * degree;

    std::vector<GrB_Index> rows(nedges);
    std::vector<GrB_Index> cols(nedges);
    std::vector<bool> vals_vec(nedges, true);

    bool *vals = static_cast<bool*>(std::malloc(nedges * sizeof(bool)));
    if (!vals) return GrB_OUT_OF_MEMORY;

    uint64_t seed = seed_val;
    
    for(GrB_Index i = 0; i < N; i++) {
        for (GrB_Index d = 0; d < degree; d++) {
            GrB_Index e = i * degree + d;
            GrB_Index j = static_cast<GrB_Index>(rand() % N);

            if (j == i) {
                j = (j + 1) % N;
            }

            rows[e] = i;
            cols[e] = j;
            vals[e] = true;
        }
    }

    info = GrB_Matrix_build_BOOL(*A, rows.data(), cols.data(), vals, nedges, GrB_LOR);

    std::free(vals);
    return info;
}

// levels[v] is 1-based BFS level. Unvisited vertices have no stored value.
// q is the current frontier.
static GrB_Info bfs_levels(
    GrB_Vector levels,
    GrB_Vector q,
    GrB_Matrix A,
    GrB_Index source
) {
    GrB_Index N;
    GrB_Info info = GrB_Matrix_nrows(&N, A);
    if (info != GrB_SUCCESS) return info;

    info = GrB_Vector_clear(levels);
    if (info != GrB_SUCCESS) return info;

    info = GrB_Vector_clear(q);
    if (info != GrB_SUCCESS) return info;

    info = GrB_Vector_setElement_BOOL(q, true, source);
    if (info != GrB_SUCCESS) return info;

    GrB_Index nfrontier = 1;
    int32_t level = 0;

    while (nfrontier > 0) {
        level++;

        // levels[q] = level
        info = GrB_Vector_assign_INT32(
            levels,
            q,
            NULL,
            level,
            GrB_ALL,
            N,
            NULL
        );
        if (info != GrB_SUCCESS) return info;

        // q<!levels, replace> = q * A over OR-AND semiring.
        // This computes the next frontier while masking out visited vertices.
        info = GrB_vxm(
            q,
            levels,
            NULL,
            GrB_LOR_LAND_SEMIRING_BOOL,
            q,
            A,
            GrB_DESC_RC
        );
        if (info != GrB_SUCCESS) return info;

        info = GrB_Vector_nvals(&nfrontier, q);
        if (info != GrB_SUCCESS) return info;
    }

    return GrB_SUCCESS;
}



int main(int argc, char**argv) {

#ifdef ON_HARDWARE
    uint64_t start_ns = bench_now_ns();
#endif

    size_t n_threads = N_THREAD_DEFAULT;
    size_t N = N_DEFAULT;
    size_t degree = DEGREE_DEFAULT;
    size_t iterations = ITERS_DEFAULT;
    size_t source = SOURCE_DEFAULT;
    size_t seed = SEED_DEFAULT;

    srand(seed);


    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];

        if (arg == "-n" || arg == "--n_threads") {
            if (i + 1 < argc) {
                int threads = std::atoi(argv[++i]);
                if (threads > 0) n_threads = static_cast<size_t>(threads);
            }
        }
        else if (arg == "-l" || arg == "--vertices") {
            if (i + 1 < argc) {
                int n = std::atoi(argv[++i]);
                if (n > 0) N = static_cast<size_t>(n);
            }
        }
        else if (arg == "-d" || arg == "--degree") {
            if (i + 1 < argc) {
                int d = std::atoi(argv[++i]);
                if (d > 0) degree = static_cast<size_t>(d);
            }
        }
        else if (arg == "-i" || arg == "--iterations") {
            if (i + 1 < argc) {
                int iters = std::atoi(argv[++i]);
                if (iters > 0) iterations = static_cast<size_t>(iters);
            }
        }
        else if (arg == "-s" || arg == "--source") {
            if (i + 1 < argc) {
                int src = std::atoi(argv[++i]);
                if (src >= 0) source = static_cast<size_t>(src);
            }
        }
        else if (arg == "-r" || arg == "--seed") {
            if (i + 1 < argc) {
                seed = parse_seed(argv[++i]);
            }
        }
    }

    srand(static_cast<unsigned int>(seed));
    omp_set_num_threads(static_cast<int>(n_threads));

    GrB_Info info = GrB_init(GrB_BLOCKING);
    if (info != GrB_SUCCESS) return 1;


    GrB_Matrix A = nullptr;
    GrB_Vector levels = nullptr;
    GrB_Vector q = nullptr;

    if (build_graph(&A, N, degree, seed) != GrB_SUCCESS) return 1;
    if (GrB_Vector_new(&levels, GrB_INT32, N) != GrB_SUCCESS) return 1;
    if (GrB_Vector_new(&q, GrB_BOOL, N) != GrB_SUCCESS) return 1;

    

    for (size_t i = 0; i < iterations; i++) {
        if (bfs_levels(levels, q, A, source) != GrB_SUCCESS) return 1;
    }

    


    GrB_finalize();

#ifdef ON_HARDWARE
    uint64_t end_ns = bench_now_ns();
    uint64_t delta = end_ns - start_ns;
    printf("Elapsed Time: %0.5f seconds\n", delta * 1e-9);
#endif

    return 0;
}