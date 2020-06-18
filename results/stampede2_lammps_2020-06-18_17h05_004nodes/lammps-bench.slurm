#!/bin/bash
#SBATCH -J benchtool
#SBATCH -o /scratch/06280/mcawood/bench-framework/results/stampede2_lammps_2020-06-18_17h05_004nodes/benchtool.o%j
#SBATCH -e /scratch/06280/mcawood/bench-framework/results/stampede2_lammps_2020-06-18_17h05_004nodes/benchtool.e%j
#SBATCH -p test1
#SBATCH -t 4:00:00
#SBATCH -N 4
#SBATCH -n 192
#SBATCH -A A-ccsc

export   working_path=/scratch/06280/mcawood/bench-framework/results/stampede2_lammps_2020-06-18_17h05_004nodes
export    output_file=output.log
export benchmark_repo=/work/06280/mcawood/datasets
export            exe=lmp_intel_cpu_intelmpi
export    base_module=/scratch/06280/mcawood/bench-framework/build/modulefiles
export     app_module=stampede2/intel/impi/lammps/skylake-xeon/stable

export x=3
export y=4
export z=4
export t=100

export OMP_NUM_THREADS=1

ml use ${base_module}
ml ${app_module}
ml

mkdir -p ${working_path} && cd ${working_path}

cp ${benchmark_repo}/in.lj . 

ibrun $exe -var x ${x} -var y ${y} -var z ${z} -var t ${t} < in.lj > ${output_file}

/scratch/06280/mcawood/bench-framework/src/collect_hw_info.sh /scratch/06280/mcawood/bench-framework/hw_utils /scratch/06280/mcawood/bench-framework/results/stampede2_lammps_2020-06-18_17h05_004nodes/hw_report