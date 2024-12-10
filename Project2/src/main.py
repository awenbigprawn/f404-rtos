import datatypes
from scheduling_functions import *
from simulation_functions import *
from preprocessor import *
from partitioner import *
import argparse
import os
import concurrent.futures
import threading

import myglobal

def parseArgs():
    """
    parse command line arguments
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("file", help="Task file")
    parser.add_argument("m", type=int, help="Number of cores to allocate")
    parser.add_argument("-v", required=True, help="Version of EDF to use ('global', 'partitioned', or <k> (for EDF^k))")
    parser.add_argument("-w", type=int, help="Number of workers (default: # of cpu cores on the machine)")
    parser.add_argument("-h", help="Heuristic for partitioned EDF", choices=["ff", "nf", "bf", "wf"])
    parser.add_argument("-s", help="Ordering of tasks for partitioned EDF", choices=["iu", "du"])

    args = parser.parse_args()

    if args.v == "partitioned":
        if args.h is None or args.s is None:
            parser.error("When 'partitioned' is selected, -h (heuristic) and -s (ordering) must be provided")
    elif args.v == "global":
        pass
    else:
        try:
            args.v = int(args.v)
        except ValueError:
            parser.error("-v must be 'global', 'partitioned', or an integer value for EDF^k")
    return args


if __name__ == "__main__":
    args = parseArgs()
    taskset_file = args.file
    num_cores = int(args.m)
    scheduling_algorithm = args.v
    num_workers = args.w if args.w is not None else os.cpu_count()

    if scheduling_algorithm == "partitioned":
        heuristic = args.h
        ordering = args.s

    task_set = datatypes.TaskSet(tasks=[])
    period_set = set()
    try:
        with open(taskset_file, 'r') as file:
            for i, line in enumerate(file):
                data = line.split(",")
                O, C, D, T = map(int, data)
                new_task = datatypes.Task(
                    task_id=i,
                    name="Task_" + str(i),
                    offset=O,
                    computation_time=C,
                    deadline=D,
                    period=T,
                )
                task_set.tasks.append(new_task)
                period_set.add(T)
    except FileNotFoundError:
        print("File not found, please check the provided path")

    processor_list = [Processor(i) for i in range(num_cores)]
    is_feasible = None
    need_simulation = None
    cannot_tell = False

    if scheduling_algorithm == "partitioned":
        partitioner = Partitioner(task_set, processor_list, ordering)
        partitioner_method = {
            "ff": "first_fit",
            "nf": "next_fit",
            "bf": "best_fit",
            "wf": "worst_fit"
        }.get(heuristic)
        partition_is_possible = partitioner.partition(partitioner_method)
        print(f"Partitioner passed? : {partition_is_possible}\n")

        if partition_is_possible:
            infeasible_detected = threading.Event()

            def preprocess_processor(processor: Processor, synchronous_taskset: TaskSet)-> NewBool:
                preprocessor_synchronous = Preprocessor(synchronous_taskset, "edf")
                synchronous_prep_is_feasible = preprocessor_synchronous.preprocess()
                processor.log.append(f"synchronous preprocess passed? : {synchronous_prep_is_feasible}")
                
                if synchronous_prep_is_feasible == NewBool.TRUE:
                    return NewBool.TRUE

                # FALSE or CANNOT_TELL, continue the asynchronous preprocess
                preprocessor = Preprocessor(processor.task_set, "edf")
                prep_is_feasible = preprocessor.preprocess()
                processor.log.append(f"Processor{processor.processor_id} preprocess passed? : {prep_is_feasible}")

                if prep_is_feasible == NewBool.TRUE:
                    return NewBool.TRUE
                if prep_is_feasible == NewBool.FALSE:
                    return NewBool.FALSE
                if prep_is_feasible == NewBool.CANNOT_TELL:
                    # start synchronous simulation
                    return NewBool.CANNOT_TELL
                
            def simulate_processor(processor: Processor, synchronous_taskset: TaskSet)-> NewBool:
                # simulate the synchronous taskset first
                schedulePassed = schedule(task_set=synchronous_taskset,
                                          scheduling_function=early_deadline_first,
                                          time_max=synchronous_taskset.feasibility_interval, 
                                          time_step=synchronous_taskset.simulator_timestep,
                                          processor=processor)

                if schedulePassed:
                    return NewBool.TRUE
                
                # synchronous simulation failed, start asynchronous simulation
                # check the feasibility_interval first, because the asynchrounous simulation will not stop early                
                schedulePassed = processor.schedule(
                    scheduling_function=early_deadline_first,
                    time_max=processor.task_set.feasibility_interval,
                    time_step=processor.task_set.simulator_timestep
                )
                return schedulePassed

            def process_processor(processor: Processor) -> NewBool:
                # sychronize the taskset first, if the synchronous passed, asynchronous also pass
                synchronous_taskset = processor.task_set.synchronize_self()
                preprocess_result = preprocess_processor(processor, synchronous_taskset)

                if preprocess_result == NewBool.TRUE:
                    return NewBool.TRUE
                if preprocess_result == NewBool.FALSE:
                    return NewBool.FALSE

                # simulation
                processor.need_simulation = True
                simulation_result = simulate_processor(processor, synchronous_taskset)
                return simulation_result

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(process_processor, processor) for processor in processor_list]
                results = []
                try:
                    for future in concurrent.futures.as_completed(futures):
                        result = future.result()
                        if isinstance(result, NewBool):
                            results.append(result)
                            if result == NewBool.FALSE:
                                myglobal.global_stop_flag.set()
                        else:
                            raise ValueError(f"Unexpected result: {result}")
                except Exception as e:
                    print(f"Error occurred: {e}")
                finally:
                    for future in futures:
                        future.cancel()

            # Aggregate results
            simulation_results=[]
            for processor in processor_list:
                simulation_results.append(processor.need_simulation)

            print(f"Results: {results}")
            print(f"need_simulation: {simulation_results}")
            
            if NewBool.FALSE in results:
                # if there exists NewBool.FALSE in results, is_feasible is False
                is_feasible = False
            elif NewBool.CANNOT_TELL in results:
                # if there exists NewBool.CANNOT_TELL in results, cannot_tell is True
                is_feasible = False
                cannot_tell = True
            elif all(result == NewBool.TRUE for result in results):
                # if results full with NewBool.TRUE, is_feasible is True
                is_feasible = True
            else:
                # raise error illegal value
                raise ValueError(f"Unexpected result: {results}")
            
            need_simulation = any(processor.need_simulation for processor in processor_list)

            for processor in processor_list:
                print(processor)
                print(processor.task_set)
                for msg in processor.log:
                    print(msg)
                print("")
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
        raise ValueError(f"is_feasible and need_simulation must be set to True or False. Currently: is_feasible = {is_feasible}, need_simulation = {need_simulation}")
