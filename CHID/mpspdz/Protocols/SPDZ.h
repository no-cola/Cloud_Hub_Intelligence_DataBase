/*
 * Multiplication.h
 *
 */

#ifndef PROTOCOLS_SPDZ_H_
#define PROTOCOLS_SPDZ_H_

#include "Hemi.h"
#include "SemiShare.h"

#include <vector>
using namespace std;

template<class T> class SubProcessor;
template<class T> class Share;
class Player;

/**
 * SPDZ protocol
 */
template <class T>
class SPDZ : public MaybeHemi<T>
{
public:
    SPDZ(Player& P) : MaybeHemi<T>(P)
    {
    }

    int get_n_relevant_players()
    {
        return this->P.num_players();
    }
};

#endif /* PROTOCOLS_SPDZ_H_ */
