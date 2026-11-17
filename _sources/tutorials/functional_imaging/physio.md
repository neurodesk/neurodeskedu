---
title: PhysIO
linkTitle: PhysIO
weight: 1
aliases:
- /tutorials/functional_imaging/physio
description: Example workflow for the PhysIO Toolbox
authors:
- name: Lars Kasper
- name: Michèle Masson-Trottier
date: '2026-10-21'
---
# PhysIO

:::{admonition} Learning Objectives
:class: tip

By the end of this tutorial you will be able to:

- Download the public PhysIO demonstration recordings.
- Configure and run the Philips ECG3T example in SPM Batch Editor.
- Inspect the physiological regressors and quality-control figures.
:::


Example workflow for the PhysIO Toolbox

> _This tutorial was created by Lars Kasper._
>
> Github: @mrikasper
>
> Twitter: @mrikasper

<!-- Following line adds a link to getting set up with Neurodesk -->
[Getting Set Up with Neurodesk](https://neurodesk.org/getting-started/)
<!-- -->

## Origin

The PhysIO Toolbox implements ideas for robust physiological noise modeling in fMRI, outlined in this paper:

1. Kasper, L., Bollmann, S., Diaconescu, A.O., Hutton, C., Heinzle, J., Iglesias, 
S., Hauser, T.U., Sebold, M., Manjaly, Z.-M., Pruessmann, K.P., Stephan, K.E., 2017. 
*The PhysIO Toolbox for Modeling Physiological Noise in fMRI Data*. 
Journal of Neuroscience Methods 276, 56-72. https://doi.org/10.1016/j.jneumeth.2016.10.019

PhysIO is part of the open-source [TAPAS Software Package](https://translationalneuromodeling.github.io/tapas/) for Translational Neuromodeling and Computational Psychiatry, introduced in the following paper:

2. Frässle, S., Aponte, E.A., Bollmann, S., Brodersen, K.H., Do, C.T., Harrison, O.K., Harrison, S.J., Heinzle, J., Iglesias, S., Kasper, L., Lomakina, E.I., Mathys, C., Müller-Schrader, M., Pereira, I., Petzschner, F.H., Raman, S., Schöbi, D., Toussaint, B., Weber, L.A., Yao, Y., Stephan, K.E., 2021. *TAPAS: an open-source software package for Translational Neuromodeling and Computational Psychiatry*. Frontiers in Psychiatry 12, 857. https://doi.org/10.3389/fpsyt.2021.680811

Please cite these works if you use PhysIO and see the [FAQ](https://gitlab.ethz.ch/physio/physio-doc/-/wikis/FAQ#3-how-do-i-cite-physio) for details.

Neurodesk offers the possibility of running PhysIO without installing MATLAB or requiring a MATLAB license. Debugging and extending the toolbox require the MATLAB version. Current source code is hosted in the [PhysIO repository](https://github.com/ComputationalPsychiatry/PhysIO).

More general information about PhysIO is available in the [README](https://github.com/ComputationalPsychiatry/PhysIO#readme).


## Purpose

The general purpose of the PhysIO toolbox is model-based physiological noise correction of fMRI data using peripheral measures of respiration and cardiac pulsation (respiratory bellows, ECG, pulse oximeter/plethysmograph).

It incorporates noise models of
- cardiac/respiratory phase (RETROICOR, Glover et al. 2000), as well as
- heart rate variability and respiratory volume per time (cardiac response function, Chang et. al, 2009, respiratory response function, Birn et al. 2006),
- and extended motion models (e.g., censoring/scrubbing)

While the toolbox is particularly well integrated with SPM via the Batch Editor GUI, its  output text files can be incorporated into any major neuroimaging analysis package for nuisance regression, e.g., within a GLM.

Core design goals for the toolbox were: flexibility, robustness, and quality assurance to enable physiological noise correction for large-scale and multi-center studies.

Some highlights:

-  Robust automatic preprocessing of peripheral recordings via iterative peak detection, validated in noisy data and patients, and extended processing of respiratory data (Harrison et al., 2021)
- Flexible support of peripheral data formats (BIDS, Siemens, Philips, GE, BioPac, HCP, ...) and noise models (RETROICOR, RVHRCOR).
- Fully automated noise correction and performance assessment for group studies.
- Integration in fMRI pre-processing pipelines as SPM Toolbox (Batch Editor GUI).

The accompanying technical paper about the toolbox concept and methodology can be found at: https://doi.org/10.1016/j.jneumeth.2016.10.019


## Download Example Data

This walkthrough uses the official [PhysIO examples v9.1.0 archive on Zenodo](https://zenodo.org/records/19075176). This version was tested with Neurodesk's `physio/r2021a` container in October 2026.

1. Open Firefox **inside the Neurodesk desktop** and visit the archive page.
2. Under **Files**, click **Download** (1). The archive is about 38.5 MB.

![Download the official PhysIO examples archive: click Download under Files](/static/tutorials/functional_imaging/physio/download-examples-annotated.svg)

3. Open **Downloads** in the file manager, right-click the downloaded ZIP and select **Extract Here**.
4. Rename the extracted `ComputationalPsychiatry-PhysIO-Examples-9343a40` folder to `physio-demo` and move it into `~/neurodesktop-storage/`.
5. Open `physio-demo/Philips/ECG3T/`. It should contain `SCANPHYSLOG.log`, `rp_fMRI.txt` and the `philips_ecg3t_*` scripts and batch files.

## Copy your own data

- On Windows, the folder `C:\neurodesktop-storage` should have been automatically created when starting neurodesk
- This is your direct link to the neurodesk environment, and anything you put in there should end up within the neurodesk desktop in `/neurodesktop-storage/` and on your desktop under `storage`


## Example: Running PhysIO in the GUI

### Start SPM

In the bottom-left Applications menu, select **Neurodesk (1) → Functional Imaging (2) → physio (3) → physioGUI r2021a (4)**.

![Follow the four numbered menu choices to open PhysIO](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/launch-physio-guide.png)

If the menu does not open SPM, open **LXTerminal** from the desktop panel and enter these two commands, one at a time:

```bash
ml physio/r2021a
spm12 fmri
```

Wait for the SPM windows to appear. This command selects fMRI mode directly. The remaining steps use the SPM GUI.

### Select the working directory

1. In SPM's main **Menu** window, open **Utils…** (1) and choose **CD** (2).

![SPM main menu: open Utils, then choose CD](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/spm-change-directory-guide.png)

2. Navigate to `~/neurodesktop-storage/physio-demo/Philips/` using the left-hand directory list. In the **right-hand list**, click **ECG3T**, then **Done**. The selected directory appears in the box at the bottom before you click Done.

The batch uses relative input paths, so SPM must be working in the folder containing `SCANPHYSLOG.log` and `rp_fMRI.txt`.

### Load and run the batch

1. Click **Batch** (1) in SPM's main Menu window.

![Open Batch Editor using the Batch button](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/spm-open-batch-guide.png)

2. In Batch Editor, choose **File → Load Batch**, or click the **open-folder icon** (1 in the next screenshot).
3. Select **`philips_ecg3t_spm_job.m`**, then **Done**. Wait for **TAPAS PhysIO Toolbox** to appear in the Module List. The corresponding `.mat` file is also supplied; do not select `philips_ecg3t_matlab_script.m`.
4. Leave the example parameters unchanged. `save_dir` is `physio_out`, a subfolder of the selected working directory.
5. Click the green **Play** button (2).

![Loaded PhysIO batch: open-folder icon and green Play button](/static/tutorials/functional_imaging/physio/loaded-batch-annotated.svg)

Several quality-control figures open during processing. The final figure is **Model: RETROICOR GLM regressors**, showing the nuisance regressor matrix. Maximize this figure to see all scan rows and regressor labels.

![PhysIO nuisance regressor matrix from the Philips ECG3T example](/static/tutorials/functional_imaging/physio/nuisance-regressor-matrix.jpg)

The tested example produced `physio_out/multiple_regressors.txt` with **495 rows and 24 columns**, plus `physio.mat` and saved quality-control figures. If the final matrix does not appear, check the terminal associated with SPM for errors. For missing input files, check the working directory and the paths under **log_files** and the movement-regressor settings in Batch Editor.

To create a new batch from scratch, use **SPM → Tools → TAPAS PhysIO Toolbox** in Batch Editor. Loading the supplied example already creates this module.

## Further Info on PhysIO

Please check out the [README](https://github.com/ComputationalPsychiatry/PhysIO#readme) and [FAQ](https://gitlab.ethz.ch/physio/physio-doc/-/wikis/FAQ).
