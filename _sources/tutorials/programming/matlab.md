---
title: Matlab
linkTitle: Matlab
weight: 1
tags:
- matlab
- programming
aliases:
- /tutorials/programming/matlab
description: A tutorial for setting up your matlab license on Neurodesk.
authors:
- name: Fernanda L. Ribeiro
- name: Michèle Masson-Trottier
date: '2026-10-21'
---
# MATLAB

:::{admonition} Learning Objectives
:class: tip

By the end of this tutorial you will be able to:

- Launch MATLAB and use the available activation route.
- Call a Neurodesk tool from MATLAB.
- Choose and save keyboard shortcut preferences.
:::


This tutorial covers activating MATLAB R2022a, calling a Neurodesk tool from MATLAB and changing keyboard shortcuts.

> _This tutorial was created by Fernanda L. Ribeiro._
>
> Email: fernanda.ribeiro@uq.edu.au · GitHub: @felenitaribeiro

[Getting Set Up with Neurodesk](https://neurodesk.org/getting-started/)

## Start MATLAB

You need your own MATLAB license. An eligible MathWorks account can activate MATLAB, or your institution can provide a network license file and access to its license server. A file installation key alone does not activate this installed copy; see [MathWorks' license-file and installation-key guidance](https://www.mathworks.com/help/install/ug/get-license-file-and-file-installation-key.html).

The desktop menu contains **Neurodesk (1) → Programming (2) → matlab (3) → matlabGUI 2022a (4)**.

![MATLAB entries in the current Neurodesk menu](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/launch-matlab-guide.png)

On the Neurodesktop image tested on 20 October 2026, that GUI entry exits without opening a window. Open **LXTerminal** from the bottom panel and start MATLAB directly:

```bash
ml matlab/2022a
matlab
```

If MATLAB reports **License Manager Error -1** because no license file is available, activate it first using the following procedure.

## Activate with a MathWorks account

In LXTerminal, run the official activation client from the installed R2022a container:

```bash
apptainer exec --bind /home/jovyan:/opt/matlab/R2022a/licenses /cvmfs/neurodesk.ardc.edu.au/containers/matlab_2022a_20231207/matlab_2022a_20231207.simg /opt/matlab/R2022a/bin/activate_matlab.sh
```

This command is specific to the tested R2022a image. It uses the same home-directory license binding as the installed MATLAB launcher.

1. Leave **Activate automatically using the Internet** selected.
2. Click **Next**.

![Activation client: 1 automatic activation, 2 Next](/static/tutorials/programming/matlab/activate-matlab-annotated.svg)

Complete the MathWorks sign-in yourself, choose an eligible license and follow the activation client's prompts. Keep the Linux login name `jovyan` when asked which user will run MATLAB. Account and license screens are omitted here because they contain private information. See [MathWorks' activation instructions for R2022a and earlier](https://uk.mathworks.com/matlabcentral/answers/99457-how-do-i-activate-matlab-or-other-mathworks-products) for the account-dependent steps.

After activation, close the client and launch MATLAB from LXTerminal again:

```bash
ml matlab/2022a
matlab
```

The MATLAB desktop should open. Double-click its title bar to maximize it.

![Activated MATLAB R2022a desktop](/static/tutorials/programming/matlab/matlab-desktop.jpg)

### Institutional network license

Ask your license administrator for the correct `network.lic` file and place it in `~/Downloads/network.lic`, the location used by this container's launcher. You must be able to reach the institution's license server from the Neurodesk instance. Use the administrator-provided file rather than constructing a license file from a license number. See [MathWorks' network-client installation guidance](https://www.mathworks.com/help/install/ug/install-products-on-client-machines.html). This alternative was not tested in the account-activated session above.

## Call Neurodesk tools from MATLAB

Add the chosen tool's Neurodesk wrapper directory to MATLAB's execution path. The older FSL 6.0.7.4 image used in this tutorial has been disabled by its maintainers. The following FSL 6.0.7.8 wrapper was verified in the current instance.

In the **MATLAB Command Window**, run:

```matlab
setenv("PATH", "/cvmfs/neurodesk.ardc.edu.au/containers/fsl_6.0.7.8_20240913:" + getenv("PATH"));
system('fslmaths');
```

Prepending the directory makes this wrapper take precedence over older FSL entries. Calling `fslmaths` without arguments prints its usage information; its nonzero exit status in this case is expected.

![FSL usage displayed in the MATLAB Command Window](/static/tutorials/programming/matlab/fslmaths-from-matlab.jpg)

To process an image, pass the arguments inside the command string, for example:

```matlab
status = system('fslmaths /path/to/input.nii.gz -mul 1 /home/jovyan/neurodesktop-storage/matlab-fsl-test.nii.gz');
```

Replace `/path/to/input.nii.gz` with an existing image. `status = 0` indicates success. This image-copy operation was tested from the GUI and its output matched the input voxel for voxel.

## Change keyboard shortcuts

MATLAB on Linux initially uses **Emacs Default Set**. To use the familiar Windows shortcuts, click **Preferences** on the **Home** ribbon.

![Open MATLAB Preferences](/static/tutorials/programming/matlab/preferences-ribbon-annotated.svg)

1. Expand **MATLAB → Keyboard** and select **Shortcuts**.
2. Change **Active settings** to **Windows Default Set**.
3. Click **OK**. Reopening Preferences should show the saved selection.

![Keyboard shortcuts: 1 Shortcuts, 2 Windows Default Set, 3 OK](/static/tutorials/programming/matlab/keyboard-shortcuts-annotated.svg)
