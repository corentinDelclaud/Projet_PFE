import os
import sys
import subprocess
import time
from datetime import datetime

# ================= Configuration =================
# Define the time limits to test (in seconds)
TIME_LIMITS = [ 3600] # 10 minutes

# Define how many times to run each configuration
ITERATIONS = 10

# Define relative paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MODEL_SCRIPT = os.path.join(PROJECT_ROOT, "src", "OR-TOOLS", "model_V4_02.py")
STATS_SCRIPT = os.path.join(PROJECT_ROOT, "src", "analysis", "generate_statistics.py")
OUTPUT_BASE_DIR = os.path.join(PROJECT_ROOT, "resultat", "batch_experiments")

# =================================================

def run_experiment():
    print("Starting Batch Experiment")
    print(f"Time Limits: {TIME_LIMITS}")
    print(f"Iterations per limit: {ITERATIONS}")
    print(f"Output Directory: {OUTPUT_BASE_DIR}")
    
    if not os.path.exists(OUTPUT_BASE_DIR):
        os.makedirs(OUTPUT_BASE_DIR)

    total_runs = len(TIME_LIMITS) * ITERATIONS
    current_run = 0

    for t_idx, time_limit in enumerate(TIME_LIMITS):
        for i_idx in range(1, ITERATIONS + 1):
            current_run += 1
            print(f"\n[{current_run}/{total_runs}] Running: Time Limit = {time_limit}s, Iteration = {i_idx}")
            
            # Construct filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"planning_t{time_limit}_iter{i_idx}_{timestamp}"
            
            sol_file = os.path.join(OUTPUT_BASE_DIR, f"{base_name}.csv")
            stats_file = os.path.join(OUTPUT_BASE_DIR, f"stats_{base_name}.xlsx")
            log_file = os.path.join(OUTPUT_BASE_DIR, f"log_{base_name}.txt")

            # 1. Run Solver
            print("  > Launching solver...")
            start_time = time.time()
            
            # Run the model script as a subprocess
            # We capture stdout/stderr to a log file
            with open(log_file, "w", encoding="utf-8") as log:
                try:
                    # Using sys.executable ensures we use the same python interpreter
                    cmd = [
                        sys.executable, 
                        MODEL_SCRIPT, 
                        "--time_limit", str(time_limit),
                        "--output", sol_file
                    ]
                    log.write(f"Command: {' '.join(cmd)}\n\n")
                    log.flush()
                    
                    subprocess.run(cmd, stdout=log, stderr=log, check=True)
                    duration = time.time() - start_time
                    print(f"  > Solver finished in {duration:.2f}s")
                    
                except subprocess.CalledProcessError:
                    print("  > ERROR: Solver failed. Check log: {log_file}")
                    continue
            
            # 2. Run Statistics
            if os.path.exists(sol_file):
                print("  > Generating statistics...")
                try:
                    cmd_stats = [
                        sys.executable,
                        STATS_SCRIPT,
                        "--input", sol_file,
                        "--output", stats_file
                    ]
                    subprocess.run(cmd_stats, check=True, stdout=subprocess.DEVNULL)
                    print(f"  > Stats generated: {os.path.basename(stats_file)}")
                except subprocess.CalledProcessError:
                    print("  > ERROR: Statistics output failed.")
            else:
                print("  > WARNING: Solution file was not created. Skipping stats.")

    print("\nBatch Experiment Complete.")

if __name__ == "__main__":
    run_experiment()
