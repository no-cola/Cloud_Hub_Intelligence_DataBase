/*
 * FunctionArgument.cpp
 *
 */

#include "FunctionArgument.h"

#include <fstream>

void FunctionArgument::open(ifstream& file, const string& name,
        vector<FunctionArgument>& arguments)
{
    string signature;
    for (auto& arg : arguments)
        signature += "-" + arg.get_type_string();
    string filename = "Programs/Functions/" + name + signature;

    file.open(filename);
    if (not file.good())
    {
        string python_call = name + "(";
        for (auto& arg : arguments)
        {
            python_call += arg.get_python_arg();
            if (&arg != &arguments[arguments.size() - 1])
                python_call += ", ";
        }
        python_call += ")";
        throw runtime_error(
                "Cannot open " + filename + ", have you compiled '"
                        + python_call
                        + "' and added '@export' to the function '" + name
                        + "'?");
    }
}

void FunctionArgument::check_type(const string& type_string)
{
    if (type_string != get_type_string()
            and get_type_string() != "-")
        throw runtime_error(
                "return type mismatch: " + get_type_string() + "/"
                        + type_string);
}

bool FunctionArgument::has_reg_type(const char* reg_type)
{
    return this->reg_type == string(reg_type);
}
