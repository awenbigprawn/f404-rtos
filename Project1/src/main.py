import datatypes
import argparse


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("algorithm", help="Scheduling algorithm", choices=["dm", "edf", "rr"])
    parser.add_argument("file", help="TaskSet file")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parseArgs()
    scheduling_algorithm = args.algorithm
    taskset_file = args.file

    task_set = datatypes.TaskSet(tasks=[])
    try:
        with open(taskset_file, 'r') as file:
            for i, line in enumerate(file):
                data = line.split(",")
                O, C, D, T = data
                new_task = datatypes.Task(
                    task_id=i,
                    name="Task_"+str(i),
                    offset=int(O),
                    computation_time=int(C),
                    deadline=int(D),
                    period=int(T),
                    priority=0
                )
                task_set.tasks.append(new_task)


    except FileNotFoundError:
        print("File not found, please check the provided path")
    
    print(task_set.tasks)
            
