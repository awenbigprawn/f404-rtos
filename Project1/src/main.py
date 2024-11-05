import datatypes
from  scheduling_functions import *
from preprocessor import *
import argparse
import math


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

    task_set = datatypes.TaskSet(tasks=[], feasibility_interval=1)
    period_set = set()
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
                    # priority=0
                )
                task_set.tasks.append(new_task)
                period_set.add(int(T))
    except FileNotFoundError:
        print("File not found, please check the provided path")
    
    scheduling_function = None
    if scheduling_algorithm == "dm":
        scheduling_function = deadline_monotonic
    elif scheduling_algorithm == "edf":
        scheduling_function = early_deadline_first
    elif scheduling_algorithm == "rr":
        scheduling_function = round_robin
    else:
        print("Invalid scheduling algorithm")

    print(task_set)
    preprocessor = Preprocessor(task_set, scheduling_algorithm)
    is_feasible = preprocessor.preprocess()

    if preprocessor.do_simulation:
        print(f"Simulation is needed, feasibility interval = {task_set.feasibility_interval}")
        schedulePassed = schedule(task_set=task_set, scheduling_function=scheduling_function, time_max=task_set.feasibility_interval, time_step=task_set.simulator_timestep)
        print(f"Simulation passed? : {schedulePassed}")
        if(schedulePassed):
            print("exit 0")
            exit(0)
        else:
            print("exit 2")
            exit(2)
    else:
        print("Simulation is not needed")
        print(f"Feasibility check passed? : {is_feasible}")
        if(is_feasible):
            print("exit 1")
            exit(1)
        else:
            print("exit 3")
            exit(3)
