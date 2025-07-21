/*
 * TruncPrTuple.cpp
 *
 */

#include "TruncPrTuple.h"

void trunc_pr_check(int k, int m, int n_bits)
{
    if (not (m < k and 0 < m and k <= n_bits))
    {
        stringstream ss;
        ss << "invalid trunc_pr parameters, need 0 < m=" << m << " < k=" << k
                << " <= n_bits=" << n_bits;
        throw Processor_Error(ss.str());
    }
}
