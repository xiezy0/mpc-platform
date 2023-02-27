#-*-coding:utf-8-*- 
import threading
import time
from concurrent.futures import ThreadPoolExecutor

class Scheduler(threading.Thread):
    def __init__(self, task_map, cache_queue, concurrent_num=1):
        super().__init__()
        self.pool = ThreadPoolExecutor(max_workers=concurrent_num)
        self.cache_queue = cache_queue
        self.task_map = task_map
        self.concurrent_num = concurrent_num

    def __release(self):
        cnt = 0 
        for k in list(self.task_map.keys()):
            v = self.task_map[k] 
            if v.getFuture() is None:
                continue
            elif v.getFuture().done():
                v = self.task_map.pop(k)
                v.persist()
            elif v.getFuture().running():
                v.update()
                cnt += 1

        if cnt >= self.concurrent_num:
            return False
        else:
            return True

    def run(self):
        while True:
            try:
                flag = self.__release()
                if flag :
                    task = self.cache_queue.get(timeout=1)
                    future = self.pool.submit(task.task_func, task.params)
                    task.setFuture(future)
                    self.task_map[task.task_id] = task
                time.sleep(1)
            except Exception:
                pass

    def stop(self):
        self.pool.shutdown(True)
