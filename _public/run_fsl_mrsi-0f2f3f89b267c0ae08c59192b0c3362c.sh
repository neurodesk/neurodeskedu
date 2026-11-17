#!/usr/bin/env bash
# Fit the public example bundled with the authors' FSL-MRS 2.1.0 archive.
set -e

work="$HOME/neurodesktop-storage/fsl-mrs-demo/fsl_mrs-2.1.0/example_usage"
if [[ ! -f "$work/example_data/example_mrsi/mrsi.nii.gz" ]]; then
    printf 'Extract fsl_mrs-2.1.0.zip into ~/neurodesktop-storage/fsl-mrs-demo first.\n' >&2
    exit 1
fi
cd "$work"
if [[ -e MRSI/fsl_mrsi_fit ]]; then
    printf 'MRSI/fsl_mrsi_fit already exists. Retain it and choose a new output folder before rerunning.\n' >&2
    exit 1
fi

ml fsl/6.0.7.23
mkdir -p MRSI
mrsi_segment -o MRSI -a example_data/example_mrsi/T1.anat \
    example_data/example_mrsi/mrsi.nii.gz

# Serial mode avoids the tested Dask/Bokeh shutdown error in this container.
fsl_mrsi \
    --data example_data/example_mrsi/mrsi.nii.gz \
    --basis example_data/example_mrsi/3T_slaser_32vespa_1250_noTMS_defaultMM \
    --output MRSI/fsl_mrsi_fit \
    --mask example_data/example_mrsi/mask.nii.gz \
    --h2o example_data/example_mrsi/wref.nii.gz \
    --tissue_frac MRSI/mrsi_seg_wm.nii.gz MRSI/mrsi_seg_gm.nii.gz MRSI/mrsi_seg_csf.nii.gz \
    --baseline poly,2 \
    --metab_groups MM09 MM12 MM14 MM17 MM21 \
    --combine PCho GPC --combine Cr PCr --combine NAA NAAG \
    --combine Glu Gln --combine Glc Tau --ignore Gly \
    --parallel off --report
