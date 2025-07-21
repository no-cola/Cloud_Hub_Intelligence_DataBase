/*
 * FunctionArgument.h
 *
 */

#ifndef PROCESSOR_FUNCTIONARGUMENT_H_
#define PROCESSOR_FUNCTIONARGUMENT_H_

#include "Protocols/ShareInterface.h"

#include <assert.h>

/**
 * Inputs and outputs for functions exported in high-level code.
 */
class FunctionArgument
{
    void* data;
    size_t size, n_bits;
    string reg_type;
    bool memory;

public:
    static void open(ifstream& file, const string& name,
            vector<FunctionArgument>& arguments);

    /**
     * Argument with integer secret shares.
     *
     * @param values shares
     * @param memory whether shares are in a (multi-)array (true) or vector (false)
     */
    template<class T>
    FunctionArgument(vector<T>& values, bool memory = false) :
            FunctionArgument(values.data(), values.size(), memory)
    {
        assert(not T::clear::characteristic_two);
    }

    FunctionArgument(ShareInterface* data, size_t size, bool memory) :
            data(data), size(size), n_bits(0), reg_type("s"), memory(memory)
    {
    }

    /**
     * Void argument.
     */
    FunctionArgument() : FunctionArgument(0, 0, false)
    {
    }

    /**
     * Argument with binary secret shares (always in array).
     *
     * @param n_bits number of bits
     * @param values shares (vector of vectors of bit_type)
     */
    template<class T>
    FunctionArgument(size_t n_bits, vector<vector<T>>& values) :
            data(values.data()), size(values.size()), n_bits(n_bits),
            reg_type("sbv"), memory(true)
    {
        assert(T::clear::binary);
        assert(not values.empty());
        assert(n_bits > 0);
        size_t n_limbs = DIV_CEIL(n_bits, T::default_length);
        size_t dl = T::default_length;
        for (auto& x : values)
        {
            assert(x.size() == n_limbs);
            for (size_t i = 0; i < n_limbs; i++)
                assert(size_t(x[i].maximum_size()) >= min(dl, n_bits - i * dl));
        }
    }

    /**
     * Argument with integer array.
     */
    FunctionArgument(vector<long>& values) :
            data(values.data()), size(values.size()), n_bits(0),
            reg_type("ci"), memory(false)
    {
    }

    size_t get_size()
    {
        return size;
    }

    size_t get_n_bits()
    {
        return n_bits;
    }

    string get_type_string()
    {
        if (data == 0)
            return "-";

        if (memory)
            if (reg_type == "sbv")
                return reg_type + ":[" + to_string(get_size()) + "x"
                        + to_string(n_bits) + "]";
            else
                return reg_type + ":[" + to_string(get_size()) + "]";
        else
            return reg_type + ":" + to_string(get_size());
    }

    string get_python_arg()
    {
        assert(data);
        if (memory)
            if (reg_type == "sbv")
                return "sbitvec.get_type(" + to_string(n_bits) + ").Array("
                        + to_string(get_size()) + ")";
            else
                return "sint.Array(" + to_string(get_size()) + ")";
        else if (reg_type == "ci")
            return "regint(0, size=" + to_string(get_size()) + ")";
        else
            return "sint(0, size=" + to_string(get_size()) + ")";
    }

    bool get_memory()
    {
        return memory;
    }

    bool has_reg_type(const char* reg_type);

    template<class T>
    T& get_value(size_t index)
    {
        return ((T*) data)[index];
    }

    void check_type(const string& type_string);
};

#endif /* PROCESSOR_FUNCTIONARGUMENT_H_ */
