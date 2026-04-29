#define STB_IMAGE_WRITE_IMPLEMENTATION
#include <string.h>

#include <algorithm>
#include <complex>
#include <iostream>
#include <vector>
#include <omp.h>
#include <mpi.h>
#include <limits>

#include "stb_image_write.h"

#define MaxRepeats 10000
#define CHUNK_SIZE 16

using namespace std;

struct Color {
    unsigned char r, g, b;
};

complex<double> trap(0.5, 0);

void hsv_to_rgb(double h, double s, double v, unsigned char &r,
                                unsigned char &g, unsigned char &b) {
    double c = v * s;
    double x = c * (1 - abs(fmod(h / 60.0, 2) - 1));
    double m = v - c;
    double r1, g1, b1;

    if (h >= 0 && h < 60) {
        r1 = c;
        g1 = x;
        b1 = 0;
    } else if (h >= 60 && h < 120) {
        r1 = x;
        g1 = c;
        b1 = 0;
    } else if (h >= 120 && h < 180) {
        r1 = 0;
        g1 = c;
        b1 = x;
    } else if (h >= 180 && h < 240) {
        r1 = 0;
        g1 = x;
        b1 = c;
    } else if (h >= 240 && h < 300) {
        r1 = x;
        g1 = 0;
        b1 = c;
    } else {
        r1 = c;
        g1 = 0;
        b1 = x;
    }

    r = static_cast<unsigned char>((r1 + m) * 255);
    g = static_cast<unsigned char>((g1 + m) * 255);
    b = static_cast<unsigned char>((b1 + m) * 255);
}

