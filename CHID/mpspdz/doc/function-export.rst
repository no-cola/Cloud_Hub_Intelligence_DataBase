.. _function-export:

Using High-Level Functionality in C++
=====================================

The fact that most functionality is implemented on the high level (in
the compiler) but the virtual machine running high-level code is
somewhat limited makes it desirable to call high-level functionality
from C++. MP-SPDZ supports defining functions on the high level and
calling them from C++. Functions can have integer secrets
(:py:class:`~Compiler.types.sint`) and (multi-)arrays thereof as
inputs and return values as well as (multi-)arrays of binary secrets
(types created using :py:class:`~Compiler.GC.types.sbitvec` and
:py:class:`~Compiler.GC.types.sbitintvec`).

As a simple example, consider
:download:`../Programs/Source/export-sort.py` and
:download:`../Utils/export-sort.cpp`. The Python part looks as follows::

  @export
  def sort(x):
    print_ln('x=%s', x.reveal())
    res = x.sort()
    print_ln('res=%s', x.reveal())

  sort(sint.Array(1000))

This makes the sorting of integer arrays of length 1000 accessible to
C++. The corresponding C++ code starts similarly to the :ref:`low-level
code example <low-level>`:

.. code-block:: cpp

  #include "Machines/maximal.hpp"

  int main(int argc, const char** argv)
  {
    assert(argc > 1);
    int my_number = atoi(argv[1]);
    int port_base = 9999;
    Names N(my_number, 3, "localhost", port_base);

This includes all necessary headers and makes contact with the other
parties on the same machine. The next step is to set up an instance of
the virtual machine:

.. code-block:: cpp

    typedef Rep3Share2<64> share_type;
    Machine<share_type> machine(N);

In this example, we use replicated secret sharing modulo
:math:`2^{64}`. Next, we prepare the inputs:

.. code-block:: cpp

    int n = 1000;

    ProtocolSet<share_type> set(machine.get_player(), machine);
    set.input.reset(0);
    for (int i = 0; i < n; i++)
    {
        if (my_number == 0)
            set.input.add_mine(n - i);
        else
            set.input.add_other(0);
    }
    set.input.exchange();

    vector<share_type> inputs;
    for (int i = 0; i < n; i++)
        inputs.push_back(set.input.finalize(0));

This initializes a :cpp:class:`ProtocolSet` using the virtual machine
instead of a :cpp:class:`ProtocolSetup`. This is necessary to avoid
differing MAC keys and other setup variables. Then, party 0 inputs the
numbers 1 to 1000 in reverse other, and the resulting secret shares
are stored in :cpp:var:`inputs`. Now we're ready to call the
function:

.. code-block:: cpp

    vector<FunctionArgument> args = {{inputs, true}};
    FunctionArgument res;

    machine.run_function("sort", res, args);

This indicates that the function takes one argument, which is an array
(as opposed to a vector, see below) and that we don't expect a return
value. Lastly, we open and check the array:

.. code-block:: cpp

    Opener<share_type> MC(machine.get_player(), machine.get_sint_mac_key());
    MC.init_open();
    for (auto& x : inputs)
        MC.prepare_open(x);
    MC.exchange();

    if (my_number == 0)
    {
        cout << "res: ";
        for (int i = 0; i < 10; i++)
            cout << MC.finalize_open() << " ";
        cout << endl;
    }
    else
    {
        for (int i = 0; i < n; i++)
        {
            auto x = MC.finalize_open();
            if (x != i + 1)
            {
                cerr << "error at " << i << ": " << x << endl;
                exit(1);
            }
        }
    }

The :cpp:class:`Opener` class is convenience that is bound to a
communication instance (unlike :cpp:class:`MAC_Check_Base` instances,
which require the communication instance in several function calls).

You can run the example as follows:

.. code-block:: console

   ./compile.py -E ring export-sort
   make export-sort.x
   for i in 0 1 2; do ./export-sort.x $i & true; done

This makes sure that all the optimizations of the protocol are used.


Vector arguments and return values
----------------------------------

Instead of arrays, it is also possible to use
:py:class:`~Compiler.types.sint` vectors as demonstrated in
:download:`../Programs/Source/export-trunc.py`::

  @export
  def trunc_pr(x):
    print_ln('x=%s', x.reveal())
    res = x.round(32, 2)
    print_ln('res=%s', res.reveal())
    return res

  trunc_pr(sint(0, size=1000))

The calling C++ code in :download:`../Utils/export-trunc.cpp` looks as
follows:

.. code-block:: cpp

    int n = 1000;
    vector<share_type> inputs;
    for (int i = 0; i < n; i++)
        inputs.push_back(share_type::constant(i, my_number));

    vector<FunctionArgument> args = {inputs};
    vector<share_type> results(n);
    FunctionArgument res(results);

    machine.run_function("trunc_pr", res, args);

This creates integer shares using public constants instead of the
input protocol as above. The :cpp:class:`FunctionArgument` instance
for both input and output are created using the vector of secret
shares without the extra ``true`` argument.


Binary values
-------------

It is possible to input and output binary secrets with an
array. Consider :download:`../Programs/Source/export-b2a.py`, which
converts arithmetic to binary shares::

  @export
  def b2a(res, x):
    print_ln('x=%s', x.reveal())
    res[:] = sint(x[:])
    print_ln('res=%s', x.reveal())

  b2a(sint.Array(size=10), sbitvec.get_type(16).Array(10))

This demonstrates the requirement of using an array of an
:py:class:`sbitvec` type with a defined number of bits (16 in this
case). :py:class:`sbitintvec` is a sub-class and also permissible.

The C++ calling code looks as follows:

.. code-block:: cpp

    int n = 10;
    vector<share_type> outputs(n);
    vector<vector<share_type::bit_type>> inputs(n);

    auto& inputter = set.binary.input;
    inputter.reset(0);
    for (int i = 0; i < n; i++)
        if (my_number == 0)
            inputter.add_mine(i + 1, 16);
        else
            inputter.add_other(0);
    inputter.exchange();
    for (int i = 0; i < n; i++)
        inputs.at(i).push_back(inputter.finalize(0, 16));

    vector<FunctionArgument> args = {{outputs, true}, {16, inputs}};
    FunctionArgument res;

    machine.run_function("b2a", res, args);

This inputs the values 1 to 10 as 16-bit numbers. Note the nested
vectors for the inputs. This is due to the fact
``share_type::bit_type`` can only hold up to 64 bits, so for longer
bit lengths several entries have to be used.

Lastly, :download:`../Programs/Source/export-a2b.py` covers the other
direction::

  @export
  def a2b(x, res):
    print_ln('x=%s', x.reveal())
    res[:] = sbitvec(x, length=16)
    print_ln('res=%s', x.reveal())

  a2b(sint(size=10), sbitvec.get_type(16).Array(10))

The calling C++ code in :download:`../Utils/export-a2b.cpp` has to
initialize the binary shares even when they are only used for output:

.. code-block::

    int n = 10;
    vector<share_type> inputs;
    for (int i = 0; i < n; i++)
        inputs.push_back(
                share_type::constant(i + 1, my_number,
                        machine.get_sint_mac_key()));

    vector<vector<bit_share_type>> outputs(n,
            vector<bit_share_type>(1,
                    bit_share_type::constant(0, my_number,
                            machine.get_bit_mac_key())));

    vector<FunctionArgument> args = {{inputs}, {16, outputs}};
    FunctionArgument res;

    machine.run_function("a2b", res, args);


C++ compilation
---------------

The easiest way is to include ``Machines/maximal.hpp`` as in the first
example and put the C++ in code ``Utils/<name>.cpp`` and calling
``make <name>.x`` in the main directory. If using oblivious transfer
or homomorphic encryption, add the following line to ``Makefile``::

  <name>.x: $(FHEOFFLINE) $(OT)

Most of the examples work slightly differently, however, in order to
distribute the compilation load. Most notably,
:download:`../Utils/export-a2b.cpp`, which supports several protocols,
only includes ``Machines/minimal.hpp`` and "outsources" the virtual
machine for the various protocols to ``Machines/export-*.cpp``, which
are all compiled separately.


Reference
---------

.. doxygenclass:: FunctionArgument
   :members:
