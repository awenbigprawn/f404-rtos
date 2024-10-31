from datatypes import *
import math

class Preprocessor:
    def __init__(self, task_set: TaskSet, scheduling_algorithm: str):
        self.task_set = task_set
        self.scheduling_algorithm = scheduling_algorithm
        self.do_simulation = False

    def check_taskset_properties(self) -> bool:
        """
        check synchronous, constrained deadline, implicite deadline
        """
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
        return True

    def set_feasibility_interval(self):
        """
        Set feasibility interval as the maximum deadline of all tasks (Corollary 32)
        """
        for task in self.task_set.tasks:
            if task.deadline > self.task_set.feasibility_interval:
                self.task_set.feasibility_interval = task.deadline

    def set_simulator_timestep(self):
        """
        Set the simulator timestep as the greatest common divisor of all tasks' C, T, D
        """
        def find_gcd(list_numbers):
            num1 = list_numbers[0]
            for num2 in list_numbers[1:]:
                num1 = math.gcd(num1, num2)
            return num1
        
        # find the greatest common divisor of all tasks' C, T, D
        temp_CTD_list = []
        for task in self.task_set.tasks:
            temp_CTD_list.extend([task.computation_time, task.period, task.deadline])

        self.task_set.simulator_timestep = find_gcd(temp_CTD_list)

    def feasibility_check(self) -> bool:
        """
        Check if the taskset is feasible for the given scheduling algorithm
        """
        # make sure do_simulation init with False
        self.do_simulation = False

        # utilisation check
        sum_utilisation = 0.0
        for task in self.task_set.tasks:
            sum_utilisation += task.computation_time / task.period
            if sum_utilisation > 1:
                # if sum of utilisation > 1, not feasible, return False
                return False

        if self.scheduling_algorithm == "dm":
            # sort tasks by deadline in task_set
            self.task_set.tasks = sorted(self.task_set.tasks, key=lambda task: task.deadline)
            print(self.task_set)
            # for task in self.task_set.tasks:
            checked_tasks_list: List[Task] = []
            for task in self.task_set.tasks:
                # compute the worst case response time for each task
                wcrt = task.computation_time
                last_wcrt = wcrt
                while(True):
                    # continue iterate until wcrt_i_k = wcrt_i_(k-1)
                    # compute wcrt_i_k = C_i + sum_j( ceil( wcrt_i_(k-1) / T_j ) * C_j )
                    wcrt = task.computation_time
                    for checked_task in checked_tasks_list:
                        wcrt += math.ceil(last_wcrt/checked_task.period) * checked_task.computation_time
                    print(f"{task.name} update wcrt = {wcrt}")
                    if wcrt > task.deadline:
                        # already miss deadline, not feasible, return False
                        print(f"{task.name} missed deadline at with wcrt >= {wcrt} > {task.deadline}")
                        return False
                    
                    if wcrt == last_wcrt:
                        print(f"{task.name} with wcrt = {wcrt} < {task.deadline}, pass")
                        break

                    last_wcrt = wcrt
                
                checked_tasks_list.append(task)
            # dm no need for simulation, exact feasibility check tells feasibility
            return True
        
        if self.scheduling_algorithm == "edf":
            # edf is ideal for implicite deadline, utilisation check already passed
            if self.task_set.is_implicite_deadline:
                return True
            # else, must do simulation

        # round robin always need simulation
        if self.scheduling_algorithm == "rr":
            pass

        # simulation
        self.do_simulation = True
        return False


    def preprocess(self) -> bool:
        """
        Preprocess the taskset to seek shortcuts
        """
        if not self.check_taskset_properties():
            raise ValueError("Taskset is not synchronous with constrained deadline, check input taskset")

        shortcut_is_feasible = self.feasibility_check()

        if self.do_simulation:
            self.set_feasibility_interval()
            self.set_simulator_timestep()

        return shortcut_is_feasible
