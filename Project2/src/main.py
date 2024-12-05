import datatypes
from  scheduling_functions import *
from preprocessor import *
from partitioner import *
import argparse
import math
import os

import concurrent.futures


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
    

    task_set = datatypes.TaskSet(tasks=[])
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
    
    cores = [Processor(i) for i in range(num_cores)]

    if scheduling_algorithm == "partitioned":
        partitioner = Partitioner(task_set, cores, ordering)
        
        partitioner_method = None
        match heuristic:
            case "ff":
                partitioner_method = "first_fit"
            case "nf":
                partitioner_method = "next_fit"
            case "bf":
                partitioner_method = "best_fit"
            case "wf":
                partitioner_method = "worst_fit"
        
        partition_is_possible = partitioner.partition(partitioner_method)
        print(f"Partitioner passed? : {partition_is_possible}")
        
        for processor in cores:
            print(processor)
            print(processor.task_set)


        def run_processor(processor):
            preprocessor = Preprocessor(processor.task_set, "edf")
            prep_is_feasible = preprocessor.preprocess()
            if prep_is_feasible:
                schedulePassed = schedule(task_set=processor.task_set, scheduling_function=early_deadline_first, time_max=task_set.feasibility_interval, time_step=task_set.simulator_timestep)
            else:
                schedulePassed = False
            return f"Processor {processor.processor_id} passed? : {schedulePassed}"

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            results = executor.map(run_processor, cores)
            for result in results:
                print(result)
    

        
        # if partition_is_feasible:
        #     for processor in cores:
        #         print(processor)
        #         print(processor.task_set)
        #         preprocessor = Preprocessor(processor.task_set, "edf")
        #         prep_is_feasible = preprocessor.preprocess()
        #         print(f"Feasibility check preprocess passed? : {prep_is_feasible}")
        #         if prep_is_feasible:
        #             print(f"preprocess.do_simulation = {preprocessor.do_simulation}, feasibility interval = {processor.task_set.feasibility_interval}, simulator timestep = {processor.task_set.simulator_timestep}")
        #             if preprocessor.do_simulation:
        #                 print(f"Simulation is needed, feasibility interval = {processor.task_set.feasibility_interval}")
        #                 schedulePassed = schedule(task_set=processor.task_set, scheduling_function=early_deadline_first, time_max=processor.task_set.feasibility_interval, time_step=processor.task_set.simulator_timestep)
        #                 print(f"Simulation passed? : {schedulePassed}")        
    elif scheduling_algorithm == "global":
        # for now single threaded implementation
        schedulable = True
        time_max = task_set.feasibility_interval
        time_step = task_set.simulator_timestep
        jobs = []
        current_time = 0
        while current_time < time_max:
            # Release new jobs at current time
            new_jobs = task_set.release_jobs(current_time)
            jobs.extend(new_jobs)

            # Remove completed jobs
            jobs = [job for job in jobs if job.computing_time > 0]

            # Check for deadline misses
            for job in jobs:
                if job.deadline_missed(current_time):
                    print(f"Deadline missed for job {job.name} at time {current_time}")
                    schedulable = False

            # Sort jobs by earliest deadline
            jobs.sort(key=lambda job: job.deadline)

            # Select up to m jobs to schedule on m cores
            scheduled_jobs = jobs[:num_cores]

            # Schedule selected jobs
            for job in scheduled_jobs:
                job.schedule(time_step)

            current_time += time_step

        print(f"Global EDF scheduling passed? : {schedulable}")


    else:
        for processor in cores:
            print(processor)
            print(processor.task_set)

    """
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
            exit(3)"""
