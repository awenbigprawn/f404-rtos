import os
import subprocess
import sys
from collections import defaultdict
import matplotlib.pyplot as plt

def run_main_py(taskset_dir):
    algorithms = ["dm", "edf", "rr"]
    exit_code_counts = defaultdict(int)

    for root, _, files in os.walk(taskset_dir):
        for file in files:
            task_file = os.path.join(root, file)
            command = ["python", r".\Project1\src\main.py", "edf", task_file]
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
    
    labels = 'Success', 'Failure', 'Infeasible'
    sizes = [success_count, failure_count, infeasible_count]
    colors = ['green', 'red', 'gray']

    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    output_dir = r".\Project1\docu"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.savefig(os.path.join(output_dir, 'taskset_results_pie_chart.png'))
    plt.show()