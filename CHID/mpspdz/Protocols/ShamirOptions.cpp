/*
 * ShamirMachine.cpp
 *
 */

#include "ShamirOptions.h"

#include <iostream>
using namespace std;

ShamirOptions ShamirOptions::singleton;

ShamirOptions& ShamirOptions::s()
{
    return singleton;
}

ShamirOptions::ShamirOptions(int nparties, int threshold) :
        nparties(nparties), threshold(threshold)
{
}

ShamirOptions::ShamirOptions(ez::ezOptionParser& opt, int argc, const char** argv)
{
    opt.add(
            "3", // Default.
            0, // Required?
            1, // Number of args expected.
            0, // Delimiter if expecting multiple args.
            "Number of players", // Help description.
            "-N", // Flag token.
            "--nparties" // Flag token.
    );
    opt.add(
            "", // Default.
            0, // Required?
            1, // Number of args expected.
            0, // Delimiter if expecting multiple args.
            "Number of corrupted parties (default: just below half)", // Help description.
            "-T", // Flag token.
            "--threshold" // Flag token.
    );
    opt.parse(argc, argv);
    opt.get("-N")->getInt(nparties);
    if (nparties < 3)
    {
        cerr << "Protocols based on Shamir secret sharing require at least "
                << "three parties." << endl;
        exit(1);
    }
    set_threshold(opt);
    opt.resetArgs();
}

void ShamirOptions::set_threshold(ez::ezOptionParser& opt)
{
    if (opt.isSet("-T"))
        opt.get("-T")->getInt(threshold);
    else
        threshold = (nparties - 1) / 2;
#ifdef VERBOSE
    cerr << "Using threshold " << threshold << " out of " << nparties << endl;
#endif
    if (2 * threshold >= nparties)
        throw runtime_error("threshold too high");
    if (threshold < 1)
    {
        cerr << "Threshold has to be positive" << endl;
        exit(1);
    }
}
