#-*-coding:utf-8-*-
import queue
import traceback, os
from flask import Flask, jsonify
from werkzeug.serving import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import settings
import yaml, argparse
from driver.scheduler import Scheduler
from concurrent.futures import ThreadPoolExecutor
from api.flask_test import app as demo_app_manager


app = Flask(__name__)

API_VERSION = "v2"

@app.errorhandler(500)
def internal_server_error(e):
    settings.server_log().exception(e)
    return jsonify({"code": 100, "msg": e})


def parse_yaml(filepath: str) -> dict:
    """
    This method parses the YAML configuration file and returns the parsed info
    as python dictionary.
    Args:
        filepath (string): relative path of the YAML configuration file
    """

    try:
        with open(filepath, 'r', encoding='utf-8') as fin:
            conf_dictionary = yaml.safe_load(fin)
            return conf_dictionary
    except Exception as e:
        print("CONFIGURATION FILE NOT FOUND, USING DEFAULT ONE")
        return {}
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='RESTFUL SERVER FOR JIT MPC PLATFORM')
    parser.add_argument('-c', '--conf', default="./conf/conf.yaml", dest="conf", help="yaml file with server configuration")
    parser.add_argument('--port', type=int, default=8101)
    args = parser.parse_args()

    conf = parse_yaml(args.conf)
    IP = conf.get("IP", settings.IP)
    PORT = conf.get("IP", args.port)
    
   
    settings.MAX_TIME = conf.get("MAX_TIME", settings.MAX_TIME) 
    settings.WORKERS = conf.get("WORKERS", settings.WORKERS)
    settings.ONLINE_POOL = ThreadPoolExecutor(max_workers=settings.WORKERS)

    settings.EXECUTE_MAX_LENGTH = conf.get("EXECUTE_MAX_LENGTH", settings.EXECUTE_MAX_LENGTH)
    settings.CACHE_MAX_LENGTH = conf.get("CACHE_MAX_LENGTH", settings.CACHE_MAX_LENGTH)
    settings.SCHEDULER_QUEUE = queue.Queue(maxsize=settings.CACHE_MAX_LENGTH)

    app.url_map.strict_slashes = False  
    app = DispatcherMiddleware(
        app,
        {
            '/mpc': demo_app_manager
        }
    )

    log = settings.server_log(os.path.join(settings.ROOT, "server.log"))
    log.info("server initialize ... ")
    scheduler = Scheduler(
        task_map=settings.EXECUTING_MAP,
        cache_queue=settings.SCHEDULER_QUEUE,
        concurrent_num=settings.EXECUTE_MAX_LENGTH)
    scheduler.start()
    log.info("server start ")
    try:
        # start http server
        run_simple(hostname=IP, port=PORT, application=app, threaded=True)
    except OSError as err:
        log.error(err)
        traceback.print_exc()
    except Exception as err:
        log.error(err)
        traceback.print_exc()

