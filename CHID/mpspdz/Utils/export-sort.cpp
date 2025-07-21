/*
 * export-sort.cpp
 *
 */

#include "Machines/maximal.hpp"

int main(int argc, const char** argv)
{
    assert(argc > 1);
    int my_number = atoi(argv[1]);
    int port_base = 9999;
    Names N(my_number, 3, "localhost", port_base);

    typedef Rep3Share2<64> share_type;
    Machine<share_type> machine(N);

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

    vector<FunctionArgument> args = {{inputs, true}};
    FunctionArgument res;

    machine.run_function("sort", res, args);

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
}
