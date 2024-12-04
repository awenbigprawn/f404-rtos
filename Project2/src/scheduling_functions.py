from datatypes import *
from typing import List

def rate_monotonic(job_set: List[Job]) -> Job:
    """
    Returns the job with the shortest period
    """
    highest_priority_job = None
    for job in job_set:
        if job.task is None:
            # error, there is no period for this job
            raise ValueError("RM scheduling: No task for the job" + str(job.job_id))
        if highest_priority_job is None or job.task.period < highest_priority_job.task.period:
            highest_priority_job = job
    return highest_priority_job

def deadline_monotonic(job_set: List[Job]) -> Job:
    """
    Returns the job with the shortest task deadline
    """
    highest_priority_job = None
    for job in job_set:
        if job.task is None:
            # error, there is no ddl for this job
            raise ValueError("DM scheduling: No task for the job" + str(job.job_id))
        if highest_priority_job is None or job.task.deadline < highest_priority_job.task.deadline: 
            # deadline here must be tasks ddl, not the absolute ddl of each job
            highest_priority_job = job
    return highest_priority_job

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

def round_robin(job_set: List[Job]) -> Job:
    """
    Returns the first job in List, and move it to the last position
    """
    # move the first Job in the List to the last position
    job_set.append(job_set.pop(0))
    # return the moved Job, now it is on tail
    return job_set[-1]

def schedule(task_set: TaskSet, scheduling_function, time_max: int, time_step: int) -> bool:
    """
    Schedule jobs from the task set using the given scheduling function and time step
    """
    jobs:List[Job] = []
    current_time = 0
    while current_time < time_max:
        if TaskSet.is_synchronous and jobs == [] and current_time > 0:
            # if taskset is synchronous and find an idle points!
            if scheduling_function == early_deadline_first:
                # Theorem 58, Idle point in EDF
                print(f"EDF: synchronous taskset with Idle point at time {current_time}")
                return True
        # jobs = old jobs + new jobs
        jobs.extend(task_set.release_jobs(current_time))
        for job in jobs:
            if job.deadline_missed(current_time):
                print("Deadline missed for job " + job.name + " at time " + str(current_time))
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
