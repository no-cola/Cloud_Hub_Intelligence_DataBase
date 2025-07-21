/*
 * shamir-party.cpp
 *
 */

#include "Protocols/ShamirOptions.h"
#include "Protocols/ShamirShare.h"

#include "Shamir.hpp"

int main(int argc, const char** argv)
{
    ShamirMachineSpec<ShamirShare>(argc, argv);
}
