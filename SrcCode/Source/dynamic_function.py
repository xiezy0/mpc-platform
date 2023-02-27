#!/usr/bin/env python3
"""
This file contains the core function of converter between the frontend and backend with the .json file as the bridge.
The .json file is the main input source of the only class of the current file.

"""
import sys
import os
sys.path.append(os.curdir)
from logging.handlers import TimedRotatingFileHandler
import logging
from Compiler.util import max, min, mod2m
from Compiler import ml
from Compiler.mpc_math import *
from Compiler.library import *
from SrcCode.Source._func.svm import svc

DATA_DIR = "opt/data"


def server_log(logfile, logger_name="server"):
    """
    服务日志模块，打印日志
    :param logfile: log 文件名
    :param logger_name: [2021-03-03 11:24:23,815][INFO][logger_name]
    :return:
    """
    log_path = os.path.dirname(os.path.abspath(logfile))
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    logging.basicConfig(filemode='a',
                        level=logging.INFO,
                        format='[%(asctime)s][%(levelname)s][%(name)s] - %(message)s')
    # 按日期分割日志，保留3天
    time_log = TimedRotatingFileHandler(filename=logfile, encoding="utf-8", when="MIDNIGHT", interval=1, backupCount=3)
    time_log.setLevel(logging.INFO)
    time_log.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s][%(name)s] - %(message)s'))
    log = logging.getLogger(logger_name)
    log.addHandler(time_log)
    return log