int main(int argc, char *argv[]) {
    // MPI 初始化
    MPI_Init(&argc, &argv);
    int world_rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    int world_size;
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    int HEIGHT, WIDTH;
    unsigned char *image = nullptr;
    string outputfile_name;

    // --- 主程序 (rank 0) 處理輸入/輸出和初始化 ---
    if (world_rank == 0) {
        if (argc < 3) {
            std::cout << "Usage: " << argv[0] << " <inputfile> <outputfile>"
                                << std::endl;
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        char *inputfile_name = argv[1];
        outputfile_name = argv[2];

        if (freopen(inputfile_name, "r", stdin) == nullptr) {
            std::cout << "Error: Unable to open input file: " << inputfile_name
                                << std::endl;
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        scanf("height=%d\n", &HEIGHT);
        scanf("width=%d", &WIDTH);
        cout << "Width: " << WIDTH << " Height: " << HEIGHT << endl;
        
        image = new unsigned char[HEIGHT * WIDTH * 3];
    }

    MPI_Bcast(&HEIGHT, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&WIDTH, 1, MPI_INT, 0, MPI_COMM_WORLD);

    // --- 主從式動態負載平衡 ---
    if (world_rank == 0) { // 主程序 (Master)
        int next_row_to_assign = 0;
        MPI_Status status;
        int active_workers = 0;

        // 初始分發工作給所有可用的 worker
        for (int i = 1; i < world_size; ++i) { // 從 rank 1 開始是 worker
            if (next_row_to_assign < HEIGHT) {
                int start_row = next_row_to_assign;
                int end_row = min(next_row_to_assign + CHUNK_SIZE, HEIGHT);
                int work_data[2] = {start_row, end_row};
                MPI_Send(work_data, 2, MPI_INT, i, 0, MPI_COMM_WORLD); // Tag 0 for work
                next_row_to_assign = end_row;
                active_workers++;
            } else {
                // 如果沒有足夠的行數分配給所有 worker，則發送終止信號
                int work_data[2] = {-1, -1}; // -1 表示終止
                MPI_Send(work_data, 2, MPI_INT, i, 0, MPI_COMM_WORLD);
            }
        }

        // 循環接收結果並分發新工作
        while (active_workers > 0) {
            int received_data[2]; // [start_row, num_rows_computed]
            MPI_Recv(received_data, 2, MPI_INT, MPI_ANY_SOURCE, 1, MPI_COMM_WORLD, &status); // Tag 1 for result
            int sender_rank = status.MPI_SOURCE;
            int start_row_received = received_data[0];
            int num_rows_computed = received_data[1];

            // 接收計算好的圖像數據
            MPI_Recv(&image[start_row_received * WIDTH * 3], num_rows_computed * WIDTH * 3,
                     MPI_UNSIGNED_CHAR, sender_rank, 2, MPI_COMM_WORLD, &status); // Tag 2 for image data

            // 分發新的工作或終止信號
            if (next_row_to_assign < HEIGHT) {
                int start_row = next_row_to_assign;
                int end_row = min(next_row_to_assign + CHUNK_SIZE, HEIGHT);
                int work_data[2] = {start_row, end_row};
                MPI_Send(work_data, 2, MPI_INT, sender_rank, 0, MPI_COMM_WORLD);
                next_row_to_assign = end_row;
            } else {
                int work_data[2] = {-1, -1};
                MPI_Send(work_data, 2, MPI_INT, sender_rank, 0, MPI_COMM_WORLD);
                active_workers--;
            }
        }

    } else { // 工作程序 (Worker)
        MPI_Status status;
        int work_data[2]; // [start_row, end_row]

        while (true) {
            MPI_Recv(work_data, 2, MPI_INT, 0, 0, MPI_COMM_WORLD, &status); // 從主程序接收工作 (Tag 0)
            int start_row = work_data[0];
            int end_row = work_data[1];

            if (start_row == -1) {
                break;
            }

            int num_rows_to_compute = end_row - start_row;
            // Worker 分配局部圖像緩衝區來存儲計算結果
            unsigned char *local_image_buffer = new unsigned char[num_rows_to_compute * WIDTH * 3];

            // --- OpenMP 並行化內部循環 (針對 worker 分配到的行) ---
            #pragma omp parallel for collapse(2) schedule(dynamic)
            for (int y_local = 0; y_local < num_rows_to_compute; y_local++) {
                for (int x = 0; x < WIDTH; x++) {
                    int y = start_row + y_local;
                    complex<double> c((x - WIDTH / 2.0) * 4.0 / WIDTH,
                                                        (y - HEIGHT / 2.0) * 4.0 / HEIGHT);
                    complex<double> z = 0;
                    double min_dist = numeric_limits<double>::max();
                    int repeats = 0;

                    for (repeats = 0; repeats <= MaxRepeats; repeats++) {
                        z = z * z + c;
                        double dist = abs(z - trap);
                        if (dist < min_dist) {
                            min_dist = dist;
                        }
                        if (abs(z) > 2.0) break;
                    }

                    int index = (y_local * WIDTH + x) * 3; // 注意這裡使用 y_local
                    if (repeats > MaxRepeats) {
                        local_image_buffer[index] = 0;
                        local_image_buffer[index + 1] = 0;
                        local_image_buffer[index + 2] = 0;
                    } else {
                        double hue = 360.0 * min_dist / 2.0;
                        double saturation = 1.0;
                        double value = repeats < MaxRepeats ? 1.0 : 0.0;
                        hsv_to_rgb(hue, saturation, value, local_image_buffer[index],
                                             local_image_buffer[index + 1],
                                             local_image_buffer[index + 2]);
                    }
                }
            }

            // 將計算好的結果發送回主程序
            int result_info[2] = {start_row, num_rows_to_compute};
            MPI_Send(result_info, 2, MPI_INT, 0, 1, MPI_COMM_WORLD); // Tag 1 for result info
            MPI_Send(local_image_buffer, num_rows_to_compute * WIDTH * 3,
                     MPI_UNSIGNED_CHAR, 0, 2, MPI_COMM_WORLD); // Tag 2 for image data

            delete[] local_image_buffer;
        }
    }

    // main output
    if (world_rank == 0) {
        stbi_write_png(outputfile_name.c_str(), WIDTH, HEIGHT, 3, image, WIDTH * 3);
        cout << "Image saved to " << outputfile_name << endl;
        delete[] image;
    }

    MPI_Finalize();
    return 0;
}