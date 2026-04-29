#!/bin/bash
#SBATCH -A ACD114003
#SBATCH -p development
#SBATCH -n <# of process>
#SBATCH -J pi_calc
#SBATCH -t 5:00
#SBATCH -o job_%j.out
#SBATCH -e job_%j.err

module purge
module load gcc/11.2.0 openmpi/5.0.2

make clean
make
# mpirun -n <# of process> ./pi_calc <# of tests>
time srun --mpi=pmix -n 10 ./pi_calc 10000
