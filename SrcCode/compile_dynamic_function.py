#!/usr/bin/env python3
import sys
import os
from Compiler.library import *
from SrcCode.Source.dynamic_function import DynamicVariables
from Compiler.program import Program, defaults
import json as js
import subprocess
import argparse



def mpc_compile(meta_js):
    opts = defaults()
    # Set the finite ring parameter gfr(2^128), namely increase more numbers.
    opts.ring = 128
    program_name = meta_js["name"]
    prog = Program([program_name], opts)
    # Literally set precision but with unconfirmed result
    sfix.set_precision(16,32)
    print_float_precision(10)
    config_cpt = meta_js["CptConfig"]
    dv = DynamicVariables(config_cpt)
    res = dv.eval_formula()
    dv.print_res()
    prog.finalize()
    msg = "compilation success"
    return msg
