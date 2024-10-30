from datatypes import *

class Preprocessor:
    def __init__(self, task_set: TaskSet):
        self.task_set = task_set

    def preprocess(self):
        """
        Preprocess the taskset to 
        """
        # check synchronous, constrained deadline, implicite deadline
        temp_implicite_deadline_checker = True
        for task in self.task_set.tasks:
            if task.offset != 0:
                print(task.name + " has a non-zero offset, taskset is asynchronous")
                return False
            if task.deadline > task.period:
                print(task.name + " has a deadline larger than its period, taskset has arbitrary deadline")
                return False
            if temp_implicite_deadline_checker and task.deadline < task.period:
                # a task has not implicite deadline
                temp_implicite_deadline_checker = False
        self.task_set.is_implicite_deadline = temp_implicite_deadline_checker

        # set feasibility interval as the maximum deadline of all tasks (Corollary 32)
        for task in self.task_set.tasks:
            if task.deadline > self.task_set.feasibility_interval:
                self.task_set.feasibility_interval = task.deadline

        