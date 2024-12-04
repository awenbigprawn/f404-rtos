from datatypes import *
import math

class Processor:
    def __init__(self, processor_id: int) -> None:
        self.processor_id = processor_id
        self.task_set = TaskSet([])
        self.jobs = []
        self.capacity = 1
        self.load = 0.0

    def __str__(self):
        # show id, capacity, load. load only show 2 decimal places
        return f"Processor{self.processor_id}: Capacity: {self.capacity}, Load: {self.load:.2f}"

class Partitioner:
    def __init__(self, task_set: TaskSet, processors: List[Processor], ordering) -> None:
        self.task_set = task_set
        self.processors = processors
        self.ordering = ordering
        self.epsilon = 1e-15

    def is_greater_or_equal(self, a, b):
        return a > b or math.isclose(a, b, abs_tol=self.epsilon)
    
    def is_smaller_or_equal(self, a, b):
        return a < b or math.isclose(a, b, abs_tol=self.epsilon)

    def is_equal(self, a, b):
        return a == b or math.isclose(a, b, abs_tol=self.epsilon)

    def partition(self, partition_method: str):
        # check task_set.tasks list is not empty
        if len(self.task_set.tasks) == 0:
            print("partioner: Task set is empty")
            return
        # check processors list is not empty
        if len(self.processors) == 0:
            print("partioner: Processors list is empty")
            return
        
        # partition the task set into processors
        # sort task set by utilization
        if self.ordering == "iu":
            # increase utilization order
            self.task_set.tasks.sort(key=lambda x: x.utilization)
        elif self.ordering == "du":
            # decrease utilization order
            self.task_set.tasks.sort(key=lambda x: x.utilization, reverse=True)
        
        # assign tasks to processors
        if partition_method == "first_fit":
            self.first_fit()
        elif partition_method == "next_fit":
            self.next_fit()
        elif partition_method == "best_fit":
            self.best_fit()
        elif partition_method == "worst_fit":
            self.worst_fit()


    # First Fit, Next Fit, Best Fit and Worst Fit
    def first_fit(self):
        # scan the processors list, find the first free processor and assign the task to it
        for task in self.task_set.tasks:
            find_processor_flag = False
            for processor in self.processors:
                print(f"c-l = {float(processor.capacity - processor.load)}, u = {task.utilization}")
                if self.is_greater_or_equal(processor.capacity - processor.load, task.utilization):
                    processor.task_set.tasks.append(task)
                    processor.load += task.utilization
                    find_processor_flag = True
                    break
            if not find_processor_flag:
                print(f"first_fit: No free processor found for task {task.task_id}")
                #TODO: not schedulable for first fit
                return
            
    def next_fit(self):
        # Next-ﬁt: assign it to the current processor being considered, and if it cannot ﬁt, it moves to the next available processor. 
        # It can never be assigned to the previous processors.
        taskset_list = self.task_set.tasks.copy()
        for processor in self.processors:
            while taskset_list:
                task = taskset_list[0]
                if self.is_greater_or_equal(processor.capacity - processor.load, task.utilization):
                    processor.task_set.tasks.append(task)
                    processor.load += task.utilization
                    taskset_list.pop(0)
                else:
                    # move to the next processor
                    break
        if taskset_list:
            print(f"next_fit: No free processor found for task {taskset_list[0].task_id}")
        #TODO: not schedulable for next fit
        return

    def best_fit(self):
        # Best-ﬁt: assign it to an eligible processor with the maximum load U(tau)
        for task in self.task_set.tasks:
            best_processor = None
            max_load = 0
            task_first_fit_flag = True
            # find the best processor
            for processor in self.processors:
                if self.is_greater_or_equal(processor.capacity - processor.load, task.utilization):
                    if task_first_fit_flag:
                        best_processor = processor
                        task_first_fit_flag = False
                        max_load = processor.load
                        continue
                    if self.is_equal(processor.load, max_load):
                        # not improving
                        continue
                    if self.is_greater_or_equal(processor.load, max_load):
                        # is actually improving, if equal, it should be continued in the if before
                        best_processor = processor
                        max_load = processor.load

            if best_processor is None:
                print(f"best_fit: No free processor found for task {task.task_id}")
                #TODO: not schedulable for best fit
                return
            else:
                best_processor.task_set.tasks.append(task)
                best_processor.load += task.utilization

    def worst_fit(self):
        # Worst-ﬁt: assign it to an eligible processor with the minimum load U(tau)
        for task in self.task_set.tasks:
            worst_processor = None
            min_load = 1
            task_first_fit_flag = True
            # find the worst processor
            for processor in self.processors:
                if self.is_greater_or_equal(processor.capacity - processor.load, task.utilization):
                    if task_first_fit_flag:
                        worst_processor = processor
                        task_first_fit_flag = False
                        min_load = processor.load
                        continue
                    if self.is_equal(processor.load, min_load):
                        # not improving
                        continue
                    if self.is_smaller_or_equal(processor.load, min_load):
                        # is actually improving, if equal, it should be continued in the if before
                        worst_processor = processor
                        min_load = processor.load
            if worst_processor is None:
                print(f"worst_fit: No free processor found for task {task.task_id}")
                #TODO: not schedulable for worst fit
                return
            else:
                worst_processor.task_set.tasks.append(task)
                worst_processor.load += task.utilization

if __name__ == "__main__":
    # tests
    test_taskset = TaskSet([Task(1, "task1", 8, 10, 10, 0), 
                            Task(2, "task2", 7, 10, 10, 0), 
                            Task(3, "task3", 6, 10, 10, 0), 
                            Task(4, "task4", 5, 10, 10, 0), 
                            Task(5, "task5", 4, 10, 10, 0),
                            Task(6, "task6", 2, 10, 10, 0),
                            Task(7, "task7", 1, 10, 10, 0)])
    print(test_taskset)
    test_processors = [Processor(1), 
                    Processor(2), 
                    Processor(3),
                    Processor(4)]

    test_partitioner = Partitioner(test_taskset, test_processors, "iu")
    test_partitioner.partition("best_fit")
    for processor in test_processors:
        print(processor)
        print(processor.task_set)
