#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os, sys
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_dir)


# example: ROOT = "/home/user/"
ROOT = current_dir + "/server"

IP = "0.0.0.0"
PORT = 8101

MAX_TIME = 2
WORKERS= 10
ONLINE_POOL = None

CACHE_MAX_LENGTH = 10
EXECUTE_MAX_LENGTH = 2
SCHEDULER_QUEUE = None
EXECUTING_MAP = {}

class GlobalVar(object):
    def __init__(self):
        self.A = None
        self.models = {}
        self.initializer()

    def initializer(self):
        self.A = 10

gv = GlobalVar()

from enum import Enum
class RetCode(Enum):
    FAIL = 0       # 执行失败
    SUCCESS = 1    # 执行成功
    RUNNING = 2    # 执行中
    WAIT = 3       # 等待中
    ABNORMAL = 8   # 异常返回
    FULL = 9       # 缓冲队列已满
    NOT_FOUND = -1  # 查询未找到该任务


import logging
from logging.handlers import TimedRotatingFileHandler
def server_log(logfile, logger_name="server"):
    log_path = os.path.dirname(os.path.abspath(logfile))
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    logging.basicConfig(filemode='a',
                        level=logging.INFO,
                        format='[%(asctime)s][%(levelname)s][%(name)s] - %(message)s')
    time_log = TimedRotatingFileHandler(filename=logfile, encoding="utf-8", when="MIDNIGHT", interval=1, backupCount=3)
    time_log.setLevel(logging.INFO)
    time_log.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s][%(name)s] - %(message)s'))
    log = logging.getLogger(logger_name)
    log.addHandler(time_log)
    return log
