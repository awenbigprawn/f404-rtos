import os
import subprocess
import sys
from collections import defaultdict
import matplotlib.pyplot as plt

def run_main_py(taskset_dir, chosenAlg):
    # algorithms = ["dm", "edf", "rr"]
    # chosenAlg = algorithms[1]
    exit_code_counts = defaultdict(int)

    for root, _, files in os.walk(taskset_dir):
        for file in files:
            task_file = os.path.join(root, file)
            if chosenAlg != "edf":
                command = [sys.executable, os.path.join(script_dir, "main.py"), "edf", task_file]
                result = subprocess.run(command, capture_output=True)
                if result.returncode == 3 or result.returncode == 2:
                    exit_code_counts[4] += 1
                    continue
            command = [sys.executable, os.path.join(script_dir, "main.py"), chosenAlg, task_file]
            result = subprocess.run(command, capture_output=True)
            exit_code_counts[result.returncode] += 1
            print(f"Running {file} with {chosenAlg}, exit code: {result.returncode}")

    return exit_code_counts

if __name__ == "__main__":
    # Ensure script runs from its directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if len(sys.argv) != 3:
        print("Usage: python plot.py <algorithm: dm/edf/rr> <taskset_directory>")
        sys.exit(1)

    chosenAlg = sys.argv[1]
    if chosenAlg not in ["dm", "edf", "rr"]:
        print("Error: Invalid algorithm. Choose from 'dm', 'edf', or 'rr'.")
        sys.exit(1)

    taskset_directory = sys.argv[2]
    if not os.path.isdir(taskset_directory):
        print(f"Error: {taskset_directory} is not a valid directory")
        sys.exit(1)

    exit_code_counts = run_main_py(taskset_directory, chosenAlg)
    success_count = exit_code_counts[0] + exit_code_counts[1]
    if chosenAlg == "edf":
        failure_count = 0
        # if edf fail, it is FJP infeasible also FTP infeasible
        infeasible_count = exit_code_counts[2] + exit_code_counts[3]
    else:
        failure_count = exit_code_counts[2] + exit_code_counts[3]
        infeasible_count = exit_code_counts[4]
    for code, count in exit_code_counts.items():
        print(f"Exit code {code}: {count} times")
    
    labels = ['Schedulable', 'Unschedulable', 'Infeasible']
    sizes = [success_count, failure_count, infeasible_count]
    colors = ['green', 'red', 'gray']

    # Plot pie chart with better configurations
    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct='%1.1f%%',
        shadow=False, startangle=90, textprops=dict(color="w")
    )
    
    for text in texts:
        text.set_fontsize(10)
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_color('black')

    ax.axis('equal')
    plt.title("Task Scheduling Results", fontsize=14, weight='bold')

    # Define output directory using script's directory as base
    output_dir = os.path.join(script_dir, "..", "docu/test")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    title1, title2 = os.path.basename(os.path.dirname(taskset_directory)), os.path.basename(taskset_directory)
    plt.savefig(os.path.join(output_dir, f'{title1}_{title2}_{chosenAlg}.png'))
    plt.show()
