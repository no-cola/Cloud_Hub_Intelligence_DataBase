/*
 * Opener.h
 *
 */

#ifndef PROTOCOLS_OPENER_H_
#define PROTOCOLS_OPENER_H_

#include <type_traits>

template<class T>
class Opener
{
    typedef typename conditional<is_same<typename T::DefaultMC, void>::value,
            typename T::MAC_Check, typename T::DefaultMC>::type inner_type;

    inner_type inner;
    Player& P;

public:
    Opener(Player& P, typename T::mac_key_type mac_key) :
            inner(mac_key), P(P)
    {
    }

    ~Opener()
    {
        Check();
    }

    void Check()
    {
        inner.Check(P);
    }

    void init_open(int n = 0)
    {
        inner.init_open(P, n);
    }

    void prepare_open(const T& secret)
    {
        inner.prepare_open(secret);
    }

    void exchange()
    {
        inner.exchange(P);
    }

    typename T::clear finalize_open()
    {
        return inner.finalize_open();
    }
};

#endif /* PROTOCOLS_OPENER_H_ */
