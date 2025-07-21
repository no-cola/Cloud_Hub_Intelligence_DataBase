#!/usr/bin/env bash

HERE=$(cd `dirname $0`; pwd)
SPDZROOT=$HERE/..

. $HERE/run-common.sh

echo NOTE: This runs the SPDZ online phase, requiring a prior preprocessing generation with Fake-Offline.x
echo See https://github.com/data61/MP-SPDZ/?tab=readme-ov-file#protocols for all protocols.

run_player Player-Online.x $* || exit 1
