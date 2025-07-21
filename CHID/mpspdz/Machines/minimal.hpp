/*
 * minimal.hpp
 *
 */

// minimal header file to make all C++ code compile
// but not produce all templated code in binary
// use maximal.hpp for that

// please report if otherwise

#ifndef MACHINES_MINIMAL_HPP_
#define MACHINES_MINIMAL_HPP_

#include "h-files.h"

// some h files depend on hpp files

#include "GC/Secret.hpp"
#include "GC/SemiSecret.hpp"
#include "Protocols/DealerMC.hpp"
#include "Protocols/MAC_Check.hpp"
#include "Protocols/MaliciousRepMC.hpp"
#include "Protocols/ShamirMC.hpp"

#endif /* MACHINES_MINIMAL_HPP_ */
