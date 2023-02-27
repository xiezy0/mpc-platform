from concurrent.futures import  TimeoutError
import settings
import time
import traceback

class Respond(object):

    def __init__(self) -> None:
        super().__init__()
        pass

    @staticmethod
    def response(func, params):
        ret_flag = settings.RetCode.FAIL
        try:
            future = settings.ONLINE_POOL.submit(func, params)
            time.sleep(0.001)
            if future.cancel():
                return {
                    "code": ret_flag.value, 
                    "msg": ret_flag.name, 
                    "error": "TASK FAILED, LINE IS FULL"
                    }
            else:
                ret = future.result(timeout=settings.MAX_TIME)
                ret_flag = settings.RetCode.SUCCESS
                return {
                    "code": ret_flag.value, 
                    "msg": ret_flag.name, 
                    "data": ret
                    }
        except TimeoutError:
            return {
                "code": ret_flag.value, 
                "msg": ret_flag.name,  
                "error": "time out"
                }
        except :
            return {
                "code": ret_flag.value, 
                "msg": ret_flag.name,  
                "error": traceback.format_exc()
                }
