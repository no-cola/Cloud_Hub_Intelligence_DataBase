/*
 * export-b2a.cpp
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
    Opener<share_type> MC(machine.get_player(), machine.get_sint_mac_key());
    MixedProtocolSet<share_type> set(machine.get_player(), machine);

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

    MC.init_open();
    for (auto& x : outputs)
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