class DynamicVariables(object):

    def __init__(self, meta_js, task_id=8888):
        # For loop has its parameter as n_threads. But the effect is unknown.
        self.n_threads = 16
        # Recording the feature dimension of each party.
        self.n_dimension_list = []
        # Read the from input js parameters.
        self.meta_js = meta_js
        # Get the input party numbers.
        self.n_parties = int(self.meta_js["n_party"])
        # Read the basic length of each data feature.
        self.n_length_basic = int(self.meta_js["n_length_basic"])
        # Set the output data length of statics.
        self.n_length_statics_result = 1
        self.n_length_ai = self.meta_js.get("n_length_ai", None)
        self.d_ai = self.meta_js.get("ai dimension", None)
        self.n_parties_list = 0
        self.input_length_dict = 0
        # Read the number of calculations
        self.num_funcs = len(self.meta_js["components"])
        # Collect the basic operation result
        self.res_basic = None
        # Collect the statics result
        self.res_statics = None
        # Collect the ai result
        self.res_ai = None
        self.names = self.__dict__  # Python 的类对象的属性储存在的 __dict__ 中。__dict__ 是一个词典，键为属性名，值对应属性的值。
        # Update all parameters and generate variables.
        self.input_analysis()
        # Set log file dir
        logfile = f'{DATA_DIR}/{task_id}/mp_spdz.log'
        self.log = server_log(logfile)

        ######################### read input ######################################################################
        #print(self.n_parties_list, self.n_dimension_list, self.input_length_dict, '\n')
        self.log.info("initialize ...")
        party_data_length = []
        for i in range(len(self.n_parties_list)):  # init variable
            single_party_data_total_length = 0
            for key in list(self.input_length_dict.keys()):
                if isinstance(key, str) is True and key[:5] == 'data' + str(i):
                    single_party_data_total_length += self.input_length_dict[key]
            party_data_length.append(single_party_data_total_length)
        self.log.info(
            '\n PLAYER 1 UPLOADS {} DATA; \n PLAYER 2 UPLOADS {} DATA \n'.format(
                party_data_length[0],
                party_data_length[1]))
        # print('\n PLAYER 1 UPLOADS {} DATA; \n PLAYER 2 UPLOADS {} DATA \n'.format(party_data_length[0], party_data_length[1]))
        for i in range(len(self.n_parties_list)):  # init variable
            party_i = self.n_parties_list[i]
            self.names['data' + str(party_i)] = sfix.Array(party_data_length[i])
            self.names['data' + str(party_i)].input_from(party_i)
            column_i = self.n_dimension_list[i]
            single_party_length_list = [0]
            upedge_list = [0]
            self.log.info("load data from party %d, data: %s" % (party_i, self.names['data' + str(party_i)]))
            # print_ln("load data from party %d, data: %s" % (party_i, self.names['data' + str(party_i)].reveal()))

            for j in range(len(column_i)):
                single_party_length_list.append(self.input_length_dict['data' + str(party_i) + '-' + str(column_i[j])])
                self.names['data' + str(party_i) + '-' + str(column_i[j])] = sfix.Array(single_party_length_list[j+1])
                upedge_list.append(sum(single_party_length_list))
                self.names['data' + str(party_i) + '-' + str(column_i[j])
                           ] = self.names['data' + str(party_i)][upedge_list[j]:upedge_list[j+1]]
        ######################### read input ######################################################################

        self.log.info("load data success ... ")

        self.statics_function_map_l1 = {
            "max": self.calc_max,
            "min": self.calc_min,
            "avg": self.calc_avg,
            "std": self.calc_std,
            "var": self.calc_var,
            "med": self.calc_med,
        }
        self.basic_function_map = {
            "sin": self.calc_sin,
            "cos": self.calc_cos,
            "tan": self.calc_tan,
            "tanh": self.calc_tanh,
            "add": self.add,
            "sub": self.sub,
            "div": self.div,
            "mul": self.multiplication,
            "gt": self.comp_gt,
            "ge": self.comp_ge,
            "lt": self.comp_lt,
            "le": self.comp_le,
            "eq": self.comp_eq,
            "sqrt": self.calc_sqrt,
            "softmax": self.ml_softmax,
            "log2": self.calc_log2
        }
        self.ai_function_map = {
            "svc": self.calc_svc
        }
        self.full_function_map = dict(self.basic_function_map, **self.statics_function_map_l1, **self.ai_function_map)
        self.num_basic = 0
        self.num_statics = 0
        self.num_ai = 0 
        self.basic_func_list = []
        self.statcs_func_list = []
        self.ai_func_list = []
        func_raw_list = []
        for single_comp in self.meta_js["components"]:
            func_raw_list.append(single_comp["function"])
        for func in func_raw_list:
            if func in list(self.statics_function_map_l1.keys()):
                self.statcs_func_list.append(func)
                self.num_statics += 1
            elif func in list(self.basic_function_map.keys()):
                self.basic_func_list.append(func)
                self.num_basic += 1
            elif func in list(self.ai_function_map.keys()):
                self.ai_func_list.append(func)
                self.num_ai += 1
        # unique_func = list(set(func_raw_list))
        # num_statics_check = 0
        # num_basic_check = 0
        # num_ai_check = 0
        # for func in unique_func:
        #     if func in list(self.statics_function_map_l1.keys()):
        #         num_statics_check += 1
        #     elif func in list(self.basic_function_map.keys()):
        #         num_basic_check += 1
        #     elif func in list(self.ai_function_map.keys()):
        #         num_ai_check += 1
        if self.num_basic + self.num_statics + self.num_ai != self.num_funcs:
            raise ValueError('THERE ARE NOT SUPPORTED OPERATORS')
        self.basic_module_dict = {}
        self.statics_module_dict = {}
        self.ai_module_dict = {}
        basic_count = 0
        statics_count = 0
        ai_count = 0
        for i in range(self.num_funcs):
            module_name = ''.join(filter(lambda x: not x.isdigit(), self.meta_js["components"][i]["module"]))
            if module_name in list(self.basic_function_map.keys()):
                self.basic_module_dict.update({self.meta_js["components"][i]["module"]: basic_count})
                basic_count += 1
            elif module_name in list(self.statics_function_map_l1.keys()):
                self.statics_module_dict.update({self.meta_js["components"][i]["module"]: statics_count})
                statics_count += 1
            elif module_name in list(self.ai_function_map.keys()):
                self.ai_module_dict.update({self.meta_js["components"][i]["module"]: ai_count})
                ai_count += 1
    def input_analysis(self):
        """
        Analysis the input data format and check the name rules.
        """
        modules_len = len(self.meta_js['components'])
        # Collect all input from each components in a nested style. [[]]
        nested_input = [self.meta_js['components'][i]['input'][:] for i in range(modules_len)] # input data name
        nested_length = [self.meta_js['components'][i]['data_len'][:] for i in range(modules_len)] # related input data length
        input = []
        input_length = []
        for item in nested_input:
            input += item
        for item in nested_length:
            input_length += item
        if len(input) != len(input_length):
            raise ValueError('THE AMOUNT OF "data_len" MUST BE ALIGNED WITH THE TOTAL AMOUNT OF "input"')
        input_length_dict = {input[i]: input_length[i] for i in range(len(input))}
        # todo: Need to add the check of the same array length.
        data_index = []
        for item in input:
            if isinstance(item, str) and item.startswith('data'):
                data_index.append(item[4:])
        party_index = []
        for item in data_index:
            party_index.append(int(item.split('-')[0]))
        party_index = sort(list(set(party_index)))
        n_party = len(party_index)
        party_dimensions = []
        for i in range(n_party): # dealing with the case that single party has multiple input columns.
            single_party_dimension = []
            for j in range(len(data_index)):
                if int(data_index[j].split('-')[0]) == i:
                    single_party_dimension.append(int(data_index[j].split('-')[1]))
            party_dimensions.append(single_party_dimension)
        self.n_dimension_list = [sort(list(set(i))) for i in party_dimensions]
        self.n_parties_list = party_index
        self.input_length_dict = input_length_dict
        return 0

    def eval_formula(self):
        """
                Support partial cases in min max and basic operation mixture.
                """
        funcs = self.meta_js["components"]
        count_statics = 0
        count_basics = 0
        count_ai = 0
        step_results_basic = sfix.Matrix(self.num_basic, self.n_length_basic)
        # print(self.num_basic, self.n_length_basic)
        step_results_statics = sfix.Matrix(self.num_statics, self.n_length_statics_result)
        step_results_ai = sfix.Matrix(self.num_ai, self.d_ai)
        for i in range(self.num_funcs):
            sfunc = funcs[i]
            func = sfunc['function']
            module = sfunc['module']
            if func != ''.join(filter(lambda x: not x.isdigit(), module)):
                raise ValueError("MODULE NAME AND FUNCTION NAME NOT ALIGNED !")
            # BASIC OPERATION PART
            if func in list(self.basic_function_map.keys()):
                inputs = sfunc["input"]
                vars = sfix.Matrix(len(sfunc["input"]), self.n_length_basic)
                for j in range(len(inputs)):
                    if isinstance(inputs[j], str) and inputs[j].startswith('data'):
                        if len(self.names[inputs[j]]) != self.n_length_basic:
                            err_msg = 'THE LENGTH: "{}" OF DATA: "{}" DOES NOT ALIGN WITH n_length_basic: "{}"' \
                                .format(len(self.names[inputs[j]]), inputs[j], self.n_length_basic)
                            raise ValueError(err_msg)
                        else:
                            vars[j] = self.names[inputs[j]]
                    # check the input data with .output postfix
                    elif isinstance(inputs[j], str) and inputs[j].endswith('output'):
                        funcname = ''.join(filter(lambda x: not x.isdigit(), inputs[j].split('.')[0]))
                        input_modulename = inputs[j].split('.')[0]
                        if i == 0:
                            raise ValueError("THE INPUT OF THE TOTAL FIRST OPERATOR MUST BE NUMBERS OR USERS'S DATA")
                        elif i != 0 and funcname in self.basic_function_map:
                            if input_modulename not in self.basic_module_dict:
                                err_msg = 'THE MODULE NAME : "{}" DOES NOT EXIST'.format(input_modulename)
                                raise ValueError(err_msg)
                            else:
                                basic_index = self.basic_module_dict[input_modulename]
                                vars[j] = step_results_basic[basic_index]
                        elif i != 0 and funcname in self.statics_function_map_l1:
                            if input_modulename not in self.statics_module_dict:
                                err_msg = 'THE MODULE NAME : "{}" DOES NOT EXIST'.format(input_modulename)
                                raise ValueError(err_msg)
                            else:
                                statics_index = self.statics_module_dict[input_modulename]
                                constand_expanding = sfix.Array(self.n_length_basic)
                                constand_expanding.assign_all(sfix(step_results_statics[statics_index][0]))
                                vars[j] = constand_expanding
                        else:
                            err_msg = 'DATA: "{}" HAS ILLEGAL PREFIX WITH .OUTPUT'.format(inputs[j])
                            raise ValueError(err_msg)
                    elif isinstance(inputs[j], int) or isinstance(inputs[j], float):
                        constand_expanding = sfix.Array(self.n_length_basic)
                        constand_expanding.assign_all(sfix(inputs[j]))
                        vars[j] = constand_expanding
                    else:
                        errmsg = 'NAME OF: {} is ILLEGAL INPUT'.format(inputs[j])
                        raise ValueError(errmsg)
                result = self.full_function_map[sfunc["function"]](vars)
                step_results_basic[count_basics] = result
                count_basics += 1
                self.res_basic = step_results_basic
            # STATICS PART
            elif func in list(self.statics_function_map_l1.keys()):
                inputs = sfunc["input"]
                n_inputs = len(inputs)
                length_list = sfunc["data_len"]
                upedge = [0] + [sum(length_list[:i + 1]) for i in range(n_inputs)]
                total_len = sum(length_list)
                total_ary = sfix.Array(total_len)
                for j in range(n_inputs):
                    if isinstance(inputs[j], str) and inputs[j].startswith('data'):
                        total_ary.assign(self.names[inputs[j]], upedge[j])
                    elif isinstance(inputs[j], str) and inputs[j].endswith('output'):
                        funcname = ''.join(filter(lambda x: not x.isdigit(), inputs[j].split('.')[0]))
                        input_modulename = inputs[j].split('.')[0]
                        if i == 0:
                            raise ValueError("THE INPUT OF THE TOTAL FIRST OPERATOR MUST BE NUMBERS OR USERS'S DATA")
                        elif i != 0 and funcname in self.basic_function_map:
                            if input_modulename not in self.basic_module_dict:
                                err_msg = 'THE MODULE NAME : "{}" DOES NOT EXIST'.format(input_modulename)
                                raise ValueError(err_msg)
                            else:
                                basic_index = self.basic_module_dict[input_modulename]
                                total_ary.assign(step_results_basic[basic_index], upedge[j])
                        elif i != 0 and funcname in self.statics_function_map_l1:
                            if input_modulename not in self.statics_module_dict:
                                err_msg = 'THE MODULE NAME : "{}" DOES NOT EXIST'.format(input_modulename)
                                raise ValueError(err_msg)
                            else:
                                statics_index = self.statics_module_dict[input_modulename]
                                constand_expanding = sfix.Array(self.n_length_basic)
                                constand_expanding.assign_all(sfix(step_results_statics[statics_index][0]))
                                total_ary.assign(constand_expanding, upedge[j])
                        else:
                            err_msg = 'DATA: "{}" HAS ILLEGAL PREFIX WITH .OUTPUT'.format(inputs[j])
                            raise ValueError(err_msg)
                    elif isinstance(inputs[j], int) or isinstance(inputs[j], float):
                        constand_expanding = sfix.Array(self.n_length_basic)
                        constand_expanding.assign_all(sfix(inputs[j]))
                        total_ary.assign(constand_expanding, upedge[j])
                    else:
                        errmsg = 'NAME OF: {} is ILLEGAL INPUT'.format(inputs[j])
                        raise ValueError(errmsg)
                result = self.statics_function_map_l1[sfunc["function"]](total_ary)

                step_results_statics[self.statics_module_dict[module]] = result
                count_statics += 1
            # AI PART
            elif func in list(self.ai_function_map.keys()):
                meta_para = sfunc.get("meta parameters", None)
                if meta_para is None:
                    raise ValueError("META PARAMS IS EMPTY")
                sfunc.get("direction", "vertical")
                if func == "svc":
                    # require: LABEL COLUMNS AS THE LAST ONE
                    inputs = sfunc.get("input", None)
                    if inputs is None:
                        raise ValueError("NO INPUT")
                    n_inputs = len(inputs)
                    if self.n_length_ai is None:
                        raise ValueError("NO INPUT AI DATA LENGTH")
                    # from the front perspective, we allow the input data differ in length, but the joint SVC requires the data share the same length.                     
                    vars = sfix.Tensor([len(sfunc["input"]), self.n_length_ai])
                    # we do not require the order of input training data, except that the last one MUST be labels.
                    for j in range(len(inputs)):
                        if isinstance(inputs[j], str) and inputs[j].startswith('data'):
                            vars[j] = self.names[inputs[j]]
                        # check the input data with .output postfix
                        elif isinstance(inputs[j], str) and inputs[j].endswith('output'):
                            funcname = ''.join(filter(lambda x: not x.isdigit(), inputs[j].split('.')[0]))
                            input_modulename = inputs[j].split('.')[0]
                            if i == 0:
                                raise ValueError("THE INPUT OF THE TOTAL FIRST OPERATOR MUST BE NUMBERS OR USERS'S DATA")
                            elif i != 0 and funcname in self.basic_function_map:
                                if input_modulename not in self.basic_module_dict:
                                    err_msg = 'THE MODULE NAME : "{}" DOES NOT EXIST'.format(input_modulename)
                                    raise ValueError(err_msg)
                                else:
                                    basic_index = self.basic_module_dict[input_modulename]
                                    vars[j] = step_results_basic[basic_index]
                            elif i != 0 and funcname in self.statics_function_map_l1:
                                if input_modulename not in self.statics_module_dict:
                                    err_msg = 'THE MODULE NAME : "{}" DOES NOT EXIST'.format(input_modulename)
                                    raise ValueError(err_msg)
                                else:
                                    statics_index = self.statics_module_dict[input_modulename]
                                    constand_expanding = sfix.Array(self.n_length_basic)
                                    constand_expanding.assign_all(sfix(step_results_statics[statics_index][0]))
                                    vars[j] = constand_expanding
                            else:
                                err_msg = 'DATA: "{}" HAS ILLEGAL PREFIX WITH .OUTPUT'.format(inputs[j])
                                raise ValueError(err_msg)
                        elif isinstance(inputs[j], int) or isinstance(inputs[j], float):
                            errmsg = 'AI OPERATOR DOES NOT SUPPORT DATA INPUT FROM API'
                            raise ValueError(errmsg)
                        else:
                            errmsg = 'NAME OF: {} is ILLEGAL INPUT'.format(inputs[j])
                            raise ValueError(errmsg)
                    result = self.ai_function_map[sfunc["function"]](vars, meta_para)
                    step_results_ai[self.ai_module_dict[module]] = result
                    count_ai += 1
                    self.res_ai = step_results_ai
                else:
                    raise ValueError("NOW ONLY 'SVC' IS SUPPORTED")
        self.res_statics = step_results_statics
        self.res_basic = step_results_basic
        return self.res_statics, self.res_basic,self.res_ai

    def print_res(self):
        if self.res_basic is not None:
            for i in range(len(self.res_basic)):
                print_ln('The result of step %s basic operation %s is : %s', i,
                        self.basic_func_list[i], self.res_basic[i].reveal())
                # This log happens in the runtime which will not show the revealed result even though we take the .reveal()
                # cmd
                self.log.info('The result of step %s basic operation %s is : %s' %
                            (i, self.basic_func_list[i], self.res_basic[i].reveal()))
        if self.res_statics is not None:
            for i in range(len(self.res_statics)):
                print_ln('The result of step %s static operation %s is : %s', i,
                        self.statcs_func_list[i], self.res_statics[i].reveal())
                self.log.info('The result of step %s static operation %s is : %s' %
                            (i, self.statcs_func_list[i], self.res_statics[i].reveal()))
        if self.res_ai is not None:
            for i in range(len(self.res_ai)):
                print_ln('The result of step %s ai operation %s is : %s', i,
                        self.ai_func_list[i], self.res_ai[i].reveal())
                self.log.info('The result of step %s ai operation %s is : %s' %
                            (i, self.ai_func_list[i], self.res_ai[i].reveal()))

    @staticmethod
    def calc_max(var):
        res = max(var)
        # print_ln('max value is: %s',res.reveal())
        return res

    @staticmethod
    def calc_min(var):
        res = min(var)
        # print_ln('min value is: %s',res.reveal())
        return res

    @staticmethod
    def calc_avg(var):
        res = sum(var)/var.total_size()
        # print_ln('avg value is: %s', res.reveal())
        return res

    @staticmethod
    def calc_med(var):
        ttlen = var.total_size()
        var.sort()
        s = sint(mod2m(ttlen, 2, None, None))
        res = (s == sint(1)).if_else(var[int((ttlen - 1) / 2)], (var[int(ttlen / 2)] + var[int(ttlen / 2 - 1)]) / 2)
        # print_ln('med value is: %s', res.reveal())
        return res

    def calc_std(self, var):
        avg = self.calc_avg(var)
        ttlen = var.total_size()
        ares = sfix.Array(ttlen)

        @for_range(ttlen)
        def _(i):
            araw = var[i] - avg
            ares[i] = araw * araw
        res = sqrt(sum(ares)/ttlen)
        # print_ln('std value is: %s', res.reveal())
        return res

    def calc_var(self, var):
        avg = self.calc_avg(var)
        ttlen = var.total_size()
        ares = sfix.Array(ttlen)

        @for_range(ttlen)
        def _(i):
            araw = var[i] - avg
            ares[i] = araw * araw
        res = sum(ares)/ttlen
        # print_ln('std value is: %s', res.reveal())
        return res

    @staticmethod
    def add(var):
        lc = locals()
        input_dimension = len(var)
        for i in range(input_dimension):
            lc['a'+str(i)] = var[i]
        res = sum(lc['a'+str(i)] for i in range(input_dimension))
        # print_ln('add result is :%s', res.reveal())
        return res

    @staticmethod
    def sub(var):
        length = len(var)
        if length < 2:
            raise ValueError('PUT AT LEAST TWO VECTORS IN THE INPUT!')
        elif length == 2:
            res = var[0]-var[1]
        elif length > 2:
            resls = sfix.Matrix(length+1, var[0].total_size())
            resls[0] = var[0]-var[1]

            @for_range(length)
            def _(i):
                resls[i] = (i > sint(1)).if_else(resls[i-1]-var[i], var[0]-var[1])
            res = resls[length-1]
        # print_ln('sub result is :%s', res.reveal())
        return res

    def div(self, var):
        ary = sfix.Array(var.sizes[1])
        a = var[0]
        b = var[1]

        @for_range_opt_multithread(self.n_threads, a.total_size())
        def _(i):
            ary[i] = a[i]/b[i]
        res = ary
        # print_ln('array div result is :%s', res.reveal())
        return res

    @staticmethod
    def multiplication(var):
        length = len(var)
        print_ln('%s', var.reveal_nested())
        if length < 2:
            raise ValueError('PUT AT LEAST TWO VECTORS IN THE INPUT!')
        elif length == 2:
            res = var[0]*var[1]
        elif length > 2:
            resls = sfix.Matrix(length+1, var[0].total_size())
            resls[0] = var[0]*var[1]

            @for_range(length)
            def _(i):
                resls[i] = (i > sint(1)).if_else(resls[i-1]*var[i], var[0]*var[1])
            res = resls[length-1]
            # print_ln('array mul result is :%s', res.reveal())
        return res

    @staticmethod
    def calc_sin(var):
        a = var[0]
        length = a.total_size()
        res = sfix.Array(length)

        @for_range(length)
        def _(i):
            res[i] = sin(a[i])
        return res

    @staticmethod
    def calc_cos(var):
        a = var[0]
        print_ln('%s', var.reveal_list())
        length = a.total_size()
        res = sfix.Array(length)

        @for_range(length)
        def _(i):
            res[i] = cos(a[i])
        return res

    @staticmethod
    def calc_tan(var):
        a = var[0]
        print_ln('%s', var.reveal_list())
        length = a.total_size()
        res = sfix.Array(length)

        @for_range(length)
        def _(i):
            res[i] = tan(a[i])
        return res

    @staticmethod
    def calc_tanh(var):
        a = var[0]
        print_ln('%s', var.reveal_list())
        length = a.total_size()
        res = sfix.Array(length)

        @for_range(length)
        def _(i):
            res[i] = tanh(a[i])
        return res

    @staticmethod
    def calc_sqrt(var):
        ary = sfix.Array(var.total_size())

        @for_range(ary.total_size())
        def _(i):
            ary[i] = sqrt(var[0][i])
        return ary

    @staticmethod
    def calc_log2(var):
        ary = sfix.Array(var.total_size())

        @for_range(ary.total_size())
        def _(i):
            ary[i] = log2_fx(var[0][i])
        return ary

    @staticmethod
    def ml_softmax(var):
        res = ml.softmax(var[0])
        return res

    @staticmethod
    def comp_gt(var):
        if var[0].total_size() != var[1].total_size():
            raise ValueError('TWO ARRAY INVOLVED DO NOT SHARE THE SAME LENGTH')
        ary = sfix.Array(var[0].total_size())

        @for_range(ary.total_size())
        def _(i):
            ary[i] = var[0][i] > var[1][i]

        return ary

    @staticmethod
    def comp_ge(var):
        if var[0].total_size() != var[1].total_size():
            raise ValueError('TWO ARRAY INVOLVED DO NOT SHARE THE SAME LENGTH')
        ary = sfix.Array(var[0].total_size())

        @for_range(ary.total_size())
        def _(i):
            ary[i] = var[0][i] >= var[1][i]

        return ary

    @staticmethod
    def comp_lt(var):
        if var[0].total_size() != var[1].total_size():
            raise ValueError('TWO ARRAY INVOLVED DO NOT SHARE THE SAME LENGTH')
        ary = sfix.Array(var[0].total_size())

        @for_range(ary.total_size())
        def _(i):
            ary[i] = var[0][i] < var[1][i]

        return ary

    @staticmethod
    def comp_le(var):
        if var[0].total_size() != var[1].total_size():
            raise ValueError('TWO ARRAY INVOLVED DO NOT SHARE THE SAME LENGTH')
        ary = sfix.Array(var[0].total_size())

        @for_range(ary.total_size())
        def _(i):
            ary[i] = var[0][i] <= var[1][i]

        return ary

    @staticmethod
    def comp_eq(var):
        if var[0].total_size() != var[1].total_size():
            raise ValueError('TWO ARRAY INVOLVED DO NOT SHARE THE SAME LENGTH')
        ary = sfix.Array(var[0].total_size())

        @for_range(ary.total_size())
        def _(i):
            ary[i] = var[0][i] == var[1][i]

        return ary

    @staticmethod
    def calc_svc(var,meta):
        res = svc(var, meta)
        return res



# def get_parameter(api_json=None):
#     with open("func.json") as f:
#         result = js.load(f)
#     return result


# import json as js
# def get_parameter(api_json=None):
#     with open("C:/Users/Genghua_Dong/Desktop/work/21_11_07-SCALE-MAMBA开发/MPC/mp-spdz-0.2.8/compute.json") as f:
#         result = js.load(f)
#     return result


# para_js = get_parameter()
# df = DynamicVariables(para_js)
# df.input_analysis()
