#!/bin/bash

# Automated gem5 design-space runner

export GEM5_DIR=~/gem5
export SPEC_DIR=~/Downloads/Project1_SPEC-master
export RESULTS_DIR=$SPEC_DIR/results_corners

MAX_INST=100000000
CPU_TYPE=TimingSimpleCPU

mkdir -p $RESULTS_DIR

# Benchmark definitions:
# name|binary|argument
BENCHMARKS=(
"401.bzip2|$SPEC_DIR/401.bzip2/src/benchmark|$SPEC_DIR/401.bzip2/data/input.program"
"429.mcf|$SPEC_DIR/429.mcf/src/benchmark|$SPEC_DIR/429.mcf/data/inp.in"
"456.hmmer|$SPEC_DIR/456.hmmer/src/benchmark|$SPEC_DIR/456.hmmer/data/bombesin.hmm.new"
"458.sjeng|$SPEC_DIR/458.sjeng/src/benchmark|$SPEC_DIR/458.sjeng/data/test.txt"
"470.lbm|$SPEC_DIR/470.lbm/src/benchmark|20 reference.dat 0 1 $SPEC_DIR/470.lbm/data/100_100_130_cf_a.of"
)

# Config definitions:
# name|L1I|L1D|L2|L1I_ASSOC|L1D_ASSOC|L2_ASSOC|CACHE_LINE
CONFIGS=(
"baseline|128kB|128kB|1MB|2|2|1|64"
"small_direct|32kB|32kB|512kB|1|1|1|64"
"small_assoc|32kB|32kB|512kB|4|4|4|64"
"balanced|128kB|128kB|2MB|2|2|2|64"
"l1_heavy|256kB|256kB|1MB|2|2|2|64"
"l2_heavy|64kB|64kB|4MB|2|2|4|64"
"data_heavy|64kB|256kB|2MB|2|2|2|64"
"instr_heavy|256kB|64kB|2MB|2|2|2|64"
"high_assoc|128kB|128kB|2MB|8|8|8|64"
"small_line|128kB|128kB|2MB|2|2|2|32"
"large_line|128kB|128kB|2MB|2|2|2|128"
)

echo "Starting all gem5 corner simulations..."
echo "Results will be saved to: $RESULTS_DIR"

for BENCH_DEF in "${BENCHMARKS[@]}"; do
    IFS="|" read -r BENCH_NAME BENCHMARK ARGUMENT <<< "$BENCH_DEF"

    for CONFIG_DEF in "${CONFIGS[@]}"; do
        IFS="|" read -r CONFIG_NAME L1I_SIZE L1D_SIZE L2_SIZE L1I_ASSOC L1D_ASSOC L2_ASSOC CACHE_LINE <<< "$CONFIG_DEF"

        OUT_DIR=$RESULTS_DIR/${BENCH_NAME}/${CONFIG_NAME}

        mkdir -p $OUT_DIR

        echo "============================================================"
        echo "Running benchmark: $BENCH_NAME"
        echo "Config: $CONFIG_NAME"
        echo "L1I=$L1I_SIZE, L1D=$L1D_SIZE, L2=$L2_SIZE"
        echo "Assoc: L1I=$L1I_ASSOC, L1D=$L1D_ASSOC, L2=$L2_ASSOC"
        echo "Cache line: $CACHE_LINE"
        echo "Output: $OUT_DIR"
        echo "============================================================"

        time $GEM5_DIR/build/X86/gem5.opt -d $OUT_DIR \
            $GEM5_DIR/configs/deprecated/example/se.py \
            -c $BENCHMARK \
            -o "$ARGUMENT" \
            -I $MAX_INST \
            --cpu-type=$CPU_TYPE \
            --caches \
            --l2cache \
            --l1d_size=$L1D_SIZE \
            --l1i_size=$L1I_SIZE \
            --l2_size=$L2_SIZE \
            --l1d_assoc=$L1D_ASSOC \
            --l1i_assoc=$L1I_ASSOC \
            --l2_assoc=$L2_ASSOC \
            --cacheline_size=$CACHE_LINE \
            > $OUT_DIR/gem5_terminal_output.txt 2>&1

        echo "Finished $BENCH_NAME / $CONFIG_NAME"
    done
done

echo "All simulations complete. The machine has survived, somehow."