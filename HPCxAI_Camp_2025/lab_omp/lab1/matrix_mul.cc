#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

// TODO: 使用 OpenMP 並行計算矩陣乘法
void matrix_multiply(int** A, int** B, int** C, int m, int n, int p) {
    #pragma omp parallel for // collapse(2)
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < p; j++) {
            int sum = 0;
            // C[i][j] = 0;
            for (int k = 0; k < n; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}

int main() {
    FILE *fa = fopen("testcases/matrix_A", "r");
    FILE *fb = fopen("testcases/matrix_B", "r");
    FILE *fc = fopen("testcases/matrix_C", "r");
    
    if (fa == NULL || fb == NULL || fc == NULL) {
        fprintf(stderr, "檔案開啟失敗！\n");
        return 1;
    }

    int m = 3000, n = 3000, p = 3000;
    int **A, **B, **C, **C_ref;

    // 配置記憶體
    A = (int**)malloc(m * sizeof(int*));
    B = (int**)malloc(n * sizeof(int*));
    C = (int**)malloc(m * sizeof(int*));
    C_ref = (int**)malloc(m * sizeof(int*));

    if (!A || !B || !C || !C_ref) return 1;

    for (int i = 0; i < m; i++) {
        A[i] = (int*)malloc(n * sizeof(int));
        C[i] = (int*)malloc(p * sizeof(int));
        C_ref[i] = (int*)malloc(p * sizeof(int));
        if (!A[i] || !C[i] || !C_ref[i]) return 1;
    }
    for (int i = 0; i < n; i++) {
        B[i] = (int*)malloc(p * sizeof(int));
        if (!B[i]) return 1;
    }

    // 讀取 A
    for (int i = 0; i < m; i++)
        for (int j = 0; j < n; j++)
            fscanf(fa, "%d", &A[i][j]);

    // 讀取 B
    for (int i = 0; i < n; i++)
        for (int j = 0; j < p; j++)
            fscanf(fb, "%d", &B[i][j]);

    // 讀取 C (參考答案)
    for (int i = 0; i < m; i++)
        for (int j = 0; j < p; j++)
            fscanf(fc, "%d", &C_ref[i][j]);

    // 執行乘法
    matrix_multiply(A, B, C, m, n, p);

    // 比對結果
    int mismatch = 0;
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < p; j++) {
            if (C[i][j] != C_ref[i][j]) {
                if (mismatch < 10) {  // 顯示前10個錯誤
                    printf("不一致：C[%d][%d] = %d, 但參考為 %d\n", i, j, C[i][j], C_ref[i][j]);
                }
                mismatch++;
            }
        }
    }

    if (mismatch == 0) {
        printf("矩陣乘法結果正確！全部比對一致。\n");
    } else {
        printf("矩陣乘法有 %d 處不一致。\n", mismatch);
    }

    // 釋放記憶體
    for (int i = 0; i < m; i++) {
        free(A[i]);
        free(C[i]);
        free(C_ref[i]);
    }
    for (int i = 0; i < n; i++) {
        free(B[i]);
    }
    free(A);
    free(B);
    free(C);
    free(C_ref);

    fclose(fa);
    fclose(fb);
    fclose(fc);

    return 0;
}
