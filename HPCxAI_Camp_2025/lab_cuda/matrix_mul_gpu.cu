#include <iostream>
#include <cuda_runtime.h>
#include <chrono>
#include <fstream>

//TODO: CUDA kernel for matrix multiplication
__global__ void matrixMulKernel(float* A, float* B_T, float* C, int N) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    float temp = 0.0f;
    if (row < N && col < N) {
        for (int k = 0; k < N; ++k) {
            // B: Strided Access
            temp += A[row * N + k] * B_T[col * N + k];
        }
        C[row * N + col] = temp;
    }
}

void matrixMultiplyGPU(float* h_A, float* h_B, float* h_C, int N) {
    // The matrix size
    size_t size = N * N * sizeof(float);
    float *d_A, *d_B, *d_C;

    //TODO: Allocate device(GPU) memory
    cudaMalloc((void**)&d_A, size);
    cudaMalloc((void**)&d_B, size);
    cudaMalloc((void**)&d_C, size);

    // B transpose
    float* h_B_T = (float*)malloc(size);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            h_B_T[j * N + i] = h_B[i * N + j]; // B_T[j][i] = B[i][j]
        }
    }
    
    //TODO: Copy matrices from host(CPU) to device(GPU)
    cudaMemcpy(d_A, h_A, size, cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, h_B_T, size, cudaMemcpyHostToDevice);


    //TODO: Define block and grid dimensions
    dim3 threadsPerBlock(16, 16); // Example block size
    dim3 numBlocks((N + threadsPerBlock.x - 1) / threadsPerBlock.x,
                   (N + threadsPerBlock.y - 1) / threadsPerBlock.y);

    //TODO: Launch the matrix multiplication kernel
    matrixMulKernel<<<numBlocks, threadsPerBlock>>>(d_A, d_B, d_C, N);

    //TODO: Copy result from device to host
    cudaMemcpy(h_C, d_C, size, cudaMemcpyDeviceToHost);
    

    //TODO: Free device memory
    cudaFree(d_A);
    cudaFree(d_B);
    cudaFree(d_C);
    free(h_B_T);
}

int main() {
    int N = 2000; // Example size of the matrix
    size_t size = N * N * sizeof(float);

    // Allocate host memory
    float* h_A = (float*)malloc(size);
    float* h_B = (float*)malloc(size);
    float* h_C = (float*)malloc(size);

    // Initialize matrices with some values
    for (int i = 0; i < N * N; ++i) {
        h_A[i] = static_cast<float>(i);
        h_B[i] = static_cast<float>(i);
    }

    // Perform matrix multiplication
    auto start = std::chrono::high_resolution_clock::now();
    matrixMultiplyGPU(h_A, h_B, h_C, N);
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<float, std::milli> duration = end - start;

    // Write the last row of the result matrix to a file
    std::ofstream outputFile("gpu_output.txt");
    if (outputFile.is_open()) {
        outputFile << h_C[0] << " ";
        outputFile << "\n";
        outputFile.close();
    } else {
        std::cerr << "Unable to open file for writing\n";
    }

    std::cout << "finish" << std::endl;
    std::cout << "GPU Matrix multiplication took " << duration.count() << " ms\n";

    // Free host memory
    free(h_A);
    free(h_B);
    free(h_C);

    return 0;
}


// nvc++ matrix_mul_gpu.cu -o matrix_mul_gpu