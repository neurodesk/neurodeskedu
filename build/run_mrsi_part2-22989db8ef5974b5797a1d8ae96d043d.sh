#!/usr/bin/env bash
# MRSIProc 0.1.0: evaluate a complete Part 1 results folder.
# Usage: bash run_mrsi_part2.sh /absolute/path/to/a/copy/of/part1-results
set -e

results="${1:-$HOME/neurodesktop-storage/mrsi_proc/ProcessResults/test_files}"
if [[ ! -d "$results" ]]; then
    printf 'Part 1 results folder not found: %s\n' "$results" >&2
    exit 1
fi
if [[ ! -d "$results/spectra/CoordFiles" && ! -f "$results/CoordFiles.tar.gz" ]]; then
    printf 'No Part 1 coordinate outputs found in: %s\n' "$results" >&2
    exit 1
fi

ml mrsiproc/0.1.0

# In this release, -S, -R and -b are flags: none takes an argument.
# Both preserves MINC maps and also exports NIfTI maps.
Part2_EvaluateMRSI.sh \
    -o "$results" \
    -N Both \
    -S \
    -R \
    -b
