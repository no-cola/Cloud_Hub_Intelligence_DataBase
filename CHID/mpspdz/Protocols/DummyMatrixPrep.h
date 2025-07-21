/*
 * DummyMatrixPrep.h
 *
 */

#ifndef PROTOCOLS_DUMMYMATRIXPREP_H_
#define PROTOCOLS_DUMMYMATRIXPREP_H_

#include "Processor/Data_Files.h"
#include "ShareMatrix.h"

class no_matrix_prep : public exception
{
};

template<class T>
class DummyMatrixPrep : public Preprocessing<ShareMatrix<T>>
{
public:
    DummyMatrixPrep(int, int, int, Preprocessing<T>&, DataPositions& usage) :
            Preprocessing<ShareMatrix<T>>(usage)
    {
        throw no_matrix_prep();
    }
};

#endif /* PROTOCOLS_DUMMYMATRIXPREP_H_ */
