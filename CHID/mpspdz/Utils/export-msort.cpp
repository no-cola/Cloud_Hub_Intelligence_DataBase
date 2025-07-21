/*
 * export-sort.cpp
 *
 */

#include "Machines/minimal.hpp"

int main(int argc, const char** argv)
{
    assert(argc > 1);
    int my_number = atoi(argv[1]);
    int port_base = 9999;
    Names N(my_number, 3, "localhost", port_base);

    typedef Rep3Share2<64> share_type;
    Machine<share_type> machine(N);

    int n = 1000;

    vector<share_type> inputs;
    for (int i = 0; i < n; i++)
    {
        int j = (i % 2) ? i : (n - i);
        inputs.push_back(share_type::constant(j, my_number));
    }

    vector<long> key_indices = {1};

    vector<FunctionArgument> args = {{inputs, true}, key_indices};
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
            if (not i % 2 and x != i + 2)
            {
                cerr << "error at " << i << ": " << x << endl;
                exit(1);
            }
        }
    }
}
