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
            # deadline here must be tasks ddl, not the absolute ddl ddl of each job
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


# testing
# t1 = Task(1, "T1", computation_time=10, period=20, deadline=18, offset=0)
# t2 = Task(2, "T2", computation_time=6, period=20, deadline=20, offset=0)
# t3 = Task(3, "T3", computation_time=2, period=10, deadline=10, offset=0)

# ts1 = TaskSet([t1, t2, t3])
# print(ts1)

# schedulePassed = schedule(task_set=ts1, scheduling_function=early_deadline_first, time_max=100, time_step=1)
# print(schedulePassed)
