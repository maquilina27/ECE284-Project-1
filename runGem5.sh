#!/bin/bash
# -- Automated script for ECE 284 Project 1 --

export GEM5_DIR=~/gem5

#401.bzip2
export BENCHMARK=~/Downloads/Project1_SPEC-master/401.bzip2/src/benchmark
export ARGUMENT=~/Downloads/Project1_SPEC-master/401.bzip2/data/input.program
export OUT_DIR=~/Downloads/Project1_SPEC-master/401.bzip2/m5out/

#429.mcf
#export BENCHMARK=~/Downloads/Project1_SPEC-master/429.mcf/src/benchmark
#export ARGUMENT=~/Downloads/Project1_SPEC-master/429.mcf/data/inp.in
#export OUT_DIR=~/Downloads/Project1_SPEC-master/429.mcf/m5out/

#456.hmmer
#export BENCHMARK=~/Downloads/Project1_SPEC-master/456.hmmer/src/benchmark
#export ARGUMENT=~/Downloads/Project1_SPEC-master/456.hmmer/data/bombesin.hmm.new
#export OUT_DIR=~/Downloads/Project1_SPEC-master/456.hmmer/m5out/

#458.sjeng
#export BENCHMARK=~/Downloads/Project1_SPEC-master/458.sjeng/src/benchmark
#export ARGUMENT=~/Downloads/Project1_SPEC-master/458.sjeng/data/test.txt
#export OUT_DIR=~/Downloads/Project1_SPEC-master/458.sjeng/m5out/

#470.lbm
#export BENCHMARK=~/Downloads/Project1_SPEC-master/470.lbm/src/benchmark
#export ARGUMENT="20 reference.dat 0 1 /home/casp26p1/Downloads/Project1_SPEC-master/470.lbm/data/100_100_130_cf_a.of"
#export OUT_DIR=~/Downloads/Project1_SPEC-master/470.lbm/m5out/

mkdir -p $OUT_DIR

# Students can edit these variables to optimize their CPI
CPU_TYPE=TimingSimpleCPU
#CPU_TYPE=DerivO3CPU
#CPU_TYPE=X86MinorCPU     
MAX_INST=10000
L1_SIZES=("64kB" "128kB" "256kB")
L2_SIZES=("512kB" "1MB" "2MB" "4MB")
ASSOCS=(1 2 4)
CACHE_LINE=64

# Start Nesting
for L1 in "${L1_SIZES[@]}"; do
    for L2 in "${L2_SIZES[@]}"; do
        for ASSOC in "${ASSOCS[@]}"; do

            # Create a unique directory name: e.g., 401_bzip2/L1_64kB_L2_1MB_A2
            CURRENT_OUT_DIR="${OUT_DIR}/L1_${L1}_L2_${L2}_A${ASSOC}"
            mkdir -p "$CURRENT_OUT_DIR"

            echo "------------------------------------------------"
            echo "RUNNING: L1=$L1, L2=$L2, Assoc=$ASSOC"
            echo "OUTPUT: $CURRENT_OUT_DIR"
            echo "------------------------------------------------"

            echo "Starting Gem5 Simulation ..."

            time $GEM5_DIR/build/X86/gem5.opt -d $CURRENT_OUT_DIR \
                $GEM5_DIR/configs/deprecated/example/se.py \
                -c "$BENCHMARK" \
                -o "$ARGUMENT" \
                -I $MAX_INST \
                --cpu-type=$CPU_TYPE \
                --caches \
                --l2cache \
                --l1d_size="$L1" \
                --l1i_size="$L1" \
                --l2_size="$L2" \
                --l1d_assoc="$ASSOC" \
                --l1i_assoc="$ASSOC" \
                --l2_assoc="$ASSOC" \
                --cacheline_size=$CACHE_LINE
        done
    done
done