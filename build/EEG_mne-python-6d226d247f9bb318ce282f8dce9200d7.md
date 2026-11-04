---
title: Analysing EEG Data with MNE
linkTitle: 'MNE-Python: EEG'
weight: 1
aliases:
- /tutorials/electrophysiology/EEG_mne-python
description: 'Use mne-python to load, pre-process, and plot example EEG data in a
  jupyter notebook through vscode. '
authors:
- name: Angela Renton
- name: "Mich\xE8le Masson-Trottier"
date: '2026-10-21'
execute:
  skip: true
doi: 10.5281/zenodo.18718426
github: https://github.com/neurodesk/neurodeskedu/blob/main/books/tutorials/electrophysiology/EEG_mne-python.md
edit_url: https://github.com/neurodesk/neurodeskedu/edit/main/books/tutorials/electrophysiology/EEG_mne-python.md
downloads:
- url: /edu/_sources/tutorials/electrophysiology/EEG_mne-python.md
  title: Download source
  filename: EEG_mne-python.md
  static: false
---
# Analysing EEG Data with MNE




:::{admonition} Learning Objectives
:class: tip

By the end of this tutorial you will be able to:

- Distinguish commands for the terminal from code for notebook cells.
- Select the MNE Python kernel and load a public EEG recording.
- Inspect raw, filtered and averaged EEG in interactive plot windows.
:::


Use mne-python to load, pre-process, and plot example EEG data in a jupyter notebook through vscode. 

