/*
 * export-a2b.cpp
 *
 */

// use maximal.hpp if changes cause compilation errors

#include "Machines/minimal.hpp"

template<class share_type, class gf2n_type = NoShare<gf2n>>
void run(int, const char**);

int main(int argc, const char** argv)
{
    if (argc < 2 or argv[2] == string("ring"))
        run<Rep3Share2<64>>(argc, argv);
    else if (argv[2] == string("atlas"))
        run<AtlasShare<gfp_<0, 2>>>(argc, argv);
    else if (argv[2] == string("mascot"))
        run<Share<gfp_<0, 2>>, Share<gf2n>>(argc, argv);
    else if (argv[2] == string("cowgear"))
        run<CowGearShare<gfp_<0, 2>>>(argc, argv);
    else if (argv[2] == string("dealer-ring"))
        run<DealerShare<SignedZ2<64>>>(argc, argv);
    else if (argv[2] == string("hemi"))
        run<HemiShare<gfp_<0, 2>>>(argc, argv);
    else if (argv[2] == string("rep4-ring"))
        run<Rep4Share2<64>>(argc, argv);
    else if (argv[2] == string("semi2k"))
        run<Semi2kShare<64>>(argc, argv);
    else if (argv[2] == string("spdz2k"))
        run<Spdz2kShare<64, 64>, Share<gf2n>>(argc, argv);
    else if (argv[2] == string("sy-rep-ring"))
        run<SpdzWiseRingShare<64, 40>>(argc, argv);
    else
    {
        cerr << "unsupported protocol: " << argv[2] << endl;
        exit(1);
    }
}

template<class share_type, class gf2n_type>
void run(int argc, const char** argv)
{
    assert(argc > 3);
    int my_number = atoi(argv[1]);
    int port_base = 9999;
    Names N(my_number, atoi(argv[3]), "localhost", port_base);

    typedef typename share_type::bit_type bit_share_type;

    Machine<share_type, gf2n_type> machine(N);
    Opener<bit_share_type> MC(machine.get_player(), machine.get_bit_mac_key());

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

    MC.init_open();
    for (auto& x : outputs)
        MC.prepare_open(x.at(0));
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
            if (x != i + 1 and share_type::real_shares(machine.get_player()))
            {
                cerr << "error at " << i << ": " << x << endl;
                exit(1);
            }
        }
    }
}
