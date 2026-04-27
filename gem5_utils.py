import subprocess
import re
from pathlib import Path

# --- Configuration Constants ---
GEM5_PATH = Path("~/gem5/build/X86/gem5.opt").expanduser()
CONFIG_PY = Path("~/gem5/configs/deprecated/example/se.py").expanduser()

# Mapping for Benchmarks (Paths based on your provided bash script)
BENCHMARK_ROOT = Path("~/Downloads/Project1_SPEC-master/").expanduser()
BENCHMARKS = {
    "bzip2": {
        "bin": BENCHMARK_ROOT / "401.bzip2/src/benchmark",
        "arg": BENCHMARK_ROOT / "401.bzip2/data/input.program",
        "out": BENCHMARK_ROOT / "401.bzip2/m5out"
    },
    "mcf": {
        "bin": BENCHMARK_ROOT / "429.mcf/src/benchmark",
        "arg": BENCHMARK_ROOT / "429.mcf/data/inp.in",
        "out": BENCHMARK_ROOT / "429.mcf/m5out"
    },
    "hmmer": {
        "bin": BENCHMARK_ROOT / "456.hmmer/src/benchmark",
        "arg": BENCHMARK_ROOT / "456.hmmer/data/bombesin.hmm.new",
        "out": BENCHMARK_ROOT / "456.hmmer/m5out"
    },
    "sjeng": {
        "bin": BENCHMARK_ROOT / "458.sjeng/src/benchmark",
        "arg": BENCHMARK_ROOT / "458.sjeng/data/test.txt",
        "out": BENCHMARK_ROOT / "458.sjeng/m5out"
    },
    "lbm": {
        "bin": BENCHMARK_ROOT / "470.lbm/src/benchmark",
        "arg": BENCHMARK_ROOT / "470.lbm/data/100_100_130_cf_a.of",
        "out": BENCHMARK_ROOT / "470.lbm/m5out"
    }
}

def run_simulation(bench_name, cpu_type, l1_size, l2_size, l1_assoc, l2_assoc, max_inst):
    """Runs the gem5 command based on input parameters."""
    if bench_name not in BENCHMARKS:
        print(f"Error: Benchmark {bench_name} not configured.")
        return None

    bench = BENCHMARKS[bench_name]
    output_dir = bench['out']
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(GEM5_PATH), "-d", str(output_dir),
        str(CONFIG_PY),
        "-c", str(bench['bin']),
        "-o", str(bench['arg']),
        "-I", str(max_inst),
        "--cpu-type", cpu_type,
        "--caches", "--l2cache",
        "--l1d_size", l1_size, "--l1i_size", l1_size,
        "--l2_size", l2_size,
        "--l1d_assoc", str(l1_assoc), "--l1i_assoc", str(l1_assoc),
        "--l2_assoc", str(l2_assoc),
        "--cacheline_size", "64"
    ]

    print(f"\n>>> Running gem5 for {bench_name}: L1={l1_size}, L2={l2_size}, L1Assoc={l1_assoc}, L2Assoc={l2_assoc}")
    subprocess.run(cmd, check=True)
    
    return output_dir / "stats.txt"

def analyze_results(stats_path):
    """Parses stats.txt and calculates CPI."""
    patterns = {
        'IL1_miss_count': r'system\.cpu\.icache\.overallMisses::total\s+(\d+)',
        'DL1_miss_count': r'system\.cpu\.dcache\.overallMisses::total\s+(\d+)',
        'L2_miss_count':  r'system\.l2\.overallMisses::total\s+(\d+)',
        'IL1_miss_rate':  r'system\.cpu\.icache\.overallMissRate::total\s+(\d+\.?\d*)',
        'DL1_miss_rate':  r'system\.cpu\.dcache\.overallMissRate::total\s+(\d+\.?\d*)',
        'L2_miss_rate':   r'system\.l2\.overallMissRate::total\s+(\d+\.?\d*)',
        'Total_Inst':     r'simInsts\s+(\d+)'
    }
    
    data = {}
    if not stats_path.exists():
        return f"Error: {stats_path} not found."

    with open(stats_path, 'r') as f:
        content = f.read()
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            data[key] = float(match.group(1)) if match else 0.0

    if data.get('Total_Inst', 0) == 0:
        return "Error: simInsts is 0."

    # CPI Calculation
    l1_penalty = (data['IL1_miss_count'] + data['DL1_miss_count']) * 6
    l2_penalty = data['L2_miss_count'] * 50
    cpi = 1.0 + ((l1_penalty + l2_penalty) / data['Total_Inst'])
    
    return {
        "Data": data,
        "CPI": round(cpi, 6)
    }