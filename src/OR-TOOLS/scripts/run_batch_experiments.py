import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

# ================= Configuration =================
# Define the models to test (filename without .py)
MODELS = [
    "model_V5_01_OK",
    "model_V5_02"
]

# Define the time limits to test (in seconds)
TIME_LIMITS = [1200, 1800]  # 20 and 30 minutes

# Define how many times to run each configuration
ITERATIONS = 10

# Define relative paths using pathlib for better cross-platform compatibility
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "src" / "OR-TOOLS"
STATS_SCRIPT = PROJECT_ROOT / "src" / "analysis" / "generate_statistics.py"
OUTPUT_BASE_DIR = PROJECT_ROOT / "resultat" / "batch_experiments"

# =================================================

def run_experiment():
    """Run batch experiments with multiple models, time limits, and iterations."""
    print("=" * 70)
    print("Starting Batch Experiment")
    print("=" * 70)
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Models to test: {', '.join(MODELS)}")
    print(f"Time Limits: {TIME_LIMITS} seconds")
    print(f"Iterations per configuration: {ITERATIONS}")
    print(f"Output Directory: {OUTPUT_BASE_DIR}")
    print("=" * 70)
    
    # Create output directory if it doesn't exist
    OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)

    total_runs = len(MODELS) * len(TIME_LIMITS) * ITERATIONS
    current_run = 0
    
    # Track results
    results_summary = []

    for model_name in MODELS:
        model_script = MODEL_DIR / f"{model_name}.py"
        
        # Check if model file exists
        if not model_script.exists():
            print(f"\n[WARNING] Model file not found: {model_script}")
            print(f"Skipping model: {model_name}")
            continue
        
        print(f"\n{'=' * 70}")
        print(f"Testing Model: {model_name}")
        print(f"{'=' * 70}")
        
        for time_limit in TIME_LIMITS:
            for iteration in range(1, ITERATIONS + 1):
                current_run += 1
                print(f"\n[Run {current_run}/{total_runs}] Model={model_name}, TimeLimit={time_limit}s, Iteration={iteration}")
                
                # Construct filenames
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = f"{model_name}_t{time_limit}_iter{iteration:02d}_{timestamp}"
                
                sol_file = OUTPUT_BASE_DIR / f"{base_name}.csv"
                stats_file = OUTPUT_BASE_DIR / f"stats_{base_name}.xlsx"
                log_file = OUTPUT_BASE_DIR / f"log_{base_name}.txt"

                # 1. Run Solver
                print(f"  → Launching solver...")
                start_time = time.time()
                
                # Run the model script as a subprocess
                with open(log_file, "w", encoding="utf-8") as log:
                    try:
                        # Using sys.executable ensures we use the same python interpreter
                        cmd = [
                            sys.executable, 
                            str(model_script), 
                            "--time_limit", str(time_limit),
                            "--output", str(sol_file)
                        ]
                        log.write(f"Command: {' '.join(cmd)}\n")
                        log.write(f"Working Directory: {os.getcwd()}\n")
                        log.write(f"Python Version: {sys.version}\n")
                        log.write(f"{'=' * 70}\n\n")
                        log.flush()
                        
                        result = subprocess.run(
                            cmd, 
                            stdout=log, 
                            stderr=log, 
                            check=True,
                            cwd=str(PROJECT_ROOT)  # Set working directory to project root
                        )
                        
                        duration = time.time() - start_time
                        status = "SUCCESS"
                        print(f"  ✓ Solver finished in {duration:.2f}s")
                        
                    except subprocess.CalledProcessError as e:
                        duration = time.time() - start_time
                        status = "FAILED"
                        print(f"  ✗ ERROR: Solver failed after {duration:.2f}s")
                        print(f"    Check log: {log_file.name}")
                        results_summary.append({
                            "model": model_name,
                            "time_limit": time_limit,
                            "iteration": iteration,
                            "status": status,
                            "duration": duration,
                            "log_file": str(log_file)
                        })
                        continue
                    except Exception as e:
                        duration = time.time() - start_time
                        status = "ERROR"
                        print(f"  ✗ UNEXPECTED ERROR: {str(e)}")
                        log.write(f"\n\nUNEXPECTED ERROR: {str(e)}\n")
                        results_summary.append({
                            "model": model_name,
                            "time_limit": time_limit,
                            "iteration": iteration,
                            "status": status,
                            "duration": duration,
                            "log_file": str(log_file)
                        })
                        continue
                
                # 2. Run Statistics
                if sol_file.exists():
                    print(f"  → Generating statistics...")
                    try:
                        cmd_stats = [
                            sys.executable,
                            str(STATS_SCRIPT),
                            "--input", str(sol_file),
                            "--output", str(stats_file)
                        ]
                        subprocess.run(
                            cmd_stats, 
                            check=True, 
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            cwd=str(PROJECT_ROOT)
                        )
                        print(f"  ✓ Stats generated: {stats_file.name}")
                        
                        results_summary.append({
                            "model": model_name,
                            "time_limit": time_limit,
                            "iteration": iteration,
                            "status": status,
                            "duration": duration,
                            "solution_file": str(sol_file),
                            "stats_file": str(stats_file),
                            "log_file": str(log_file)
                        })
                        
                    except subprocess.CalledProcessError:
                        print(f"  ✗ ERROR: Statistics generation failed.")
                        results_summary.append({
                            "model": model_name,
                            "time_limit": time_limit,
                            "iteration": iteration,
                            "status": status,
                            "duration": duration,
                            "solution_file": str(sol_file),
                            "log_file": str(log_file),
                            "stats_error": True
                        })
                else:
                    print(f"  ⚠ WARNING: Solution file was not created. Skipping stats.")
                    results_summary.append({
                        "model": model_name,
                        "time_limit": time_limit,
                        "iteration": iteration,
                        "status": "NO_SOLUTION",
                        "duration": duration,
                        "log_file": str(log_file)
                    })

    # Print summary
    print("\n" + "=" * 70)
    print("Batch Experiment Complete!")
    print("=" * 70)
    print(f"\nTotal runs attempted: {current_run}")
    
    success_count = sum(1 for r in results_summary if r.get("status") == "SUCCESS")
    failed_count = sum(1 for r in results_summary if r.get("status") in ["FAILED", "ERROR", "NO_SOLUTION"])
    
    print(f"Successful runs: {success_count}")
    print(f"Failed runs: {failed_count}")
    
    # Save summary to file
    summary_file = OUTPUT_BASE_DIR / f"experiment_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("BATCH EXPERIMENT SUMMARY\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Models tested: {', '.join(MODELS)}\n")
        f.write(f"Time limits: {TIME_LIMITS}\n")
        f.write(f"Iterations per config: {ITERATIONS}\n")
        f.write(f"\nTotal runs: {current_run}\n")
        f.write(f"Successful: {success_count}\n")
        f.write(f"Failed: {failed_count}\n\n")
        f.write("=" * 70 + "\n")
        f.write("DETAILED RESULTS\n")
        f.write("=" * 70 + "\n\n")
        
        for r in results_summary:
            f.write(f"Model: {r['model']}, TimeLimit: {r['time_limit']}s, "
                   f"Iteration: {r['iteration']}, Status: {r['status']}, "
                   f"Duration: {r['duration']:.2f}s\n")
            if 'solution_file' in r:
                f.write(f"  Solution: {Path(r['solution_file']).name}\n")
            if 'stats_file' in r:
                f.write(f"  Stats: {Path(r['stats_file']).name}\n")
            if 'log_file' in r:
                f.write(f"  Log: {Path(r['log_file']).name}\n")
            f.write("\n")
    
    print(f"\nSummary saved to: {summary_file.name}")
    print(f"All results saved in: {OUTPUT_BASE_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    run_experiment()
