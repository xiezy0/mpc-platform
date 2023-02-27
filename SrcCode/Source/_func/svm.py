import sys, os
sys.path.append(os.curdir)
from Compiler.program import Program, defaults
opts = defaults()
opts.ring = 128
prog = Program(['svm'], opts)
#------------------------------above is compilation code----------------------------------------------------------------
from Compiler.library import *
from Compiler.mpc_math import *


def svc(data, meta):
    meta_params = list(meta.keys())
    if "regression" not in meta_params:
        raise ValueError("'meta parameters' does not contain 'regression'")
    if "epochs" not in meta_params:
        raise ValueError("'meta parameters' does not contain 'epochs'")
    reg_para = meta.get("regression", None)
    if reg_para is None:
        reg_para = 0.01 
        print(
            '\n using default regression parameter: {}'.format(reg_para)
        )
        reg_para = sfix(0.01)
    epochs = meta.get("epochs",None)
    if epochs is None:
        epochs = 100
        print(
            '\n using default training epochs: {}'.format(epochs)
        )

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
            # print_ln('%s', xi.reveal_nested())
            # tmp = w.get_part(epoch, 1)
            # print_ln('w, %s',tmp.reveal_nested())
            # print_ln('xi, %s',xi.reveal_nested())

            criteria = yi*w.get_part(epoch, 1)[0]*xi
            flag = sfix.Tensor([1, 1])
            flag.assign(criteria[0][0] < sfix(1))
            a = (E-lr)*w.get_part(epoch, 1)[0] + lr*lmdt*xi.direct_mul_to_matrix(yi).transpose()
            b = (E-lr)*w.get_part(epoch, 1)[0]
            res = flag*(a-b)+b
            @for_range(d_train)
            def _(i):
                w[epoch + 1][0][i] = res[0][i]
            print_ln('epoch, %s', epoch)
        last_index = epochs

        return w[last_index]
    data = data.transpose()


    print_ln('%s', data.reveal_nested())
    n_input = data.sizes[1]
    n_train = data.sizes[0]
    d_train = n_input - 1
    datat = data.transpose()
    print('datat',datat)
    Xtrt = datat.get_part(0, d_train)
    Ytrt = datat.get_part(d_train, 1)
    print(Xtrt)
    Xtr = Xtrt.transpose()
    Ytr = Ytrt.transpose()
    print_ln('%s', Xtr.reveal_nested())
    #ttl_x = n_train*d_train
    #Xtr = data.get_part(0, d_train)
    #Ytr = data.get_part(d_train, 1)
    #minibatch = sfix.Array(ttl_x)
    #@for_range(d_train)
    #def _(i):
    #    head = n_train*i
    #    feature = Xtr.get_part(i, 1)
    #    minibatch.assign_part_vector(feature, head)
#
#    Xtrt = sfix.Tensor([n_train, d_train])
#    @for_range(n_train)
#    def _(i):
#        ledge = d_train*i
#        batch = minibatch.get_part(ledge, d_train)
#        @for_range(d_train)
#        def _(j):
#            Xtrt[i][j] = batch[j]
    print('xtr', Xtr)
    #Ytrt = Ytr.transpose()
    print('ytr', Ytr)
    sgd_flag = 1
    if sgd_flag == 1:
        w_sgd = svm_sgd(Xtr, Ytr, n_train, d_train, reg_para, epochs)
        print_ln('final w is: %s ', w_sgd.reveal_nested())
        # print_ln_to(0, 'final w is: %s ', w_sgd.reveal_nested())
        # print_ln_to(1, 'final w is: %s ', w_sgd.reveal_nested())
        return w_sgd
    else:
        w_gd = svm_gd(Xtr, Ytr, n_train, d_train, reg_para, epochs)
        print_ln('final w is: %s ', w_gd.reveal_nested())
        # print_ln_to(0, 'final w is: %s ', w_gd.reveal_nested())
        # print_ln_to(1, 'final w is: %s ', w_gd.reveal_nested())
        return w_gd


# prog.finalize()


# import subprocess
# prog_name = 'svm'
# subprocess.run('Scripts/semi2k.sh svm'.split(' '))

#----This concludes the online phase of MP-SPDZ----

