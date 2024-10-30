# Purpose: Defines the data types Tasks, Job and TaskSet
from typing import List
from dataclasses import dataclass

@dataclass
class Task:
    task_id: int
    name: str
    computation_time: int
    period: int
    deadline: int
    priority: int
    offset: int

    def release_job(self, t:int) -> 'Job':
        if self.offset > t:
            return None
        if (t-self.offset) % self.period == 0:
            return Job(job_id=self.task_id*1000+t,
                       name=self.name+"_J"+str(t),
                       task_id=self.task_id,
                       release_time=t,
                       computing_time=self.computation_time,
                       deadline=t + self.deadline,
                       priority=self.priority,
                       task=self)  # pass the task itself here
        else:
            return None
        
@dataclass
class Job:
    """computation_time: the time REMAINS to complete the job """
    job_id: int
    name: str
    task_id: int
    release_time: int
    computing_time: int
    deadline: int
    priority: int
    task: Task

    def deadline_missed(self, t: int) -> bool:
        return t > self.deadline

    def schedule(self, duration: int) -> bool:
        if self.computing_time <= duration:
            return True
        else:
            self.computing_time -= duration
            return False

@dataclass
class TaskSet:
    tasks: List[Task]

    def release_jobs(self, t: int) -> List[Job]:
        jobs = []
        for task in self.tasks:
            job = task.release_job(t)
            if job is not None:
                jobs.append(job)
        return jobs


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

def schedule(task_set: TaskSet, scheduling_function, time_max: int) -> List[Job]:
    """
    Schedule jobs from the task set using the given scheduling function and time step
    """
    current_time = 0
    jobs = []
    scheduled_jobs: List[Job] = []
    while current_time < time_max:
        jobs = task_set.release_jobs(current_time)
        if jobs:
            scheduled_job = scheduling_function(jobs)
            if scheduled_job:
                scheduled_jobs.append(scheduled_job)
        current_time += 1
    return scheduled_jobs    


t1 = Task(1, "T1", 10, 20, 20, 1, 0)
t2 = Task(2, "T2", 10, 20, 20, 2, 0)

print(t1)
j1 = t1.release_job(0)
j2 = t1.release_job(20)
print(j1)
jobset = [j1, j2]
print(rate_monotonic(jobset))
schedule(jobset, rate_monotonic, 40)
