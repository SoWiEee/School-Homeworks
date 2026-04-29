#!/bin/bash
#SBATCH -A ACD114003
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 4
#SBATCH -c 1
#SBATCH -t 5:00
#SBATCH -o job_%j.out
#SBATCH -e job_%j.err

# 載入環境
module purge
module load gcc/11.2.0 openmpi/5.0.2

# 設定環境變數
export OBJ="mpi_hello_world"
export FILE="mpi_hello_world.cc"

# 編譯
mpicc -o $OBJ $FILE

# 執行
mpirun -np 4 $OBJ
