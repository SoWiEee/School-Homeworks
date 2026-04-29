#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

#define N 1000000  
#define FILENAME "testcases/array"

int main() {
   double *arr = (double *)malloc(N * sizeof(double));
   FILE *fp;
   double sum = 0.0;
   
   fp = fopen(FILENAME, "rb");
   if(fp == NULL) {
       printf("無法開啟檔案\n"); 
       free(arr);
       return 1;
   }

   fread(arr, sizeof(double), N, fp);
   fclose(fp);

   // TODO: 使用 OpenMP 並行計算陣列總和
   #pragma omp parallel for reduction(+:sum)
   for(int i = 0; i < N; i++) {
       sum += arr[i];
   }

   printf("總和: %.2f\n", sum);
   
   free(arr);
   return 0;
}
