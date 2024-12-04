# Purpose: Defines the data types Tasks, Job and TaskSet
from typing import List
from dataclasses import dataclass, field

@dataclass
class Task:
    task_id: int
    name: str
    computation_time: int
    period: int
    deadline: int
    # priority: int
    offset: int
    utilization: float = field(init=False)

    def __post_init__(self):
        self.utilization = self.computation_time / self.period

    def __str__(self):
        return "Task: " + self.name + " " + str(self.computation_time) + " " + str(self.period) + " " + str(self.deadline) + " " + str(self.offset) + " " + str(self.utilization)

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
    feasibility_interval: int = 0
    simulator_timestep: int = 1
    is_synchronous: bool = False
    is_implicite_deadline: bool = False


    def __str__(self):
        # make a table to list all tasks
        table = "TaskSet:\n"
        table += "ID\tName\tC\tT\tD\tO\n"
        for task in self.tasks:
            table += str(task.task_id) + "\t" + task.name + "\t" + str(task.computation_time) + "\t" + str(task.period) + "\t" + str(task.deadline) + "\t" + str(task.offset) + "\n"
        return table

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
