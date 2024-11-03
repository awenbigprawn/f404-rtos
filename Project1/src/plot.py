import os
import subprocess
import sys
from collections import defaultdict
import matplotlib.pyplot as plt

def run_main_py(taskset_dir):
    algorithms = ["dm", "edf", "rr"]
    chosenAlg = algorithms[2]
    exit_code_counts = defaultdict(int)

    for root, _, files in os.walk(taskset_dir):
        for file in files:
            task_file = os.path.join(root, file)
            if chosenAlg != "edf":
                command = ["python", r".\Project1\src\main.py", "edf", task_file] # run edf for feasibility
                result = subprocess.run(command, capture_output=True)
                if result.returncode == 3 or result.returncode == 2:
                    exit_code_counts[3] += 1
                    continue
            command = ["python", r".\Project1\src\main.py", chosenAlg, task_file]
            result = subprocess.run(command, capture_output=True)
            exit_code_counts[result.returncode] += 1

    return exit_code_counts

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python plot.py <taskset_directory>")
        sys.exit(1)

    taskset_directory = sys.argv[1]
    if not os.path.isdir(taskset_directory):
        print(f"Error: {taskset_directory} is not a valid directory")
        sys.exit(1)

    exit_code_counts = run_main_py(taskset_directory)
    success_count = exit_code_counts[0] + exit_code_counts[1]
    failure_count = exit_code_counts[2]
    infeasible_count = exit_code_counts[3]
    for code, count in exit_code_counts.items():
        print(f"Exit code {code}: {count} times")
    
    labels = 'Schedulable', 'Unschedulable', 'Infeasible'
    sizes = [success_count, failure_count, infeasible_count]
    colors = ['green', 'red', 'gray']

    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90)
    plt.axis('equal')

    output_dir = r".\Project1\docu"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    title1, title2 = taskset_directory.split('\\')[-2], taskset_directory.split('\\')[-1]
    plt.savefig(os.path.join(output_dir, f'{title1}_{title2}_{"rr"}.png'))
    plt.show()