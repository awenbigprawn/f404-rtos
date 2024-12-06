from datatypes import *
import math
import help_functions

class Preprocessor:
    def __init__(self, task_set: TaskSet, scheduling_algorithm: str):
        self.task_set = task_set
        self.scheduling_algorithm = scheduling_algorithm
        self.do_simulation = False

    def check_taskset_properties(self, is_print: bool = True):
        """
        check synchronous, constrained deadline, implicite deadline
        """
        # init a checker for implicite deadline with True
        temp_synchronous_checker = True
        temp_implicite_deadline_checker = True
        temp_constrained_deadline_checker = True
        for task in self.task_set.tasks:
            # check synchronous
            if temp_synchronous_checker and task.offset != 0:
                temp_synchronous_checker = False
                if is_print: print(task.name + " has a non-zero offset, taskset is asynchronous")
            # check deadline type
            if temp_implicite_deadline_checker and task.deadline < task.period:
                # a task has not implicite deadline, set the checker to False
                temp_implicite_deadline_checker = False
                if is_print: print(task.name + " has a deadline smaller than its period, taskset has not implicite deadline")
            if task.deadline > task.period:
                if is_print: print(task.name + " has a deadline larger than its period, taskset has arbitrary deadline")
                temp_constrained_deadline_checker = False

        # set the task_set properties
        if temp_synchronous_checker:
            self.task_set.is_synchronous = True
            if is_print: print("taskset is synchronous")
        else:
            self.task_set.is_synchronous = False
            if is_print: print("taskset is asynchronous")

        if temp_implicite_deadline_checker and temp_constrained_deadline_checker:
            self.task_set.deadline_type = "implicite"
            if is_print: print("taskset has implicite deadline")
        elif temp_constrained_deadline_checker:
            self.task_set.deadline_type = "constrained"
            if is_print: print("taskset has constrained deadline")
        else:
            self.task_set.deadline_type = "arbitrary"
            if is_print: print("taskset has arbitrary deadline")

    def set_feasibility_interval(self) -> None:
        """
        Set the feasibility interval.
        For synchronous task sets:
        * constrainted ddl:
            - For rr, use the hyperperiod
            - For edf, use the hyperperiod first, it will stop early when idle point found (Corollary 59)
            - For other FTP algorithms, use the maximum deadline among all tasks (corollary 32)
        * arbitrary ddl:
            - use the hyperperiod first, it will stop early when idle point found (Theorem 40)
        For asynchronous task sets:
        - Use Omax + 2P, where Omax is the maximum offset and P is the hyperperiod
        """
        if self.task_set.is_synchronous:
            self._set_synchronous_feasibility_interval()
        else:
            self._set_asynchronous_feasibility_interval()

    def _set_synchronous_feasibility_interval(self) -> None:
        if self.task_set.deadline_type == "implicite" or self.task_set.deadline_type == "constrained":
            if self.scheduling_algorithm in ["rr", "edf"]:
                self.task_set.feasibility_interval = self._calculate_hyper_period()
            else:
                self.task_set.feasibility_interval = max(task.deadline for task in self.task_set.tasks)
        elif self.task_set.deadline_type == "arbitrary":
            # arbitrary deadline, need find idle point, set feasibility interval to hyper period first
            self.task_set.feasibility_interval = self._calculate_hyper_period()
        else:
            print("Error: taskset has no correct deadline type")
            # for safety, set hyper period
            self.task_set.feasibility_interval = self._calculate_hyper_period()

    def _set_asynchronous_feasibility_interval(self) -> None:
        Omax = max(task.offset for task in self.task_set.tasks)
        hyper_period = self._calculate_hyper_period()
        self.task_set.feasibility_interval = Omax + 2 * hyper_period

    def _calculate_hyper_period(self) -> int:
        return math.lcm(*(task.period for task in self.task_set.tasks))

    def set_simulator_timestep(self):
        """
        Set the simulator timestep as the greatest common divisor of all tasks' C, T, D, O
        """
        def find_gcd(list_numbers):
            num1 = list_numbers[0]
            for num2 in list_numbers[1:]:
                num1 = math.gcd(num1, num2)
            return num1
        
        # find the greatest common divisor of all tasks' C, T, D, O
        temp_CTD_list = []
        for task in self.task_set.tasks:
            temp_CTD_list.extend([task.computation_time, task.period, task.deadline, task.offset])

        self.task_set.simulator_timestep = find_gcd(temp_CTD_list)

    def feasibility_check(self, is_print) -> bool:
        """
        Check if the taskset is feasible for the given scheduling algorithm, and if not sure, do simulation
        """
        # make sure do_simulation init with False
        self.do_simulation = False

        # utilisation check
        sum_utilisation = 0.0
        for task in self.task_set.tasks:
            sum_utilisation += task.utilization
            if help_functions.is_greater(sum_utilisation, 1):
                # if sum of utilisation > 1, not feasible, return False
                return False
        # if there is only one/no task in taskset
        if len(self.task_set.tasks) <= 1:
            if is_print: print("taskset has only one/no task, utiliasion check pass")
            return True
        # if taskset is implicite deadline
        if self.task_set.deadline_type == "implicite":
            # DM become RM, utilisation check possible:
            # Theorem 33
            n_task = len(self.task_set.tasks)
            if n_task > 0:
                if sum_utilisation <= n_task * (2**(1/n_task) - 1):
                    return True
            else:
                if is_print: print("taskset has no task")
                return True

        if self.scheduling_algorithm == "dm":
            # There is exact schedulability test for dm
            # sort tasks by deadline in task_set
            self.task_set.tasks = sorted(self.task_set.tasks, key=lambda task: task.deadline)
            if is_print: print(self.task_set)
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
                    if is_print: print(f"{task.name} update wcrt = {wcrt}")
                    if wcrt > task.deadline:
                        # already miss deadline, not feasible, return False
                        if is_print: print(f"{task.name} missed deadline at with wcrt >= {wcrt} > {task.deadline}")
                        return False
                    
                    if wcrt == last_wcrt:
                        if is_print: print(f"{task.name} with wcrt = {wcrt} <= {task.deadline}, pass")
                        break

                    last_wcrt = wcrt
                
                checked_tasks_list.append(task)
            # dm no need for simulation, exact feasibility check tells FTP feasibility
            return True
        
        if self.scheduling_algorithm == "edf":
            # edf is ideal for implicite deadline, utilisation check already passed
            if self.task_set.is_synchronous and self.task_set.deadline_type == "implicite":
                if is_print: print(f"taskset is synchronous and implicite deadline, no need for simulation")
                return True
            # else, must do simulation

        # round robin always need simulation
        if self.scheduling_algorithm == "rr":
            pass

        # simulation
        self.do_simulation = True
        return False


    def preprocess(self, is_print: bool = False) -> bool:
        """
        Preprocess the taskset to seek shortcuts
        """
        self.check_taskset_properties(is_print)
        
        shortcut_is_feasible = self.feasibility_check(is_print)

        if self.do_simulation:
            self.set_feasibility_interval()
            self.set_simulator_timestep()

        return shortcut_is_feasible

def preprocess_global_edf(task_set, num_cores):
    """
    Preprocess the taskset to determine if simulation is needed for asynchronous tasks on multiple cores.
    Returns is_feasible and need_simulation.
    is_feasible is True if the taskset is schedulable without simulation.
    is_feasible is False if the taskset is not schedulable or cannot be determined without simulation.
    need_simulation is True if we need to simulate to determine schedulability.
    """
    
    total_utilization = sum(task.computation_time / task.period for task in task_set.tasks)
    print(f"Total utilization: {total_utilization}")

    
    if total_utilization > num_cores:
        print("Total utilization exceeds the number of cores. Taskset is not schedulable.")
        return False, False  # Not feasible, no need to simulate

    
    print("Cannot guarantee schedulability without simulation for asynchronous tasks.")
    return False, True  # Feasibility unknown, need to simulate