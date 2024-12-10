from datatypes import *
from scheduling_functions import *
from partitioner import Processor
from typing import List
import myglobal


def schedule(task_set: TaskSet, scheduling_function, 
             time_max: int, time_step: int, processor: Processor = None) -> NewBool:
    """
    Schedule jobs from the task set using the given scheduling function and time step
    Save logs to the processor's log attribute if provided, otherwise print
    """
    jobs: List[Job] = []
    current_time = 0
    if scheduling_function == early_deadline_first: edf_flag = True
    synchronous_flag = task_set.is_synchronous
    if processor: processor.log.append(f"task_set.is_synchronous:{synchronous_flag}, edf_flag:{edf_flag}")
    while current_time < time_max:
        if myglobal.global_stop_flag.is_set():
            log_message = f"other processor failed, stop simulation at time {current_time}"
            if processor:
                processor.log.append(log_message)
            else:
                print(log_message)
            return NewBool.CANNOT_TELL

        if  synchronous_flag and jobs == [] and current_time > 0:
            # if taskset is synchronous and find an idle points!
            if edf_flag:
                # Idle point in EDF, (Corollary 59)
                log_message = f"EDF: synchronous taskset with Idle point at time {current_time}"
                if processor:
                    processor.log.append(log_message)
                else:
                    print(log_message)
                return NewBool.TRUE
        # jobs = old jobs + new jobs
        jobs.extend(task_set.release_jobs(current_time))
        for job in jobs:
            if job.deadline_missed(current_time):
                log_message = f"Deadline missed for job {job.name} at time {current_time}"
                if processor:
                    processor.log.append(log_message)
                else:
                    print(log_message)
                return NewBool.FALSE
        # schedule the job with the highest priority
        job = scheduling_function(jobs)
        if job is not None:
            job.schedule(time_step)
            if job.computing_time == 0:
                jobs.remove(job)
        # move to next step
        current_time += time_step
    return NewBool.TRUE    

def schedule_global_edf(task_set: TaskSet, time_max: int, time_step: int, num_cores: int) -> bool:
    """
    Schedule jobs from the task set using the global EDF scheduling algorithm
    """
    # for now single threaded implementation
    jobs: List[Job] = []
    current_time = 0

    while current_time < time_max:
        # Release new jobs at current time
        new_jobs = task_set.release_jobs(current_time)
        jobs.extend(new_jobs)

        # Check for deadline misses
        for job in jobs:
            if job.deadline_missed(current_time):
                print(f"Deadline missed for job {job.name} at time {current_time}")
                return False

        # Sort jobs by earliest deadline
        jobs.sort(key=lambda job: job.deadline)

        # Schedule selected jobs
        for job in jobs[:num_cores]:
            job.schedule(time_step)

        # Remove completed jobs
        jobs = [job for job in jobs if job.computing_time > 0]

        current_time += time_step

    return True

def schedule_global_edf_k(task_set: TaskSet, time_max: int, time_step: int, k_value: int, num_cores: int) -> bool:
    """
    Schedule jobs from the task set using the global EDF(k) scheduling algorithm
    """
    task_set.tasks = sorted(task_set.tasks, key=lambda task: task.utilization, reverse=True)
    schedulable = True
    jobs: List[Job] = []
    current_time = 0
    taskset_in_k = TaskSet(task_set.tasks[:k_value])
    task_set_out_k = TaskSet(task_set.tasks[k_value:])

    while current_time < time_max:
        # handle the first k taskset
        new_jobs_in_k = taskset_in_k.release_jobs(current_time)
        for job in new_jobs_in_k:
            job.priority = -1000 # set the priority to a very low value represent -infinity
        jobs.extend(new_jobs_in_k)
        
        # Release new jobs at current time
        new_jobs_out_k = task_set_out_k.release_jobs(current_time)
        for new_job in new_jobs_out_k:
            new_job.priority = new_job.deadline
        jobs.extend(new_jobs_out_k)

        # Check for deadline misses
        for job in jobs:
            if job.deadline_missed(current_time):
                print(f"Deadline missed for job {job.name} at time {current_time}")
                schedulable = False
                return schedulable

        # Sort jobs by earliest deadline
        jobs.sort(key=lambda job: job.priority)

        # Schedule selected jobs
        for job in jobs[:num_cores]:
            job.schedule(time_step)
        
        # Remove completed jobs
        jobs = [job for job in jobs if job.computing_time > 0]

        current_time += time_step

    return schedulable
