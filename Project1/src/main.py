import datatypes
import argparse


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("algorithm", help="Scheduling algorithm", choices=["dm", "edf", "rr"])
    parser.add_argument("file", help="TaskSet file")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    scheduling_algorithm, taskset_file = parseArgs()

    task_set = datatypes.TaskSet(tasks=[])
    try:
        with open(taskset_file, 'r') as file:
            for line in file:
                data = line.split(",").strip()
                O, C, D, T = data
                new_task = datatypes.Task()
                new_task.offset = int(O)
                new_task.computation_time = int(C)
                new_task.deadline = int(D)
                new_task.period = int(T)
                task_set.tasks.append(new_task)

                
    except FileNotFoundError:
        print("File not found, please check the provided path")
    
    print(task_set.tasks)
            
