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
    # priority: int
    offset: int

    def release_job(self, t:int) -> 'Job':
        """
        Return a new job if the task release one at time t
        """
        if self.offset > t:
            return None
        if (t-self.offset) % self.period == 0:
            return Job(job_id=self.task_id*1000+t,
                       name=self.name+"_J"+str(t),
                       task_id=self.task_id,
                       release_time=t,
                       computing_time=self.computation_time,
                       deadline=t + self.deadline,
                    #    priority=self.priority,
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
    # priority: int
    task: Task

    def deadline_missed(self, t: int) -> bool:
        return t > self.deadline

    def schedule(self, duration: int) -> bool:
        """
        Schedule the job for the given duration
        """
        if self.computing_time <= duration:
            # job finished
            self.computing_time = 0
            return True
        else:
            self.computing_time -= duration
            # job not finished
            return False 

@dataclass
class TaskSet:
    tasks: List[Task]

    def release_jobs(self, t: int) -> List[Job]:
        """
        Return all new jobs release at time t
        """
        jobs = []
        for task in self.tasks:
            job = task.release_job(t)
            if job is not None:
                jobs.append(job)
        return jobs

def schedule(task_set: TaskSet, scheduling_function, time_max: int, time_step: int) -> bool:
    """
    Schedule jobs from the task set using the given scheduling function and time step
    """
    jobs:List[Job] = []
    current_time = 0
    while current_time < time_max:
        # jobs = old jobs + new jobs
        jobs.extend(task_set.release_jobs(current_time))
        for job in jobs:
            if job.deadline_missed(current_time):
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
