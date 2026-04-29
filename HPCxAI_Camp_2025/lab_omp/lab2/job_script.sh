#!/usr/bin/bash
#SBATCH -A ACD114003
#SBATCH -p development
#SBATCH -n 1
#SBATCH -c 10
#SBATCH --exclusive
#SBATCH -J bar_calc
#SBATCH -e %j.e
#SBATCH -o %j.out

source /project/ACD114003/2025summer/omp-mpi/venv/bin/activate
export PYTHONPATH="/project/ACD114003/2025summer/omp-mpi/venv/lib/python3.6/site-packages":$PYTHONPATH
make clean
make
time ./bar_chart testcases/1.txt 1.png
deactivate
