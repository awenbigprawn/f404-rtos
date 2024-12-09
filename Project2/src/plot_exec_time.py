import os
import subprocess
import time
import matplotlib.pyplot as plt

def get_tasksets(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def time_execution(taskset, worker_count):
    start_time = time.time()
    subprocess.run(['python', './src/main.py', taskset, '8', '-v', 'partitioned', '-h', 'bf', '-s', 'du', '-w', str(worker_count)], stdout=subprocess.DEVNULL)
    end_time = time.time()
    return end_time - start_time

def main():
    tasksets_dir = 'tasksets'
    tasksets = get_tasksets(tasksets_dir)
    avg_times = []
    for i in range(1, 33):
        print(f"Running with {i} workers \n")
        avg_time = 0
        for taskset in tasksets:
            exec_time = time_execution(taskset, i)
            #print(f"Execution time for {taskset}: {exec_time:.4f} seconds")
            avg_time += exec_time
        avg_time /= len(tasksets)
    avg_times.append(avg_time)

    for i, avg_time in enumerate(avg_times):
        print(f"Average execution time for {i+1} workers: {avg_time:.4f} seconds")

    plt.plot(range(1, 33), avg_times)
    plt.xlabel('Number of workers')
    plt.ylabel('Average execution time (seconds)')
    plt.title('Average execution time vs number of workers')
    plt.savefig('./docu/average_execution_time.png')
    plt.show()

    

if __name__ == "__main__":
    main()