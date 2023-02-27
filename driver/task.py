# -*-coding:utf-8-*-
import os, threading, json, datetime
import traceback
import settings


class TaskIdCounter(object):
    _lock = threading.RLock()

    def __init__(self, initial_value=0):
        self._value = initial_value

    def incr(self, delta=1):
        with TaskIdCounter._lock:
            self._value += delta
            return self._value


id_counter = TaskIdCounter()

def generate_task_id():
    return '{}{}'.format(datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"), str(id_counter.incr()))


class Task(object):
    def __init__(self, task_name=None, task_func=None, params=None):
        self.task_id = generate_task_id() 
        self.task_status = settings.RetCode.WAIT 
        self.task_name = task_name
        self.task_func = task_func
        self.create_time = datetime.datetime.now() 
        self.params = params
        self.task_log = settings.server_log(
            logfile=os.path.join(settings.ROOT, "logs", str(self.task_id) + "/tasks.log"),
            logger_name=str(self.task_id)
        )
        self.task_path = os.path.join(settings.ROOT, "tasks", str(self.task_id))
        self.__future = None
        self.task_log.info("tasks initializer ... ")

    def __str__(self):
        return "{'code': %s, 'msg': '%s' , 'task_id': '%s', 'task_name': '%s', 'create_time': '%s'}" % (
            self.task_status.value, self.task_status.name, self.task_id, self.task_name,
            self.create_time.strftime("%Y%m%d%H%M%S%f")
        )
    def getFuture(self):
        return self.__future

    def setFuture(self, f):
        self.__future = f
        return 1

    def update(self):
        self.task_status = settings.RetCode.RUNNING

    def persist(self):
        if not os.path.exists(self.task_path):
            os.makedirs(self.task_path)
        try:
            r = self.__future.result()
            self.task_status = settings.RetCode.SUCCESS
            result = {
                "code": self.task_status.value,
                "msg": self.task_status.name,
                "task_id": self.task_id,
                "task_name": self.task_name,
                "create_time": self.create_time.strftime("%Y%m%d%H%M%S%f"),
                "data": str(r)
            }
            with open(os.path.join(self.task_path, "success.json"), "w", encoding="utf-8") as g:
                g.write(json.dumps(result, ensure_ascii=False))
        except :
            self.task_status = settings.RetCode.FAIL
            result = {
                "code": self.task_status.value,
                "msg": self.task_status.name,
                "task_id": self.task_id,
                "task_name": self.task_name,
                "create_time": self.create_time.strftime("%Y%m%d%H%M%S%f"),
                "error": traceback.format_exc()
            }
            with open(os.path.join(self.task_path, "fail.json"), "w", encoding="utf-8") as g:
                g.write(json.dumps(result, ensure_ascii=False))

    @staticmethod
    def query(task_id):
        t = settings.EXECUTING_MAP.get(task_id, None)
        if t is None:
            task_path = os.path.join(settings.ROOT, "tasks", str(task_id))
            if os.path.exists(task_path):
                if os.path.exists(os.path.join(task_path, "success.json")):
                    with open(os.path.join(task_path, "success.json"), "r", encoding="utf-8") as g:
                        return json.load(g)
                elif os.path.exists(os.path.join(task_path, "fail.json")):
                    with open(os.path.join(task_path, "fail.json"), "r", encoding="utf-8") as g:
                        return json.load(g)
                else:
                    return {
                        "code": settings.RetCode.ABNORMAL.value,
                        "msg": settings.RetCode.ABNORMAL.name,
                        "task_id": task_id
                    }
            else:
                return {
                    "code": settings.RetCode.NOT_FOUND.value,
                    "msg": settings.RetCode.NOT_FOUND.name,
                    "task_id": task_id
                }
        else:
            return eval(str(t))
