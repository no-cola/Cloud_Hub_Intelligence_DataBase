.. default-domain:: cpp


Navigating the C++ Code
=======================

In this section, we will explain how the most important aspects of the
C++ codebase fit together and explain them with brief examples.

MP-SPDZ heavily relies on templates (also called generic
programming). This is to achieve high efficiency while retaining
modularity as many MPC building blocks work in a number of contexts. A
notable example of this is `Beaver multiplication
<https://link.springer.com/chapter/10.1007/3-540-46766-1_34>`_. The
same code is used in more than 20 contexts without loss of efficiency.
See `this introduction
<https://dev.to/pratikparvati/introduction-to-c-templates-3d2e>`_ if
you're new to C++ templates.

Due to the size of the codebase (more than 100,000 lines of code in
hundreds of files), we recommend using an integrated development
environment (IDE) to navigate it. `Eclipse
<https://www.eclipse.org/downloads>`_ has very useful features such as
jumping to the definition of function or variable using F3 or find all
references to a function or variable with Strg-Shift-g. The latter
doesn't work well with templates, however, so global text search is
necessary for a more comprehensive view.


Mathematical Domains
--------------------

All protocols in MP-SPDZ are based on finite domains for secret
sharing, most importantly integers modulo a number. While basic CPU
arithmetic and existing libraries provide all required functionality
(e.g., modern CPUs generally work with integers modulo :math:`2^{64}`
and the `GNU Multiple Precision Arithmetic Library
<https://gmplib.org>`_ has provisions for a plethora of integer
operations), we have found these to be inefficient in the context of
MPC. The main reason is that an MPC protocol uses the same modulus
throughout but the variable-length nature of GMP incurs a considerable
cost for every operation, which is not necessary. MP-SPDZ therefore
provides a tailored data type for every mathematical domain. These
data types use operator overloading for easy use. For example,

.. code-block::

  cout << (Z2<5>(20) + Z2<5>(30)) << endl;

should output::

  18

because ``Z2<5>`` represents computation modulo :math:`2^5=32`. See
the reference of :cpp:class:`Z2` and :cpp:class:`SignedZ2` for further
details.

For computation modulo a prime on the other hand, the data type fixes
only a range at compile time, so the exact modulus has be given before
usage::

  gfp_<0; 1>::init_field(13);
  cout << (gfp_<0, 1>(8) + gfp_<0, 1>(7)) << endl;

should output::

  2

The first parameter to :cpp:class:`gfp_` is a counter that allows
several moduli to be used at once, for example::

  gfp_<0, 1>::init_field(13);
  gfp_<1, 1>::init_field(17);

The second parameter denotes the number of 64-bit limbs, that is, it
should be 1 for primes in :math:`[0,2^{64}]`, 2 for prime in
:math:`[2^{64},2^{128}]` etc.

In addition to the fixed domains, :cpp:class:`bigint` is a sub-class
of :cpp:class:`mpz_class` `type in GMP
<https://gmplib.org/manual/C_002b_002b-Interface-Integers>`_. It used
for conversions amongst other things.


Communication
-------------

MP-SPDZ provides a communication interface that is more involved than
sending bytes via a socket. There are two reasons for doing
this. First, the structure of MPC goes far beyond the query-reply
pattern often found in online communication. For example, two parties
might need to exchange a large quantity of information
simultaneously. Second, the atomic quantity communicated in MPC (i.e.,
the numbers) are usually so small that it is preferential to send them
in batches. The following example demonstrates the exchange of a
vector of 64-bit numbers in the two-party setting::

  Player& P = ...;
  vector<Z2<64>> numbers;
  // populate vector
  ...
  octetStream os;
  os.store(numbers);
  P.pass_around(1, os);
  os.get(numbers);
  // numbers now contains the ones from the other side

No matter how many numbers there are, the framework makes sure to send
and receive them at the same time. The number given to
:cpp:func:`Player::pass_around` denotes an offset, that is, the
numbers are sent to "next" party and received from the "previous" one
(regarding player number with wrap-around). See :ref:`this section
<network-reference>` for more details.


Randomness
----------

Randomness is a crucial component of MPC (as for cryptography in
general). Random number generation in MP-SPDZ centers on the
:cpp:class:`PRNG` class. It implements optimized random number
generation based on hardware AES if available. This allows for local
as well as coordinated randomness generation. An exampled for the
first is as follows::

  SeededPRNG G;
  auto res = G.get<Z2<64>>();

This initializes the PRNG with secure randomness from libsodium and
then generates a random 64-bit element.

On the other hand, the following initializes a global PRNG securely,
that is, with a seed that cannot be influenced by any party, before
generating a random element modulo a prime::

  // initialize at some point
  gfp_<0, 1>::init_field(prime);
  Player& P = ...;
  ...
  GlobalPRNG G(P);
  auto res = G.get<gfp_<0, 1>>();


