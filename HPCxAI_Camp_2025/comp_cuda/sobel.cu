#include <iostream>
#include <cstdlib>
#include <cassert>
#include <zlib.h>
#include <png.h>
#include <cuda_runtime.h>

#define MASK_N 2
#define MASK_X 5
#define MASK_Y 5
#define SCALE 8
#define BLOCK_SIZE 16
#define SHARED_W (BLOCK_SIZE + MASK_X - 1)
#define SHARED_H (BLOCK_SIZE + MASK_Y - 1)

// Copy mask to constant memory for fast access
__constant__ int d_mask[MASK_N][MASK_X][MASK_Y];

int mask[MASK_N][MASK_X][MASK_Y] = { 
    {{ -1, -4, -6, -4, -1},
     { -2, -8,-12, -8, -2},
     {  0,  0,  0,  0,  0}, 
     {  2,  8, 12,  8,  2}, 
     {  1,  4,  6,  4,  1}},
    {{ -1, -2,  0,  2,  1}, 
     { -4, -8,  0,  8,  4}, 
     { -6,-12,  0, 12,  6}, 
     { -4, -8,  0,  8,  4}, 
     { -1, -2,  0,  2,  1}} 
};

int read_png(const char* filename, unsigned char** image, unsigned* height, 
             unsigned* width, unsigned* channels) {

    unsigned char sig[8];
    FILE* infile;
    infile = fopen(filename, "rb");

    fread(sig, 1, 8, infile);
    if (!png_check_sig(sig, 8))
        return 1;   /* bad signature */

    png_structp png_ptr;
    png_infop info_ptr;

    png_ptr = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (!png_ptr)
        return 4;   /* out of memory */
  
    info_ptr = png_create_info_struct(png_ptr);
    if (!info_ptr) {
        png_destroy_read_struct(&png_ptr, NULL, NULL);
        return 4;   /* out of memory */
    }

    png_init_io(png_ptr, infile);
    png_set_sig_bytes(png_ptr, 8);
    png_read_info(png_ptr, info_ptr);
    int bit_depth, color_type;
    png_get_IHDR(png_ptr, info_ptr, width, height, &bit_depth, &color_type, NULL, NULL, NULL);

    png_uint_32  i, rowbytes;
    png_bytep  row_pointers[*height];
    png_read_update_info(png_ptr, info_ptr);
    rowbytes = png_get_rowbytes(png_ptr, info_ptr);
    *channels = (int) png_get_channels(png_ptr, info_ptr);

    if ((*image = (unsigned char *) malloc(rowbytes * *height)) == NULL) {
        png_destroy_read_struct(&png_ptr, &info_ptr, NULL);
        return 3;
    }

    for (i = 0;  i < *height;  ++i)
        row_pointers[i] = *image + i * rowbytes;
    png_read_image(png_ptr, row_pointers);
    png_read_end(png_ptr, NULL);
    return 0;
}

