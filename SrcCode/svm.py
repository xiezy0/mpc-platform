#!/usr/bin/env python3
# 具体协议与编译文件的关系，是否是静态的还是动态相关的。
import sys, os
sys.path.append(os.curdir)
from Compiler.program import Program, defaults
opts = defaults()
opts.ring = 128
prog = Program(['svm'], opts)
#------------------------------above is compilation code----------------------------------------------------------------
from Compiler.types import sint
from Compiler import mpc_math, util
from Compiler.types import *
from Compiler.types import _unreduced_squant
from Compiler.library import *
from Compiler.mpc_math import *

# you can assign public numbers to sint
# program.use_edabit(True)

from Compiler.mpc_math import sqrt
# precision = 32
# sfix.set_precision(16,precision)
# print_float_precision(20)


def svm_sgd(x, y, n_train, d_train, lmd, epochs):
    """
    x: input private data including all features
    y: input private data including all labels
    lmd: public data as lambda in svm
    epochs: public data
    """

    w_length = epochs + 1
    w = sfix.Tensor([w_length, 1, d_train])
    lmdt = sfix.Tensor([1, 1])
    lmdt.assign_all(lmd)
    E = sfix.Tensor([1, 1])
    E_value = sfix([1])
    E.assign(E_value)

    @for_range(epochs)
    def _(epoch):
        lr_up = sfix(1)
        lr_btm = sfix(epoch)+sfix(1)
        lr_value = lr_up/lr_btm
        lr = sfix.Tensor([1, 1])
        lr.assign_all(lr_value)
        i = trunc(sfix.get_random(0, n_train, size=1)).reveal()
        yi = y.get_part(i, 1)
        # get_vector ensures getting the multi_vector type and it can only extract the rows.
        xi = x.get_part(i, 1).transpose()
        # tmp = w.get_part(epoch, 1)
        # print_ln('w, %s',tmp.reveal_nested())
        # print_ln('xi, %s',xi.reveal_nested())

        criteria = yi*w.get_part(epoch, 1)[0]*xi
        flag = sfix.Tensor([1, 1])
        flag.assign(criteria[0][0] < sfix(1))
        a = (E-lr)*w.get_part(epoch, 1)[0] + lr*lmdt*xi.direct_mul_to_matrix(yi).transpose()
        b = (E-lr)*w.get_part(epoch, 1)[0]
        res = flag*(a-b)+b
        w[epoch+1][0][0] = res[0][0]
        w[epoch+1][0][1] = res[0][1]
        w[epoch+1][0][2] = res[0][2]
        w[epoch+1][0][3] = res[0][3]
        w[epoch+1][0][4] = res[0][4]
        print_ln('epoch, %s', epoch)

    return w


def svm_gd(x, y, n_train, d_train, lmd, epochs):
    """
    x: input private data including all features
    y: input private data including all labels
    lmd: secret data as lambda in svm
    epochs: public data
    """
    w_length = epochs*n_train+1
    w = sfix.Tensor([w_length, 1, d_train])
    lmdt = sfix.Tensor([1, 1])
    lmdt.assign_all(lmd)
    E = sfix.Tensor([1, 1])
    E_value = sfix([1])
    E.assign(E_value)

    @for_range(epochs)
    def _(epoch):
        lr_up = sfix(1)
        lr_btm = sfix(epoch)+sfix(1)
        lr_value = lr_up/lr_btm
        lr = sfix.Tensor([1, 1])
        lr.assign_all(lr_value)

        @for_range(n_train)
        def _(i):
            w_index = n_train*epoch+i
            yi = y.get_part(i, 1)
            # get_vector ensures getting the multi_vector type and it can only extract the rows.
            xi = x.get_part(i, 1).transpose()
            criteria = yi*w.get_part(w_index, 1)[0]*xi
            flag = sfix.Tensor([1, 1])
            flag_value = criteria[0][0] < sfix(1)
            flag.assign(flag_value)
            a = (E - lr)*w.get_part(w_index, 1)[0] + lr*lmdt*xi.direct_mul_to_matrix(yi).transpose()
            b = (E - lr)*w.get_part(w_index, 1)[0]
            res = flag*(a-b)+b
            w[w_index+1][0][0] = res[0][0]
            w[w_index+1][0][1] = res[0][1]
            w[w_index+1][0][2] = res[0][2]
            w[w_index+1][0][3] = res[0][3]
            w[w_index+1][0][4] = res[0][4]
        print_ln('epoch, %s', epoch)
        tmp_index = n_train*epoch
        #print_ln('res, %s', w[tmp_index].reveal_nested())
    last_index = n_train * epochs
    return w[last_index]


n_train = 420
d_train = 5
reg_para = sfix(0.01)
epochs = 1700
Xtr = sfix.Tensor([n_train, d_train])
Ytr = sfix.Tensor([n_train,1])
Xtr.input_from(0)
Ytr.input_from(1)

sgd_flag = 1
if sgd_flag == 1:
    w_sgd = svm_sgd(Xtr, Ytr, n_train, d_train, reg_para, epochs)
    print_ln('final w is: %s ', w_sgd.reveal_nested())
    print_ln_to(0, 'final w is: %s ', w_sgd.reveal_nested())
    print_ln_to(1, 'final w is: %s ', w_sgd.reveal_nested())
else:
    w_gd = svm_gd(Xtr, Ytr, n_train, d_train, reg_para, epochs)
    print_ln('final w is: %s ', w_gd.reveal_nested())
    print_ln_to(0, 'final w is: %s ', w_gd.reveal_nested())
    print_ln_to(1, 'final w is: %s ', w_gd.reveal_nested())


prog.finalize()


import subprocess
prog_name = 'svm'
subprocess.run('Scripts/semi2k.sh svm'.split(' '))

#----This concludes the online phase of MP-SPDZ----

