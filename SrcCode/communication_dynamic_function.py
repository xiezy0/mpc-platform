#!/usr/bin/env python3
import sys
import os
from Compiler.library import *
from SrcCode.Source.dynamic_function import DynamicVariables
from Compiler.program import Program, defaults
import json as js
import subprocess
import argparse



def mpc_communication(meta_js):
    program_name = meta_js["name"]
    config_mpc = meta_js["MpcConfig"]
    config_ip = meta_js["IpConfig"]
    n_p = config_mpc.get("party_amount",3)
    sim_flag = config_mpc.get("simulation",0)
    p = config_mpc.get("party_index",1)
    protocol = config_mpc.get("protocol","semi2k")
    pn = config_ip.get("port_number","6000")
    if sim_flag == 0:
        command = './%s-party.x ' \
                '-N %d -p %d ' \
                '-IF Player-Data/Input -OF Player-Data/Public-Output ' \
                '--ip-file-name ConfigFiles/IPConfig_%dp ' \
                '-pn %d '%(protocol, n_p, p, n_p, pn) \
                + program_name
        subprocess.run(command.split(' '))
    else:
        command = 'Scripts/%s.sh'%protocol + ' ' + program_name
        subprocess.run(command.split(' '))
    msg = "communictaion finished"
    return msg
