#include <iostream>
#include <mpi.h>
#include <algorithm>

struct xorshift64 {
    uint64_t x;
    xorshift64(int seed) : x(seed + 1) {}
    uint64_t operator()() {
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        return x;
    }
};

int main(int argc, char *argv[]) {
    // xorshift64 gen(time(NULL) + rank * 123456789);
    xorshift64 gen(time(NULL));
    auto rand_val = [&gen]() { 
        return (gen() & 0x1FFFFFFFFFFFFF) * (1.0 / 0x1FFFFFFFFFFFFF); 
    };

    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    omp_set_num_threads(N);

    long long total_tests = strtoll(argv[1], NULL, 10);
    long long local_tests = total_tests / size;
    long long remainder = total_tests % size;
    if (rank == 0) local_tests += remainder;
    long long circle_cnt = 0;

    // const long long max_batch = 1e8;
    // long long batch_count = local_tests / max_batch + (local_tests % max_batch != 0);

    // for (long long b = 0; b < batch_count; ++b) {
    //     long long this_batch = std::min(max_batch, local_tests - b * max_batch);
    //     #pragma omp parallel for reduction(+:circle_cnt)
    //     for (long long i = 0; i < this_batch; i++) {
    //         ...
    //     }
    // }

    #pragma omp parallel for reduction(+:circle_cnt)
    for (long long i = 0; i < local_tests; i++) {
        double x = rand_val();
        double y = rand_val();
        circle_cnt += (x*x + y*y <= 1.0f);
    }

    long long global_circle_cnt = 0;
    MPI_Reduce(&circle_cnt, &global_circle_cnt, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        double pi = 4.0 * global_circle_cnt / total_tests;
        std::cout << "Pi = " << pi << std::endl;
    }
    
    MPI_Finalize();
    return 0;
}