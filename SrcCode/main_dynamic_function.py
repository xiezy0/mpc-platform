#!/usr/bin/env python3
from Compiler.library import *
from SrcCode.Source.dynamic_function import DynamicVariables
from Compiler.program import Program, defaults
import subprocess


def start_mpc(meta_js, taskId):
    opts = defaults()
    # Set the finite ring parameter gfr(2^128), namely increase more numbers.
    opts.ring = 128
    program_name = 'dynamic_function'
    prog = Program([program_name], opts)
    # Literally set precision but with unconfirmed result
    sfix.set_precision(16, 32)
    print_float_precision(10)
    config_mpc = meta_js["MpcConfig"]
    config_ip = meta_js["IpConfig"]
    config_cpt = meta_js["CptConfig"]
    n_p = config_mpc.get("party_amount", 3)
    sim_flag = config_mpc.get("simulation", 0)
    p = config_mpc.get("party_index", 1)
    protocol = config_mpc.get("protocol", "semi2k")
    pn = config_ip.get("port_number", "6000")
    dv = DynamicVariables(config_cpt, taskId)
    dv.eval_formula()
    dv.print_res()
    prog.finalize()
    if sim_flag == 0:
        command = './%s-party.x ' \
                  '-N %d -p %d ' \
                  '-IF Player-Data/Input -OF Player-Data/Public-Output ' \
                  '--ip-file-name ConfigFiles/IPConfig_%dp -e ' \
                  '-pn %d ' % (protocol, n_p, p, n_p, pn) \
                  + program_name
        print(command)
        subprocess.run(command.split(' '))
    else:
        command = 'Scripts/%s.sh' % protocol + ' ' + program_name
        subprocess.run(command.split(' '))
    return 0
