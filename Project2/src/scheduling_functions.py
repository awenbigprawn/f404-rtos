from datatypes import *
from partitioner import Processor
from typing import List

"""
def rate_monotonic(job_set: List[Job]) -> Job:
    
    # Returns the job with the shortest period
    
    highest_priority_job = None
    for job in job_set:
        if job.task is None:
            # error, there is no period for this job
            raise ValueError("RM scheduling: No task for the job" + str(job.job_id))
        if highest_priority_job is None or job.task.period < highest_priority_job.task.period:
            highest_priority_job = job
    return highest_priority_job

def deadline_monotonic(job_set: List[Job]) -> Job:
    
    # Returns the job with the shortest task deadline
    
    highest_priority_job = None
    for job in job_set:
        if job.task is None:
            # error, there is no ddl for this job
            raise ValueError("DM scheduling: No task for the job" + str(job.job_id))
        if highest_priority_job is None or job.task.deadline < highest_priority_job.task.deadline: 
            # deadline here must be tasks ddl, not the absolute ddl of each job
            highest_priority_job = job
    return highest_priority_job
"""

def early_deadline_first(job_set: List[Job]) -> Job:
    """
    Returns the job with the earliest absolute deadline
    """
    highest_priority_job = None
    for job in job_set:
        if highest_priority_job is None or job.deadline < highest_priority_job.deadline: 
            # EDF use the absolute ddl of each job
            highest_priority_job = job
    return highest_priority_job


"""
def round_robin(job_set: List[Job]) -> Job:
    
    # Returns the first job in List, and move it to the last position
    
    # move the first Job in the List to the last position
    job_set.append(job_set.pop(0))
    # return the moved Job, now it is on tail
    return job_set[-1]
"""

def schedule(task_set: TaskSet, scheduling_function, time_max: int, time_step: int, processor: Processor = None) -> bool:
    """
    Schedule jobs from the task set using the given scheduling function and time step
    Save logs to the processor's log attribute if provided, otherwise print
    """
    jobs: List[Job] = []
    current_time = 0
    while current_time < time_max:
        if TaskSet.is_synchronous and jobs == [] and current_time > 0:
            # if taskset is synchronous and find an idle points!
            if scheduling_function == early_deadline_first:
                # Idle point in EDF, (Corollary 59)
                log_message = f"EDF: synchronous taskset with Idle point at time {current_time}"
                if processor:
                    processor.log.append(log_message)
                else:
                    print(log_message)
                return True
        # jobs = old jobs + new jobs
        jobs.extend(task_set.release_jobs(current_time))
        for job in jobs:
            if job.deadline_missed(current_time):
                log_message = f"Deadline missed for job {job.name} at time {current_time}"
                if processor:
                    processor.log.append(log_message)
                else:
                    print(log_message)
                return False
        # schedule the job with the highest priority
        job = scheduling_function(jobs)
        if job is not None:
            job.schedule(time_step)
            if job.computing_time == 0:
                jobs.remove(job)
        # schedule the job
        current_time += time_step
    return True    

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
