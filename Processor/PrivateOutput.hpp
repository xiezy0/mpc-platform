/*
 * PrivateOutput.cpp
 *
 */

#include "PrivateOutput.h"
#include "Processor.h"

template<class T>
PrivateOutput<T>::PrivateOutput(SubProcessor<T>& proc) :
        proc(proc), MC(proc.MC.get_alphai())
{
    cout << "private output initial" << endl;
    MC.init_open(proc.P);
    MC.set_prep(proc.DataF);
}

template<class T>
PrivateOutput<T>::~PrivateOutput()
{
    MC.Check(proc.P);
}

template<class T>
void PrivateOutput<T>::prepare_sending(const T& source, int player)
{
    assert (player < proc.P.num_players());
    open_type mask;
    T res;
    proc.DataF.get_input(res, mask, player);
    res += source;

    cout << "open mask get: " << mask << endl;
    cout << "open res get:" << source << endl;
    if (player == proc.P.my_num())
        masks.push_back(mask);

    MC.prepare_open(res);
}

template<class T>
void PrivateOutput<T>::exchange()
{
    cout << "go to exchange" << endl;
    MC.exchange(proc.P);
}

template<class T>
typename T::clear PrivateOutput<T>::finalize(int player)
{
    cout << "finalize phase" << endl;
    auto res = MC.finalize_open();

    if (player == proc.P.my_num())
    {
        res -= masks.front();
        masks.pop_front();
    }

    return res;
}