void write_png(const char* filename, png_bytep image, const unsigned height, const unsigned width, 
               const unsigned channels) {
    FILE* fp = fopen(filename, "wb");
    png_structp png_ptr = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    png_infop info_ptr = png_create_info_struct(png_ptr);
    png_init_io(png_ptr, fp);
    png_set_IHDR(png_ptr, info_ptr, width, height, 8,
                 PNG_COLOR_TYPE_RGB, PNG_INTERLACE_NONE,
                 PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
    png_set_filter(png_ptr, 0, PNG_NO_FILTERS);
    png_write_info(png_ptr, info_ptr);
    png_set_compression_level(png_ptr, 1);

    png_bytep row_ptr[height];
    for (int i = 0; i < height; ++ i) {
        row_ptr[i] = image + i * width * channels;
    }
    png_write_image(png_ptr, row_ptr);
    png_write_end(png_ptr, NULL);
    png_destroy_write_struct(&png_ptr, &info_ptr);
    fclose(fp);
}

__global__ void sobel(const unsigned char* s, unsigned char* t, 
                            unsigned height, unsigned width, unsigned channels) {
    __shared__ unsigned char tile[SHARED_H][SHARED_W][3];
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int lx = threadIdx.x;
    int ly = threadIdx.y;

    for (int offset_y = ly; offset_y < SHARED_H; offset_y += blockDim.y) {
        for (int offset_x = lx; offset_x < SHARED_W; offset_x += blockDim.x) {
            int global_x = blockIdx.x * blockDim.x + offset_x - (MASK_X / 2);
            int global_y = blockIdx.y * blockDim.y + offset_y - (MASK_Y / 2);

            for (int c = 0; c < 3; ++c) {
                if (global_x >= 0 && global_x < width && global_y >= 0 && global_y < height) {
                    tile[offset_y][offset_x][c] = s[channels * (width * global_y + global_x) + c];
                } else {
                    tile[offset_y][offset_x][c] = 0;
                }
            }
        }
    }

    __syncthreads();

    if (x >= width || y >= height) return;

    // [修改] 1. 將累加器從 float 改為 int
    int val[MASK_N * 3] = {0}; // 初始化為 0

    // 使用整數進行卷積累加，避免了型別轉換的開銷
    for (int i = 0; i < MASK_N; ++i) {
        for (int v = 0; v < MASK_Y; ++v) {
            for (int u = 0; u < MASK_X; ++u) {
                int w = d_mask[i][u][v];
                int tx = lx + u;
                int ty = ly + v;
                val[i*3 + 0] += tile[ty][tx][0] * w;
                val[i*3 + 1] += tile[ty][tx][1] * w;
                val[i*3 + 2] += tile[ty][tx][2] * w;
            }
        }
    }

    // [修改] 2. 在所有卷積計算完成後，才將 int 總和轉為 float
    // Gx_r, Gx_g, Gx_b 分別是 val[2], val[1], val[0]
    // Gy_r, Gy_g, Gy_b 分別是 val[5], val[4], val[3]
    float Gx_r = (float)val[2], Gy_r = (float)val[5];
    float Gx_g = (float)val[1], Gy_g = (float)val[4];
    float Gx_b = (float)val[0], Gy_b = (float)val[3];

    // [修改] 3. 使用轉好的 float 進行最終的精確計算
    float totalR = Gx_r * Gx_r + Gy_r * Gy_r;
    float totalG = Gx_g * Gx_g + Gy_g * Gy_g;
    float totalB = Gx_b * Gx_b + Gy_b * Gy_b;

    unsigned char cR = min(255, (int)(sqrtf(totalR) / SCALE));
    unsigned char cG = min(255, (int)(sqrtf(totalG) / SCALE));
    unsigned char cB = min(255, (int)(sqrtf(totalB) / SCALE));

    int outIdx = channels * (width * y + x);
    t[outIdx + 2] = cR;
    t[outIdx + 1] = cG;
    t[outIdx + 0] = cB;
}

int main(int argc, char** argv) {
    assert(argc == 3);
    unsigned height, width, channels;
    unsigned char* host_s = NULL;
    read_png(argv[1], &host_s, &height, &width, &channels);
    size_t imgSize = height * width * channels * sizeof(unsigned char);
    unsigned char* host_t = (unsigned char*) malloc(imgSize);
    unsigned char *dev_s, *dev_t;
    cudaMalloc(&dev_s, imgSize);
    cudaMalloc(&dev_t, imgSize);


    cudaMemcpyToSymbol(d_mask, mask, sizeof(int) * MASK_N * MASK_X * MASK_Y);
    cudaMemcpy(dev_s, host_s, imgSize, cudaMemcpyHostToDevice);

    dim3 blockDim(16, 16);
    dim3 gridDim((width + blockDim.x - 1) / blockDim.x,
                 (height + blockDim.y - 1) / blockDim.y);

    sobel<<<gridDim, blockDim>>>(dev_s, dev_t, height, width, channels);
    cudaDeviceSynchronize();

    cudaMemcpy(host_t, dev_t, imgSize, cudaMemcpyDeviceToHost);
    write_png(argv[2], host_t, height, width, channels);

    cudaFree(dev_s);
    cudaFree(dev_t);
    free(host_s);
    free(host_t);

    return 0;
}