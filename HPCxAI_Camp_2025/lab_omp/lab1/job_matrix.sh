#!/bin/bash
#SBATCH -A ACD114003
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 4
#SBATCH -t 5:00
#SBATCH -o job_%j.out
#SBATCH -e job_%j.err

# 編譯程式
gcc -fopenmp -o matrix_mul matrix_mul.cc

# 執行程式
time ./matrix_mul
