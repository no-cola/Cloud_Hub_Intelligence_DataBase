/*
 * ShamirMachine.cpp
 *
 */

#ifndef MACHINE_SHAMIR_HPP_
#define MACHINE_SHAMIR_HPP_

#include "Protocols/ShamirOptions.h"
#include "Protocols/ShamirShare.h"
#include "Protocols/MaliciousShamirShare.h"
#include "Math/gfp.h"
#include "Math/gf2n.h"
#include "GC/VectorProtocol.h"
#include "GC/CcdPrep.h"
#include "GC/TinyMC.h"
#include "GC/MaliciousCcdSecret.h"
#include "GC/VectorInput.h"

#include "Processor/FieldMachine.hpp"

#include "Processor/Data_Files.hpp"
#include "Processor/Instruction.hpp"
#include "Processor/Machine.hpp"
#include "Protocols/ShamirInput.hpp"
#include "Protocols/Shamir.hpp"
#include "Protocols/ShamirMC.hpp"
#include "Protocols/MaliciousShamirMC.hpp"
#include "Protocols/MaliciousShamirPO.hpp"
#include "Protocols/MAC_Check_Base.hpp"
#include "Protocols/Beaver.hpp"
#include "Protocols/Spdz2kPrep.hpp"
#include "Protocols/ReplicatedPrep.hpp"
#include "Protocols/MalRepRingPrep.hpp"
#include "GC/ShareSecret.hpp"
#include "GC/VectorProtocol.hpp"
#include "GC/Secret.hpp"
#include "GC/CcdPrep.hpp"
#include "Math/gfp.hpp"

template<template<class U> class T>
ShamirMachineSpec<T>::ShamirMachineSpec(int argc, const char** argv)
{
    auto& opts = ShamirOptions::singleton;
    ez::ezOptionParser opt;
    opts = {opt, argc, argv};
    HonestMajorityFieldMachine<T>(argc, argv, opt, opts.nparties);
}

#endif
