import re
from pathlib import Path

def process_stats(file_path):
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

    try:
        with open(file_path, 'r') as f:
            content = f.read()
            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    # USE FLOAT HERE. It handles 100, 0.05, and 1.2e-5 perfectly.
                    data[key] = float(match.group(1))
                else:
                    data[key] = 0.0
                    print(f"Warning: Field for {key} not found in {file_path}")

        if data.get('Total_Inst', 0) == 0:
            return "Error: simInsts is 0 or missing. Check if the simulation ran."

        # Calculation logic
        # Penalty = (Misses * Latency)
        l1_penalty = (data['IL1_miss_count'] + data['DL1_miss_count']) * 6
        l2_penalty = data['L2_miss_count'] * 50
        
        # CPI = Base CPI (1) + (Total Penalty / Total Instructions)
        # Note: Added 1.0 to ensure float division
        cpi = 1.0 + ((l1_penalty + l2_penalty) / data['Total_Inst'])
        
        return {
            "Extracted Data": data,
            "Calculated CPI": round(cpi, 6)
        }

    except FileNotFoundError:
        return f"Error: Could not find file '{file_path}'"

# --- Main Loop ---
model_type = ['401.bzip2', '429.mcf', '456.hmmer', '458.sjeng', '470.lbm']
cpu_types = ['CPU1', 'CPU2', 'CPU3']
selected_cpu = cpu_types[0]

for model in model_type:
    filepath = Path('benchmarks') / model / f"stats{selected_cpu}.txt"
    
    print(f"\n--- Processing {model} ---")
    result = process_stats(filepath)
    
    if isinstance(result, dict):
        print(f"Path: {filepath}")
        print(f"CPI: {result['Calculated CPI']}")
        print(f"L2_mr: {result['Extracted Data']['L2_miss_rate']}")
    else:
        print(result)