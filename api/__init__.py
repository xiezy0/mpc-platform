from driver.task import Task
import settings
from flask import jsonify
from driver.respond import Respond

def api_submit(name, func, params):
    t = Task(name, func, params)
    params["##Object"] = t
    if settings.SCHEDULER_QUEUE.full():
        return jsonify({"code": settings.RetCode.FULL.value, "msg": settings.RetCode.FULL.name})
    else:
        settings.SCHEDULER_QUEUE.put(t)
        settings.EXECUTING_MAP[t.task_id] = t
        return jsonify(eval(str(t)))
def api_query(task_id):
    ret = Task.query(task_id)
    return jsonify(ret)


def api_response(func, params):
    ret = Respond.response(func, params)
    return jsonify(ret)
