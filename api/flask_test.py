#!/usr/bin/env python
# -*- coding: utf-8 -*-
# by vellhe 2017/7/9
import api
from flask import Flask, abort, request, jsonify
from SrcCode.main_dynamic_function import start_mpc
from SrcCode.compile_dynamic_function import mpc_compile
from SrcCode.communication_dynamic_function import mpc_communication
import json as js

app = Flask(__name__)


@app.route('/compile', methods=['POST'])
def compile():
    params = request.json
    return api.api_submit("compilatiion", mpc_compile, params)

@app.route('/communicate', methods=['post'])
def communicate():
    params = request.json
    return api.api_submit("communication", mpc_communication, params)

@app.route('/start', methods=['POST'])
def add_task():
    #start_mpc(request.json)
    params = request.json
    if isinstance(params, str):
        params = js.loads(params)
        print(params)
    return api.api_submit("whole process", start_mpc, params)

@app.route('/status', methods=['GET'])
def api_get_id():
    task_id = request.args['task_id']
    return api.api_query(task_id)



