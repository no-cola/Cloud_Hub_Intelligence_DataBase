#include "SPDZ.hpp"

#include "Protocols/MascotPrep.hpp"
#include "Processor/FieldMachine.hpp"
#include "Math/gfp.hpp"

template class FieldMachine<Share, Share, DishonestMajorityMachine>;

template class Machine<Share<gfp_<0, 2>>, Share<gf2n>>;
