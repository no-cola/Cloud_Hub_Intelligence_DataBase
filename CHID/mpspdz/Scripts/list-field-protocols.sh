#!/bin/bash

dir="$(dirname $0)"
echo rep-field shamir mal-rep-field ps-rep-field sy-rep-field \
     atlas mal-shamir sy-shamir semi mascot `$dir/list-he-protocols.sh`
