#!/bin/bash
#SBATCH -J specfem
#SBATCH -p gp1d                # Partition
#SBATCH -N 1                   # Number of nodes
#SBATCH --ntasks-per-node=6
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:6
#SBATCH --account=ACD114003
#SBATCH -o specfem_%j.out
#SBATCH -e specfem_%j.err
#SBATCH --time=0-00:50:00      # Wall-clock time limit

module purge
module load nvhpc-24.11_hpcx-2.20_cuda-12.6 gcc10/10.2.1
# export OMPI_MCA_hwloc_base_binding_policy=none
TOTAL_RANKS=24                                          # 6 * NPROC_XI(2) * NPROC_ETA(2)

echo "[*] Cleaning up old output files..."
rm -rf ./OUTPUT_FILES/*

# --- 執行 Mesher ---
echo "[*] Starting Mesher..."
# make meshfem3D
mpirun -np $SLURM_NTASKS ./bin/xmeshfem3D > ./OUTPUT_FILES/output_mesher.txt

# 檢查 Mesher 是否成功執行
if [ $? -ne 0 ]; then
    echo "[X] Mesher failed! Check output_mesher.txt for details."
    exit 1
fi
echo "[V] Mesher finished. Output in ./OUTPUT_FILES/output_mesher.txt"

# --- 執行 Solver ---
echo "[*] Starting Solver..."
export UCX_TLS=^gdr_copy
# make clean
# make specfem3D
mpirun -np $SLURM_NTASKS ./bin/xspecfem3D &> ./OUTPUT_FILES/output_solver.txt

# 檢查 Solver 是否成功執行
if [ $? -ne 0 ]; then
    echo "[!] Solver failed! Check output_solver.txt for details."
    exit 1
fi
echo "[V] Solver finished. Output in ./OUTPUT_FILES/output_solver.txt"

echo "[V] SPECFEM3D_GLOBE simulation completed."