Protocols
---------

The implementation of protocols is centered on the share types. They
not only hold all values necessary to represent a secret value for one
party, they also provide local operations, refer to other classes
implementing protocols, and contain variables and static functions to
describes protocols.

As an example, consider :cpp:class:`Rep3Share\<T>` in
:download:`../Protocols/Rep3Share.h`. It implements a share for
three-party replicated secret sharing. It takes one template parameter
for the mathematical domain because the secret sharing and the
multiplication protocol work for any finite domain. The following
typedef makes the cleartext domain generally accessible::

  typedef T clear;

Further typedefs are used to indicate which class to use for inputs,
multiplications, and outputs::

  typedef ReplicatedInput<Rep3Share> Input;
  typedef Replicated<Rep3Share> Protocol;
  typedef ReplicatedMC<Rep3Share> MAC_Check;

The latter usually contains the name MAC_Check or MC because MAC
checking is a core function of the output protocol in SPDZ.

These typedefs follow the general pattern that the *share type* is a
template argument to the *protocol type*. This makes everything
contained defined by the share type accessible to the protocol
type. As an example of this, :cpp:class:`ReplicatedMC\<Rep3Share>` is
a sub-class of :cpp:class:`MAC_Check_Base\<Rep3Share>`, which
implements the general interface for opening shares. On the functions
there is defined as follows::

  virtual typename T::clear finalize_open();

Another important typedef in :cpp:class:`Rep3Share` is the
preprocessing type::

  typedef typename conditional<T::characteristic_two,
          ReplicatedPrep<Rep3Share>, SemiRep3Prep<Rep3Share>>::type LivePrep;

It is more complicated because it uses meta-programming to assign
different types depending on whether mathematical domain has
characteristic two (i.e., it's :math:`\mathrm{GF}(2^n)`). This is to
avoid compiling code for a specific daBit generation that doesn't make
sense in said domain. The preprocessing classes use polymorphism to
mix and match the possible protocols. For example,
:cpp:func:`BitPrep<T>::buffer_squares` to implements a generic
protocol to generate square tuples from multiplication triples, but
this isn't the most efficient way with replicated secret sharing,
which is why :cpp:func:`ReplicatedRingPrep<T>::buffer_squares`
overrides this with a more specific protocol in our example.

The four protocol types above are contained in an instance
:cpp:class:`ProtocolSet\<T>` as documented in :ref:`low-level` where
:py:class:`T` is a share type.

:cpp:class:`Rep3Share\<T>` is a sub-class of
:cpp:class:`FixedVec\<T,2>`. The latter contains a pair of values in the
cleartext domain as one would expect with this kind of secret sharing,
and it implements element-wise addition, subtraction, and
multiplication via operator overloading, which makes it
straight-forward to run local operations with share types.

Lastly, :cpp:class:`Rep3Share` defines a few variables that describe
the protocols, for example::

  const static bool dishonest_majority = false;
  const static bool variable_players = false;

These indicate that replicated secret sharing requires and honest
majority and fixed number of players. First is used to the set default
number of parties and the second to decide whether to offer the
``--nparties`` command-line option.


Virtual Machines
----------------

The main function for the protocol-specific virtual machines is
defined in the file of the appropriate name in the ``Machines``
directory. For example, the virtual machine for three-party replicated
secret sharing over prime fields is defined in
:download:`../Machines/replicated-field-party.cpp`, and the main function
looks as follows::

  int main(int argc, const char** argv)
  {
      HonestMajorityFieldMachine<Rep3Share>(argc, argv);
  }

Indirectly, this calls an instance of :cpp:class:`Machine\<sint,
sgf2n>` where :cpp:class:`sint` and :cpp:class:`sgf2n` denote the
complete share type for integer and :math:`\mathrm{GF}(2^n)`,
respectively. The defaults are :cpp:class:`Rep3Share\<gfp_\<0, 2>>` and
:cpp:class:`Rep3Share\<gf2n_long>` in the example. To choose that,
the constructor of :cpp:class:`FieldMachine` (in
:download:`../Processor/FieldMachine.hpp`) contains code to the length
for :cpp:class:`gfp_` (the second parameter, the first is always
0). For protocols modulo a power of two other than SPDZ2k, this
happens in the constructor of :cpp:class:`RingMachine` or
:cpp:class:`HonestMajorityRingMachineWithSecurity` in
:download:`../Processor/RingMachine.hpp`. The purpose of all this is
to fix the mathematical domains throughout for maximum performance.

The includes are structured in a way that all relevant templated code
is included in these files, so compiling it makes sure that the object
file contains most protocol-specific code. The main exceptions from
this are code related to homomorphic encryption (in ``libFHE.so``),
oblivious transfer (included via object files), and Tinier (in
``Machines/Tinier.o``). Furthermore, all general code is put in
``libSPDZ.so``. All this is to reduce the compilation time and/or the
binary size.
