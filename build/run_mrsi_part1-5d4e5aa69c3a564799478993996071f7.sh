#!/usr/bin/env bash
# Example for a compatible DAT acquisition and T1/INV1 DICOM folders.
set -e

mrsi_input="$HOME/neurodesktop-storage/data/meas_test.dat"
t1_input="$HOME/neurodesktop-storage/data/T1"
inv1_input="$HOME/neurodesktop-storage/data/INV1"
mrsi_results="$HOME/neurodesktop-storage/mrsi_proc/ProcessResults/test_files"

if [[ ! -f "$mrsi_input" || ! -d "$t1_input" || ! -d "$inv1_input" ]]; then
    printf 'Edit the input paths to your own compatible acquisition first.\n' >&2
    exit 1
fi

ml mrsiproc/0.1.0

Part1_ProcessMRSI.sh \
    -c "$mrsi_input" \
    -t "$t1_input" \
    -a "$inv1_input" \
    -b fid_1.300000ms.basis \
    -o "$mrsi_results" \
    -j LCModel_Control_Template.m \
    -m dreid \
    -L "L2,0.2"
