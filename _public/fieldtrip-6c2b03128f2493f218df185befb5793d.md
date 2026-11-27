---
title: Analysing M/EEG Data with FieldTrip
linkTitle: fieldtrip
weight: 1
tags:
- fieldtrip
- documentation
aliases:
- /static/tutorials/electrophysiology/fieldtrip
description: A brief guide to using FieldTrip to analyse electrophysiological data
  within neurodesk.
authors:
- name: Judy D Zhu
- name: "Mich\xE8le Masson-Trottier"
date: '2026-10-21'
execute:
  skip: true
doi: 10.5281/zenodo.18718424
github: https://github.com/neurodesk/neurodeskedu/blob/main/books/tutorials/electrophysiology/fieldtrip.md
edit_url: https://github.com/neurodesk/neurodeskedu/edit/main/books/tutorials/electrophysiology/fieldtrip.md
downloads:
- url: /edu/_sources/tutorials/electrophysiology/fieldtrip.md
  title: Download source
  filename: fieldtrip.md
  static: false
---
# Analysing M/EEG Data with FieldTrip




:::{admonition} Learning Objectives
:class: tip

By the end of this tutorial you will be able to:

- Open the compiled FieldTrip environment.
- Download a public EEG recording and a ready-to-run MATLAB script.
- Browse recording segments and adjust the time scale.
:::

The Neurodesk container runs compatible FieldTrip scripts using MATLAB Runtime. A MATLAB licence is not required for this example.

## General use

### Open the FieldTrip terminal

From Neurodesktop's bottom-left Applications menu, choose **Neurodesk (1) → Electrophysiology (2) → fieldtrip (3) → fieldtrip 20211114 (4)**.

![The four numbered choices that launch FieldTrip](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/launch-fieldtrip-guide.png)

This opens a terminal with **[fieldtrip/20211114]** in its prompt. Commands go after that prompt.

![Terminal with FieldTrip loaded](/static/tutorials/electrophysiology/fieldtrip/fieldtrip-terminal.jpg)

For a compatible script of your own, run the following in this terminal, replacing the example path:

```bash
run_fieldtrip.sh /opt/MCR/v99 /path/to/yourscript.m
```

The script determines which viewer opens. It can call the FieldTrip, SPM and toolbox functions included in this compiled release; its search path cannot be extended with `addpath`, and internal script functions are unsupported. Develop new scripts in MATLAB before running them in the compiled environment.

## Worked example: browse a public EEG recording

### 1. Download and extract the recording

Open a **separate LXTerminal** using Neurodesktop's terminal icon. Use this normal terminal for downloading the data. The tested platform already includes `osf`; if it is unavailable, install its client here with `python -m pip install --user osfclient`.

Paste these commands into this download terminal, pressing **Enter** after each line:

```bash
mkdir -p ~/neurodesktop-storage/EEGDemo
cd ~/neurodesktop-storage/EEGDemo
osf -p c689u fetch osfstorage/Data_sample.zip Data_sample.zip
unzip -nq Data_sample.zip
```

The [public OSF recording](https://osf.io/c689u/) is approximately 157 MB and has five EEG channels. Wait for **100%** and for the terminal prompt to return. `unzip -nq` extracts quietly and preserves files that already exist. If you already downloaded `Data_sample.zip` for the MNE tutorial, reuse it and run only the extraction command.

![The EEG archive has finished downloading and extraction has returned to the prompt](/static/tutorials/electrophysiology/fieldtrip/download-data.png)

The recording's BrainVision files should now be under `~/neurodesktop-storage/EEGDemo/Data_sample/sub-01/eeg/`.

### 2. Download the browsing script

In **Firefox inside Neurodesk**, open the [browse-eeg.m file on GitHub](https://github.com/neurodesk/neurodeskedu/blob/main/books/static/tutorials/electrophysiology/fieldtrip/browse-eeg.m). Click **Download raw file (1)**, the downward arrow beside **Raw**, and save it in **Downloads** as **browse-eeg.m**.

![The browsing script and GitHub's Download raw file button](/static/tutorials/electrophysiology/fieldtrip/download-script-annotated.svg)

You can also [download the script directly](/static/tutorials/electrophysiology/fieldtrip/browse-eeg.m). If your browser displays its text, use **Save Page As…** and keep the `.m` filename extension.

The script already uses the data folder above. Its `cfg.readbids = false` setting makes this FieldTrip release read the recording's native BrainVision header and markers; it avoids a sampling-frequency parsing error in this sample's JSON metadata. The data files are left unchanged.

### 3. Run the downloaded script

Return to the **FieldTrip terminal opened from the application menu**, identified by **[fieldtrip/20211114]**. Paste this command after its prompt and press **Enter**:

```bash
run_fieldtrip.sh /opt/MCR/v99 ~/Downloads/browse-eeg.m
```

![The downloaded script is run in the FieldTrip-loaded terminal](/static/tutorials/electrophysiology/fieldtrip/run-script.png)

Wait for **ft_databrowser** to open, then double-click its title bar to maximise it. The first view shows **segment 1/309**, covering approximately 0–10 seconds. The large initial transient is present in this recording. Five EEG traces and the TRIG channel are displayed.

![The first segment in the actual FieldTrip data browser](/static/tutorials/electrophysiology/fieldtrip/first-segment.png)

### 4. Move between segments

Click **> beside segment (1)** at the bottom of the viewer. The title changes to **segment 2/309, time from 10 to 19.9992 s**. The matching **<** button returns to the previous segment.

![The second segment, with navigation and horizontal zoom controls numbered](/static/tutorials/electrophysiology/fieldtrip/raw-eeg-browser-annotated.svg)

### 5. Change the time scale

Click **+ beside horizontal (2)** to shorten the displayed interval. The title and segment count update; this click displays approximately seven seconds. The matching **−** button widens the interval again.

![The same recording after shortening the horizontal time interval](/static/tutorials/electrophysiology/fieldtrip/horizontal-zoom.png)

Close the data-browser window to finish this viewing exercise and return to the terminal. For artifact selection and other browsing options, see the [official FieldTrip data-browser guide](https://www.fieldtriptoolbox.org/faq/how_can_i_use_the_databrowser/).
