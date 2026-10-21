---
title: Spectroscopy pipeline with MRSIProc
linkTitle: mrsiproc
weight: 1
tags:
- mrsiproc
aliases:
- /tutorials/spectroscopy/mrsiproc
description: Using mrsiproc, you can reconstruct and analyze MR spectroscopy data.
authors:
- name: Korbinian Eckstein
- name: Michèle Masson-Trottier
date: '2026-10-21'
---
# Spectroscopy pipeline with MRSIProc

:::{admonition} Learning Objectives
:class: tip

By the end of this tutorial you will be able to:

- Prepare the two MRSI processing scripts in Neurodesktop.
- Pass the completed Part 1 results to Part 2 using the correct options.
- Check for generated maps and open them in Freeview.
:::

MRSIProc reconstructs and analyses MR spectroscopic imaging data. **Part 1** reconstructs the acquisition and runs LCModel fitting. **Part 2** evaluates those results and creates maps for inspection.

For a complete public-data exercise with fitted spectra and map screenshots, follow [FSL-MRS: fit and inspect a public MRSI dataset](fsl-mrs.md). FSL-MRS uses a different processing workflow; its outputs are not inputs to MRSIProc Part 2.

## Inputs and verification status

This is a **bring-your-own-data workflow**. The supplied scripts contain example paths; you must set them to a compatible MRSI DAT acquisition and its T1/INV1 DICOM folders. The T1 folders used by this example should contain the acquisition's `.IMA` files. Select a basis set and control file appropriate to your acquisition before processing.

The current screenshots demonstrate script preparation and syntax checks. The Part 2 option parser has also been checked against the installed **mrsiproc 0.1.0** container. Preparation checks do not establish successful reconstruction or fitting. Use the FSL-MRS tutorial above for the demonstrated public-data example; use this reference when you have compatible MRSIProc inputs.

## General use: start the desktop

In JupyterLab's Launcher, choose **Neurodesktop VNC (2)**.

![Neurodesktop RDP is 1 and VNC is 2](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/neurodesktop-launcher-desktop.png)

Use the **terminal icon in Neurodesktop's bottom panel** for the Bash commands below. Use **Mousepad** to edit the `.sh` scripts. Each script loads `mrsiproc/0.1.0` when run.

## Part 1: prepare reconstruction and fitting

### 1. Open the Part 1 template

Download [run_mrsi_part1.sh](/static/tutorials/spectroscopy/mrsiproc/run_mrsi_part1.sh) in **Firefox inside Neurodesk**, saving it in **Downloads**. Open it from the Neurodesktop terminal:

```bash
mousepad ~/Downloads/run_mrsi_part1.sh
```

Maximise Mousepad by double-clicking its title bar. Set the three acquisition input paths **(1)** and the Part 1 output path **(2)** to your files. Save with **Ctrl+S** and close the editor.

![Set the input paths and the output folder in the Part 1 script](/static/tutorials/spectroscopy/mrsiproc/part1-template-annotated.svg)

The template uses the same acquisition settings as the original example:

```bash
Part1_ProcessMRSI.sh \
    -c "$mrsi_input" \
    -t "$t1_input" \
    -a "$inv1_input" \
    -b fid_1.300000ms.basis \
    -o "$mrsi_results" \
    -j LCModel_Control_Template.m \
    -m dreid \
    -L "L2,0.2"
```

These lines are **already in the downloaded script**, where the variables are defined. The bundled basis and control filenames are starting points for this example; their presence does not establish suitability for another acquisition.

### 2. Check and run Part 1

In the **Neurodesktop terminal**, check the script's syntax:

```bash
bash -n ~/Downloads/run_mrsi_part1.sh
```

A successful syntax check returns to the prompt without output. After setting and verifying your input paths and acquisition parameters, run:

```bash
bash ~/Downloads/run_mrsi_part1.sh
```

The input guard stops the template if its example DAT file or structural folders do not exist. Reconstruction and LCModel fitting can take several hours. Wait for completion, inspect the processing log for errors, and retain the **whole output folder**, including sidecar files and coordinate outputs. Part 2 uses that folder's contents.

## Part 2: evaluate the fitted spectra and inspect maps

### 1. Prepare a working copy of the Part 1 results

Use a **completed Part 1 results folder**. Part 2 rebuilds map subfolders, so perform evaluation on a working copy if you need to retain an earlier set of maps.

In the **Neurodesktop terminal**, set `part1_results` to the actual folder created by Part 1. The path below matches the template's default output:

```bash
part1_results="$HOME/neurodesktop-storage/mrsi_proc/ProcessResults/test_files"
part2_copy="$HOME/neurodesktop-storage/mrsiproc-demo/part1-copy"
mkdir -p "$part2_copy"
cp -a "$part1_results/." "$part2_copy/"
```

Copy the complete folder. For this release, the Part 1 LCModel coordinate outputs should be available as `spectra/CoordFiles/` or `CoordFiles.tar.gz`; other Part 1 metadata and structural files are also required.

### 2. Open the corrected Part 2 script

Download [run_mrsi_part2.sh](/static/tutorials/spectroscopy/mrsiproc/run_mrsi_part2.sh) in **Firefox inside Neurodesk**, saving it in **Downloads**. Open it from the terminal:

```bash
mousepad ~/Downloads/run_mrsi_part2.sh
```

The script accepts your results folder as its first command-line argument. The default folder **(1)** is used only when no argument is supplied. The options **(2)** create maps while retaining both MINC and NIfTI outputs. Save any changes with **Ctrl+S**, then close Mousepad.

![The Part 2 results path and corrected options in Mousepad](/static/tutorials/spectroscopy/mrsiproc/part2-template-annotated.svg)

The processing command already included in this script is:

```bash
Part2_EvaluateMRSI.sh \
    -o "$results" \
    -N Both \
    -S \
    -R \
    -b
```

| Option | Meaning in mrsiproc 0.1.0 |
|---|---|
| `-o` | The complete Part 1 results folder, here a working copy. |
| `-N Both` | Retain MINC maps and also export NIfTI maps. |
| `-S` | Enable spectral maps for inspecting spectra and fits. |
| `-R` | Create ratio maps. |
| `-b` | Run tissue segmentation, using the structural information from Part 1. |

**Version-specific fix:** in the installed 0.1.0 script, `-S`, `-R` and `-b` are flags with no value. The older tutorial's `-S "Glu,Gln,Raw-abs-csi"` stops option parsing at that text, leaving the later options unprocessed. The corrected template removes it and uses an absolute results path.

### 3. Check the script before processing

In the **Neurodesktop terminal**, run:

```bash
bash -n ~/Downloads/run_mrsi_part2.sh && printf 'Part 2 script syntax: OK\n'
bash -c 'type ml >/dev/null' && printf 'Neurodesk module command: available\n'
```

![The actual script syntax and module-command checks passed](/static/tutorials/spectroscopy/mrsiproc/part2-preflight.png)

These checks verify script preparation. They do not run Part 2 or validate your acquisition data.

### 4. Run Part 2 on the completed working copy

In the **Neurodesktop terminal**, pass the working-copy folder explicitly:

```bash
bash ~/Downloads/run_mrsi_part2.sh "$HOME/neurodesktop-storage/mrsiproc-demo/part1-copy"
```

The script checks for the folder and coordinate outputs before loading the processing module. If either is absent, check the Part 1 output path and copy the complete results before retrying. Wait for processing to finish and inspect its log for errors.

### 5. Locate and inspect the generated maps

After a successful Part 2 run, list the maps from the **Neurodesktop terminal**:

```bash
part2_copy="$HOME/neurodesktop-storage/mrsiproc-demo/part1-copy"
find "$part2_copy/maps" -type f \
    \( -name '*.nii' -o -name '*.nii.gz' -o -name '*.mnc' \)
```

The exact map names depend on the fitted metabolites and enabled options. Check the metabolite and quality maps, the `maps/Ratio/` outputs requested by `-R`, and the spectral maps requested by `-S`. A returned prompt or an `END` message alone does not establish that the expected maps were generated.

To view a generated NIfTI map, open Freeview from the terminal:

```bash
ml freesurfer/8.2.0
freeview
```

Wait for the **FreeView** window. Choose **File → Load Volume… (1)** and select an actual map from your working copy's `maps/` folder.

![Freeview's File menu; Load Volume is numbered 1](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/freeview-menu-guide.png)

Load the matching structural image as another volume to inspect coverage and alignment. For volume display controls, see the [Freeview GUI walkthrough](../structural_imaging/freesurfer.md). Review maps and fitting quality together before interpreting metabolite values.

## Further information

The [MRSI pipeline project](https://github.com/korbinian90/mrsi_pipeline_neurodesk) contains the processing scripts and their option documentation. Use options appropriate to the container version you are running; newer releases can expose different arguments.
