import datatypes
from  scheduling_functions import *
from preprocessor import *
from partitioner import *
import argparse
import math
import os


def parseArgs():
    """
    parse command line arguments
    """
    parser = argparse.ArgumentParser(add_help=False)
    # Positional arguments
    parser.add_argument("file", help="Task file")
    parser.add_argument("m", type=int, help="Number of cores to allocate")

    # EDF version
    parser.add_argument("-v", required=True, help="Version of EDF to use ('global', 'partitioned', or <k> (for EDF^k))")

    # Optional arguments
    parser.add_argument("-w", type=int, help="Number of workers (default: # of cpu cores on the machine)")
    parser.add_argument("-h", help="Heuristic for partitioned EDF", choices=["ff", "nf", "bf", "wf"])
    parser.add_argument("-s", help="Ordering of tasks for partitioned EDF", choices=["iu", "du"])

    args = parser.parse_args()

    # Validate -v option
    if args.v == "partitioned":
        if args.h is None or args.s is None:
            parser.error("When 'partitioned' is selected, -h (heuristic) and -s (ordering) must be provided")
    elif args.v == "global":
        pass
    else:
        try:
            args.v = int(args.v)
        except ValueError:
            parser.error("-v must be followed by 'global', 'partitioned', or an integer value for <k> (for EDF^k)")         
    return args


if __name__ == "__main__":
    args = parseArgs()
    taskset_file = args.file
    num_cores = int(args.m)
    scheduling_algorithm = args.v

    if args.w is not None:
        num_workers = args.w
    else:
        num_workers = os.cpu_count()

    if scheduling_algorithm == "partitioned":
        heuristic = args.h
        ordering = args.s
    

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

    processor_list = []
    for i in range(num_cores):
        processor_list.append(Processor(i))
    
    print(task_set)
    
    # start processing
    scheduling_function = None
    if scheduling_algorithm == "partitioned":
        partitioner = Partitioner(task_set, processor_list, ordering)
        scheduling_function = early_deadline_first
        partitioner.partition(heuristic)

        for iProcessor in processor_list:
            preprocessor = Preprocessor(task_set, "EDF")
            is_feasible = preprocessor.preprocess()
            print(f"{iProcessor} is feasible? : {is_feasible}")

    elif scheduling_algorithm == "global":
        # TODO: add global scheduling function
        scheduling_function = early_deadline_first
    else:
        print("Invalid scheduling algorithm")

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
