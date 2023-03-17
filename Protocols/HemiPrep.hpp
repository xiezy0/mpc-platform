/*
 * HemiPrep.hpp
 *
 */

#ifndef PROTOCOLS_HEMIPREP_HPP_
#define PROTOCOLS_HEMIPREP_HPP_

#include "HemiPrep.h"
#include "FHEOffline/PairwiseMachine.h"
#include "Tools/Bundle.h"

template<class T>
PairwiseMachine* HemiPrep<T>::pairwise_machine = 0;

template<class T>
Lock HemiPrep<T>::lock;

template<class T>
void HemiPrep<T>::teardown()
{
    if (pairwise_machine)
        delete pairwise_machine;
}

template<class T>
void HemiPrep<T>::basic_setup(Player& P)
{
    assert(pairwise_machine == 0);
    pairwise_machine = new PairwiseMachine(P);
    auto& machine = *pairwise_machine;
    auto& setup = machine.setup<FD>();
    setup.params.set_matrix_dim_from_options();
    setup.params.set_sec(OnlineOptions::singleton.security_parameter);
    setup.secure_init(P, machine, T::clear::length(), 0);
    T::clear::template init<typename FD::T>();
}

template<class T>
const FHE_PK& HemiPrep<T>::get_pk()
{
    assert(pairwise_machine);
    return pairwise_machine->pk;
}

template<class T>
const typename T::clear::FD& HemiPrep<T>::get_FTD()
{
    assert(pairwise_machine);
    return pairwise_machine->setup<FD>().FieldD;
}


template<class T>
HemiPrep<T>::~HemiPrep()
{
    for (auto& x : multipliers)
        delete x;

    if (two_party_prep)
    {
        auto& usage = two_party_prep->usage;
        delete two_party_prep;
        delete &usage;
    }
}

template<class T>
vector<Multiplier<typename T::clear::FD>*>& HemiPrep<T>::get_multipliers()
{
    assert(this->proc != 0);
    auto& P = this->proc->P;

    lock.lock();
    if (pairwise_machine == 0 or pairwise_machine->enc_alphas.empty())
    {
        PlainPlayer P(this->proc->P.N, "Hemi" + T::type_string());
        if (pairwise_machine == 0)
            basic_setup(P);
        pairwise_machine->setup<FD>().covert_key_generation(P,
                *pairwise_machine, 1);
        pairwise_machine->enc_alphas.resize(1, pairwise_machine->pk);
    }
    lock.unlock();

    if (multipliers.empty())
        for (int i = 1; i < P.num_players(); i++)
            multipliers.push_back(
                    new Multiplier<FD>(i, *pairwise_machine, P, timers));
    return multipliers;
}

template<class T>
void HemiPrep<T>::buffer_triples()
{
    assert(this->proc != 0);
    auto& P = this->proc->P;
    auto& multipliers = get_multipliers();
    auto& FieldD = pairwise_machine->setup<FD>().FieldD;
    Plaintext_<FD> a(FieldD), b(FieldD), c(FieldD);
    a.randomize(G);
    b.randomize(G);
    c.mul(a, b);
    Bundle<octetStream> bundle(P);
    Ciphertext sendvalue = pairwise_machine->pk.encrypt(a);
    
    cout << "plaintext of ai: ";
    for (unsigned int i = 0; i <= a.num_slots(); i++)
    {
        cout << a.element(i) << ",";
    }
    cout << "" << endl;
    cout << "pk of Ciphtertext:" << endl;
    cout << "value pk(a, b)-a : ";
    for(int i = 0; i <= pairwise_machine->pk.a().n_mults(); i++)
    {
        for(int j = 0;j <= pairwise_machine->pk.a().get(i).n_mults(); j++)
        {
            for(int k = 0; k <= 2; k++)
            {
                cout << pairwise_machine->pk.a().get(i).get_element(j).get()[k] << ",";
            }
        }
    }
    cout << "" << endl;

    cout << "value pk(a, b)-b : ";
    for(int i = 0; i <= pairwise_machine->pk.b().n_mults(); i++)
    {
        for(int j = 0; j <= pairwise_machine->pk.b().get(i).n_mults(); j++)
        {
            for(int k = 0; k <= 2; k++)
            {
                cout << pairwise_machine->pk.b().get(i).get_element(j).get()[k] << ",";
            }
        }
    }
    cout << "" << endl;

    cout << "send Ciphertext Enc(ai) to each party" << endl;
    cout << "value ai-c0: ";
    for (int i = 0; i <= sendvalue.c0().n_mults(); i++)
    {
        for (int j = 0; j <= sendvalue.c0().get(i).n_mults(); j++)
        {
            for (int k = 0; k <= 2; k++)
            {
                cout << sendvalue.c0().get(i).get_element(j).get()[k] << ",";
            }
        }
    }
    cout << "" << endl;
    cout << "value ai-c1: ";
    for (int i = 0; i <= sendvalue.c1().n_mults(); i++)
    {
        for (int j = 0; j <= sendvalue.c1().get(i).n_mults(); j++)
        {
            for (int k = 0; k <= 2; k++)
            {
                cout << sendvalue.c1().get(i).get_element(j).get()[k] << ",";
            }
        }
    }
    cout << "" << endl;
    cout << "number of ai.c" << sendvalue.c0().n_mults() << endl;
    cout << "number of ai.c.ring" << sendvalue.c0().get(0).n_mults() << endl;

    sendvalue.pack(bundle.mine);
    P.unchecked_broadcast(bundle);
    Ciphertext C(pairwise_machine->pk);
    for (auto m : multipliers)
    {
        C.unpack(bundle[P.get_player(-m->get_offset())]);
        m->multiply_and_add(c, C, b);
    }
    assert(b.num_slots() == a.num_slots());
    assert(c.num_slots() == a.num_slots());
    for (unsigned i = 0; i < a.num_slots(); i++)
        this->triples.push_back(
        {{ a.element(i), b.element(i), c.element(i) }});
}

template<class T>
SemiPrep<T>& HemiPrep<T>::get_two_party_prep()
{
    assert(this->proc);
    assert(this->proc->P.num_players() == 2);

    if (not two_party_prep)
    {
        two_party_prep = new SemiPrep<T>(this->proc,
                *new DataPositions(this->proc->P.num_players()));
        two_party_prep->set_protocol(this->proc->protocol);
    }

    return *two_party_prep;
}

template<class T>
void HemiPrep<T>::buffer_bits()
{
    assert(this->proc);
    if (this->proc->P.num_players() == 2)
    {
        auto& prep = get_two_party_prep();
        prep.buffer_dabits(0);
        for (auto& x : prep.dabits)
            this->bits.push_back(x.first);
        prep.dabits.clear();
    }
    else
        SemiHonestRingPrep<T>::buffer_bits();
}

template<class T>
void HemiPrep<T>::buffer_dabits(ThreadQueues* queues)
{
    assert(this->proc);
    if (this->proc->P.num_players() == 2)
    {
        auto& prep = get_two_party_prep();
        prep.buffer_dabits(queues);
        this->dabits = prep.dabits;
        prep.dabits.clear();
    }
    else
        SemiHonestRingPrep<T>::buffer_dabits(queues);
}

#endif