<!-- Following line adds a link to getting set up with Neurodesk -->
[Getting Set Up with Neurodesk](https://neurodesk.org/getting-started/)
<!-- -->

## Getting started

To begin, navigate to Neurodesk → Electrophysiology → mne → code 0.23.4 in the menu. This version of vscode has been installed in a software container together with a conda environment containing MNE-python. Note that if you open any other version of vscode in Neurodesk, you will not be able to access the MNE conda environment.

![Click 1 Neurodesk, 2 Electrophysiology, 3 mne, and 4 code 0.23.4](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/launch-mne-guide.png?v=0e87aca15eb3)

Follow the numbered menu targets: **1** Neurodesk → **2** Electrophysiology → **3** mne → **4** code 0.23.4.

Open the folder: “/neurodesktop-storage” or a subfolder in which you would like to store this demo. In this folder, create a new file named “EEGDemo.ipynb” or something similar:


If VS Code prompts you to install its Jupyter extension, click **Install**, then reopen the notebook. The extension may already be installed in your instance.

## Activate the MNE conda environment in the terminal

Next, activate the MNE environment in a terminal. From VS Code's top menu, select **Terminal → New Terminal**.

If this is your first time using vscode in this container, you may have to initialise conda by typing `conda init bash` in the bash terminal. After initialising bash, you will have to close and then reopen the terminal. 

Once you have initialised conda, you can activate the MNE environment in the terminal:

```bash
conda activate mne-0.23.4
```

If `conda activate` asks you to initialise the shell, you can also initialise only the current terminal without changing your shell startup files:

```bash
source /opt/miniconda-latest/etc/profile.d/conda.sh
conda activate mne-0.23.4
```


You should now see "(mne-0.23.4)" ahead of the current line in the terminal. Paste the download commands into this **terminal panel (1)**. The notebook cells remain above it.

![The MNE environment activated in the integrated terminal](/static/tutorials/electrophysiology/eeg_mne-python/mne-terminal-annotated.svg)

## Download sample data

In the terminal (in which you have activated the MNE environment), input the following code to download some BIDS formatted sample EEG data:

> Remember to update the path to the location you are storing this tutorial! 

```bash
python -m pip install osfclient
mkdir -p /neurodesktop-storage/EEGDemo
cd /neurodesktop-storage/EEGDemo
osf -p c689u fetch osfstorage/Data_sample.zip Data_sample.zip
unzip Data_sample.zip 
```

This is a small dataset with only 5 EEG channels from a single participant. The participant is viewing a frequency tagged display and is cued to attend to dots tagged at one frequency or another (6 Hz, 7.5 Hz) for long, 15 s trials. To read more about the dataset, click [here]( https://osf.io/c689u/)

## Load the sample EEG in a notebook cell

Return to **EEGDemo.ipynb** and click **+ Code** to create a Python code cell. Copy the complete block below into it. This is the loading code shown in the screenshots: it imports the Python packages and reads the BrainVision `.vhdr` file from the **Data_sample** folder downloaded above.

```python
# Interactive plotting
%matplotlib qt

# Import modules
import os
import numpy as np
import mne

# Load data
sample_data_folder = '/neurodesktop-storage/EEGDemo/Data_sample'
sample_data_raw_file = os.path.join(sample_data_folder, 'sub-01', 'eeg',
                                    'sub-01_task-FeatAttnDec_eeg.vhdr')
raw = mne.io.read_raw_brainvision(sample_data_raw_file, preload=True)
```

![Paste Python into a notebook code cell and run it with Shift+Enter](/static/tutorials/electrophysiology/eeg_mne-python/mne-notebook-cell-annotated.svg)

The highlighted **code cell (1)** receives the Python block. After selecting the kernel in the next step, run it using the **triangle (2)** or **Shift+Enter**.

`%matplotlib qt` opens plots in separate interactive windows. Every Python block from this section onwards goes into a **notebook code cell**; add a new cell for each block and run the cells in order.

## Select the MNE kernel and run the first cell

Next, we need to direct vscode to use the python kernel associated with MNE. In the top right corner of your notebook, click **Select Kernel (1)** (or the current kernel name).


Then select **mne-0.23.4** from the dropdown menu, marked **2** below.

![Select the mne-0.23.4 Python environment](/static/tutorials/electrophysiology/eeg_mne-python/mne-kernel-options-annotated.svg)

Click the first code cell and press **Shift+Enter**. It loads the EEG recording into the variable `raw`. If you saved the data elsewhere, change `sample_data_folder` to your extracted **Data_sample** folder before running the cell.

## Inspect and process the EEG

The [MNE tutorials](https://mne.tools/stable/auto_tutorials/index.html) explain the processing methods in more detail.

The `raw.info` structure contains information about the dataset:
```python
# Display data info
print(raw)
print(raw.info)
```

This data file did not include a montage. Lets create one using standard values for the electrodes we have:
```python
# Create montage
montage = {'Iz':  [0, -110, -40],
            'Oz': [0, -105, -15],
            'POz': [0,   -100, 15],
            'O1': [-40, -106, -15],
            'O2':  [40, -106, -15],
 }

montageuse = mne.channels.make_dig_montage(ch_pos=montage, lpa=[-82.5, -19.2, -46], nasion=[0, 83.2, -38.3], rpa=[82.2, -19.2, -46]) # based on mne help file on setting 10-20 montage
```

Next, lets visualise the data. 
```python
raw.plot()
```

This should open an interactive window in which you can scroll through the data. See the MNE documentation for help on how to customise this plot. 

![Interactive raw EEG traces](/static/tutorials/electrophysiology/eeg_mne-python/raw-eeg.png)

If, upon visual inspection, you decide to exclude one of the channels, you can specify this in `raw.info['bads']` now. For example:
```python
raw.info['bads'] = ['POz']
```

Next, we’ll extract our events. The trigger channel in this file is incorrectly scaled, so we’ll correct that before we extract our events:
```python
# Correct trigger scaling
trigchan = raw.copy()
trigchan = trigchan.pick('TRIG')
trigchan._data = trigchan._data*1000000

# Extract events
events = mne.find_events(trigchan, stim_channel='TRIG', consecutive=True, initial_event=True, verbose=True)
print('Found %s events, first five:' % len(events))
print(events[:5])

# Plot events
mne.viz.plot_events(events, raw.info['sfreq'], raw.first_samp)
```

![Events extracted from the trigger channel](/static/tutorials/electrophysiology/eeg_mne-python/events.png)

Now that we’ve extracted our events, we can extract our EEG channels and do some simple pre-processing:
```python
# select
eeg_data = raw.copy().pick_types(eeg=True, exclude=['TRIG'])

# Set montage
eeg_data.info.set_montage(montageuse)

# Interpolate
eeg_data_interp = eeg_data.copy().interpolate_bads(reset_bads=True) 

# Filter Data
eeg_data_interp.filter(l_freq=1, h_freq=45, h_trans_bandwidth=0.1)
```

Let’s visualise our data again now that it’s cleaner:
```python
#plot results again, this time with some events and scaling. 
eeg_data_interp.plot(events=events, duration=10.0, scalings=dict(eeg=0.00005), color='k', event_color='r')
```

![Filtered EEG after interpolation](/static/tutorials/electrophysiology/eeg_mne-python/filtered-eeg.png)

That’s looking good! We can even see hints of the frequency tagging. It’s about time to epoch our data. 
```python
# Epoch to events of interest
event_id = {'attend 6Hz K': 23, 'attend 7.5Hz K':  27}  

# Extract 15 s epochs relative to events, baseline correct, linear detrend, and reject 
# epochs where eeg amplitude is > 400
epochs = mne.Epochs(eeg_data_interp, events, event_id=event_id, tmin=0,
                    tmax=15, baseline=(0, 0), reject=dict(eeg=0.000400), detrend=1)  

# Drop bad trials
epochs.drop_bad()
```

We can average these epochs to form Event Related Potentials (ERPs):
```python
# Average erpochs to form ERPs
attend6 = epochs['attend 6Hz K'].average()
attend75 = epochs['attend 7.5Hz K'].average()

# Plot ERPs
evokeds = dict(attend6=list(epochs['attend 6Hz K'].iter_evoked()),
               attend75=list(epochs['attend 7.5Hz K'].iter_evoked()))
mne.viz.plot_compare_evokeds(evokeds, combine='mean')
```

![Evoked responses for both attention conditions](/static/tutorials/electrophysiology/eeg_mne-python/evoked-responses.png)

In this plot, we can see that the data are frequency tagged. While these data were collected, the participant was performing an attention task in which two visual stimuli were flickering at 6 Hz and 7.5 Hz respectively. On each trial the participant was cued to monitor one of these two stimuli for brief bursts of motion. From previous research, we expect that the steady-state visual evoked potential (SSVEP) should be larger at the attended frequency than the unattended frequency. Lets check if this is true. 

We'll begin by exporting our epoched EEG data to a numpy array

```python
# Preallocate
n_samples = attend6.data.shape[1]
sampling_freq = 1200 # sampling frequency
epochs_np = np.empty((n_samples, 2) )

# Get data - averaging across EEG channels
epochs_np[:,0] = attend6.data.mean(axis=0)
epochs_np[:,1] = attend75.data.mean(axis=0)

```

Next, we can use a Fast Fourier Transform (FFT) to transform the data from the time domain to the frequency domain. For this, we'll need to import the FFT packages from scipy:

```python
from scipy.fft import fft, fftfreq, fftshift

# Get FFT
fftdat = np.abs(fft(epochs_np, axis=0)) / n_samples
freq = fftfreq(n_samples, d=1 / sampling_freq)  # get frequency bins

```

Now that we have our frequency transformed data, we can plot our two conditions to assess whether attention altered the SSVEP amplitudes:

```python
import matplotlib.pyplot as plt

fig,ax = plt.subplots(1, 1)

ax.plot(freq, fftdat[:,0], '-', label='attend 6Hz', color=[78 / 255, 185 / 255, 159 / 255])  
ax.plot(freq, fftdat[:,1], '-', label='attend 7.5Hz', color=[236 / 255, 85 / 255, 58 / 255])  
ax.set_xlim(4, 17)
ax.set_ylim(0, 1e-6)
ax.set_title('Frequency Spectrum')
ax.legend()


```
![Frequency spectrum for both attention conditions](/static/tutorials/electrophysiology/eeg_mne-python/frequency-spectrum.png)

This plot shows that the SSVEPs were indeed modulated by attention in the direction we would expect! Congratulations! You’ve run your first analysis of EEG data in neurodesktop.
