import os
import subprocess
import time
import matplotlib.pyplot as plt

def get_tasksets(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def time_execution(taskset, worker_count):
    start_time = time.time()
    try:
        subprocess.run(['python', './src/main.py', taskset, '8', '-v', 'partitioned', '-h', 'bf', '-s', 'du', '-w', str(worker_count)], stdout=subprocess.DEVNULL, timeout=120)
        end_time = time.time()
        return end_time - start_time, False
    except subprocess.TimeoutExpired:
        return 120, True

def main():
    tasksets_dir = 'tasksets'
    tasksets = get_tasksets(tasksets_dir)

    #tasksets.remove('tasksets\\taskset-39')
    #tasksets.remove('tasksets\\taskset-734')

    avg_times = []
    timeouts = []
    for i in range(1, 33):
        print(f"Running with {i} workers \n")
        avg_time = 0
        timeout_count = 0
        for taskset in tasksets:
            exec_time, timed_out = time_execution(taskset, i)
            if timed_out:
                timeout_count += 1
                print(f"Execution for {taskset} with {i} workers timed out")
            else:
                print(f"Execution time for {taskset} with {i} workers: {exec_time:.4f} seconds")
            avg_time += exec_time
        avg_time /= len(tasksets)
        avg_times.append(avg_time)
        timeouts.append(timeout_count)

    for i, (avg_time, timeout_count) in enumerate(zip(avg_times, timeouts)):
        print(f"Average execution time for {i+1} workers: {avg_time:.4f} seconds with {timeout_count} timeouts")

    plt.plot(range(1, 33), avg_times)
    plt.xlabel('Number of workers')
    plt.ylabel('Average execution time (seconds)')
    plt.title('Average execution time vs number of workers')
    plt.savefig('./docu/average_execution_time.png')
    plt.show()

    

if __name__ == "__main__":
    main()
