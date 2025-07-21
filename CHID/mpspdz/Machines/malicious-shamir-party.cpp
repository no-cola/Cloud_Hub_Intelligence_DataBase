/*
 * malicious-shamir-party.cpp
 *
 */

#include "Protocols/MaliciousShamirShare.h"
#include "Protocols/ShamirOptions.h"
#include "Machines/MalRep.hpp"

#include "Shamir.hpp"

int main(int argc, const char** argv)
{
    ShamirMachineSpec<MaliciousShamirShare>(argc, argv);
}
