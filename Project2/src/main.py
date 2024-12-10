import datatypes
from  scheduling_functions import *
from preprocessor import *
from partitioner import *
import argparse
import math
import os

import concurrent.futures

cannot_tell: bool = False

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

    processor_list = [Processor(i) for i in range(num_cores)]

    is_feasible = None
    need_simulation = None

    if scheduling_algorithm == "partitioned":
        partitioner = Partitioner(task_set, processor_list, ordering)
        
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
        print(f"Partitioner passed? : {partition_is_possible}\n")
        
        if partition_is_possible:
            def process_processor(processor:Processor):
                preprocessor = Preprocessor(processor.task_set, "edf")
                prep_is_feasible = preprocessor.preprocess()
                processor.log.append(f"{processor} preprocess passed? : {prep_is_feasible}")
                if not prep_is_feasible and preprocessor.do_simulation:
                    # sychronize the taskset first, if the synchronous passed, asynchronous also pass
                    synchronous_taskset = processor.task_set.synchronize_self()
                    preprocessor_synchronous = Preprocessor(synchronous_taskset, "edf")
                    synchronous_prep_is_feasible = preprocessor_synchronous.preprocess()
                    processor.log.append(f"synchronous preprocess passed? : {synchronous_prep_is_feasible}")
                    print(f"{synchronous_prep_is_feasible}")

                    if synchronous_prep_is_feasible:
                        processor.log.append(f"synchronous taskset preprocess passed, asynchronous must also pass, no need to simulate")
                        return synchronous_prep_is_feasible, False
                    if not synchronous_prep_is_feasible and preprocessor_synchronous.do_simulation:
                        # if the synchronous preprocess failed, but the preprocessor.do_simulation is true, then we need to simulate
                        # the synchronous taskset
                        schedulePassed = scheduling_functions.schedule(task_set=synchronous_taskset,
                                                                       scheduling_function=early_deadline_first,
                                                                       time_max=synchronous_taskset.feasibility_interval, 
                                                                       time_step=synchronous_taskset.simulator_timestep,
                                                                       processor=processor)
                        processor.log.append(f"synchronous simulation passed? : {schedulePassed}")
                        print(f"synchronous simulation passed? : {schedulePassed}")
                        if schedulePassed:
                            return schedulePassed, True
                    
                    # if the synchronous all failed, and the preprocessor.do_simulation is true, 
                    # then we need to simulate the asynchronous taskset
                    if processor.task_set.feasibility_interval > 1e7:
                        processor.log.append(f"feasibility interval is too large, can't tell feasiblity")
                        cannot_tell = True
                        return False, False
                    processor.log.append(f"preprocess.do_simulation = {preprocessor.do_simulation}, feasibility interval = {processor.task_set.feasibility_interval}, simulator timestep = {processor.task_set.simulator_timestep}")
                    schedulePassed = processor.schedule(scheduling_function=early_deadline_first, time_max=processor.task_set.feasibility_interval, time_step=processor.task_set.simulator_timestep)
                    processor.log.append(f"Simulation passed? : {schedulePassed}")
                    return schedulePassed, preprocessor.do_simulation
                return prep_is_feasible, False

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                results = list(executor.map(process_processor, processor_list))
                results, results_need_simulation = zip(*results)
            
            for processor in processor_list:
                print(processor)
                print(processor.task_set)
                for msg in processor.log:
                    print(msg)
                print("")

            is_feasible = all(results)
            need_simulation = any(results_need_simulation)
            print("results:")
            print(results)
            print("results_need_simulation:")
            print(results_need_simulation)
            
            print(f"Overall scheduling passed? : {is_feasible}")
            print(f"Need simulation? : {need_simulation}")
        else:
            is_feasible = False
            need_simulation = False

    elif scheduling_algorithm == "global":
        preprocessor = Preprocessor(task_set, "edf")
        is_feasible, need_simulation = preprocessor.preprocess_global_edf(task_set, num_cores)
        print(f"Feasibility check preprocess passed? : {is_feasible}")
        if not is_feasible and need_simulation:
            print(f"preprocess.do_simulation = {need_simulation}, feasibility interval = {task_set.feasibility_interval}, simulator timestep = {task_set.simulator_timestep}")
            schedulePassed = schedule_global_edf(task_set, task_set.feasibility_interval, task_set.simulator_timestep, num_cores)
            print(f"Simulation passed? : {schedulePassed}")

    else:
        print(f"edf(k), k = {scheduling_algorithm}")
        k_of_edf = int(scheduling_algorithm)
        preprocessor = Preprocessor(task_set, "edf")
        is_feasible, need_simulation = preprocessor.preprocess_global_edf_k(task_set, num_cores, k_of_edf)
        if not is_feasible and need_simulation:
            print(f"preprocess.do_simulation = {need_simulation}, feasibility interval = {task_set.feasibility_interval}, simulator timestep = {task_set.simulator_timestep}")
            schedulePassed = schedule_global_edf_k(task_set, task_set.feasibility_interval, task_set.simulator_timestep, k_of_edf, num_cores)
            print(f"Simulation passed? : {schedulePassed}")

    if is_feasible is None or need_simulation is None:
       raise ValueError(f"is_feasible and need_simulation must be set to True or False. Currently: is_feasible = {is_feasible}, need_simulation = {need_simulation}")
    
    if is_feasible and need_simulation:
       print("exit 0")
       exit(0)
    elif is_feasible and not need_simulation:
       print("exit 1")
       exit(1)
    elif not is_feasible and need_simulation:
       print("exit 2")
       exit(2)
    elif not is_feasible and not need_simulation:
        if cannot_tell:
            print("exit 4")
            exit(4)
        print("exit 3")
        exit(3)
    else:
        pass
