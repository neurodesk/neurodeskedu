---
title: Spectroscopy with lcmodel
linkTitle: lcmodel
weight: 1
tags:
- lcmodel
aliases:
- /tutorials/spectroscopy/lcmodel
description: Using lcmodel, you can analyze MR spectroscopy data.
authors:
- name: Steffen Bollmann
- name: Michèle Masson-Trottier
date: '2026-10-21'
---
# Spectroscopy with lcmodel

:::{admonition} Learning Objectives
:class: tip

By the end of this tutorial you will be able to:

- Launch LCModel and initialise its graphical interface.
- Load the bundled Varian spectrum and matching basis.
- Run the fit and inspect the saved spectral reports.
:::


Using lcmodel, you can analyze MR spectroscopy data.


> _This tutorial was created by Steffen Bollmann._
>
> Github: [@stebo85](https://github.com/stebo85)
> Web: [mri.sbollmann.net](https://mri.sbollmann.net/)
> Twitter: [@sbollmann_MRI](https://twitter.com/sbollmann_MRI)

<!-- Following line adds a link to getting set up with Neurodesk -->
[Getting Set Up with Neurodesk](https://neurodesk.org/getting-started/)
<!-- -->

Open the bottom-left Applications menu and select **Neurodesk (1) → Spectroscopy (2) → lcmodel (3) → lcmodel 6.3 (4)**.

![Follow the four numbered menu choices to open the LCModel terminal](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/launch-lcmodel-guide.png)

In the terminal opened by the menu, enter the setup command and press **Enter**:

```bash
setup_lcmodel.sh
```

Wait for the setup to finish. In the **same terminal**, enter the next command and press **Enter** to open the graphical interface:

```bash
lcmgui
```

We packed example data into the container (https://zenodo.org/record/3904443/) and we will use this to show a basic analysis.

The example data comes in the Varian fid format, so click **Varian** (1):

![Select Varian data in LCMgui](/static/tutorials/spectroscopy/lcmodel/select-data-type-annotated.svg)


Use the directory tree to navigate to:

```text
/opt/datasets/Spectra_hippocampus(rat)_TE02/s_20131015_03_BDL106_scan0/isise_01.fid
```

Double-click each directory to open it. Select the **fid** file (1) inside `isise_01.fid`, then click **OK** (2).

![Select the bundled Varian fid file](/static/tutorials/spectroscopy/lcmodel/select-fid-annotated.svg)


Then click **Change BASIS** and navigate to `/opt/datasets/Spectra_hippocampus(rat)_TE02/Control_files_Basis_set`. Select the supplied `9T_TE02_...BASIS` file (1) and click **OK** (2).

![Select the supplied basis set](/static/tutorials/spectroscopy/lcmodel/select-basis-annotated.svg)


If the Control Parameters window extends beyond the desktop, double-click its title bar to maximize it. Check the selected basis, then click **Run LCModel** (2):

![LCModel parameters with the selected basis file](/static/tutorials/spectroscopy/lcmodel/control-parameters-annotated.svg)


Click **Yes** (1) to analyze all ten voxels in Slice 1:

![Confirm analysis of the selected voxels](/static/tutorials/spectroscopy/lcmodel/confirm-analysis-annotated.svg)


Wait until the fitted spectra appear. Maximize the Ghostview window and press **-** to reduce the scale if the report is clipped; the screenshot uses scale 0.500. Closing a result window reveals the next voxel’s result. See the [Ghostview key bindings](https://www.gnu.org/software/gv/manual/gv.html) for display controls:

![Fitted spectroscopy result displayed in the LCModel viewer](/static/tutorials/spectroscopy/lcmodel/fitted-spectrum.jpg)

The results are also saved in `~/.lcmodel/saved/`. The tested example produced ten PostScript reports and ten result tables.

