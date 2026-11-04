---
title: 'FreeSurfer: viewing anatomy with Freeview'
linkTitle: FreeSurfer
weight: 1
aliases:
- /tutorials/structural_imaging/freesurfer
description: A GUI walkthrough of anatomical images, segmentations and cortical surfaces
  using bundled demonstration data.
authors:
- name: Steffen Bollmann
- name: Michèle Masson-Trottier
date: '2026-10-21'
---
# FreeSurfer: viewing anatomy with Freeview

:::{admonition} Learning Objectives
:class: tip

By the end of this tutorial you will be able to:

- Open Freeview from a Neurodesk terminal.
- Load an anatomical image and a coloured segmentation.
- Read structure labels and explore a cortical surface in 3D.
:::

Freeview is FreeSurfer's graphical viewer for anatomical images, segmentations and surfaces. This example uses the **fsaverage demonstration files bundled with FreeSurfer 8.2.0**. You can start immediately without downloading a participant dataset or waiting for a reconstruction.

## General use

Open **LXTerminal** using the terminal icon in Neurodesktop's bottom panel. Click after the terminal prompt, where the cursor appears, and paste these commands, pressing **Enter** after each line:

```bash
ml freesurfer/8.2.0
freeview
```

Wait until the **FreeView** window has fully opened, then double-click its title bar to maximize it. You should see the **File** menu, toolbar and empty viewing area shown below. Keep the launch terminal open in the background while Freeview runs.

![Freeview fully open and ready to load the first anatomical image](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/freeview-start.png)

The tested FreeSurfer container supplies a license. License contents do not need to be copied into a tutorial or typed into Freeview. If another container asks for a license, follow its launch-terminal instructions or obtain your own from the [FreeSurfer registration page](https://surfer.nmr.mgh.harvard.edu/registration.html).

## Worked example: anatomy, labels and a surface

### 1. Open the anatomical image

In Freeview, choose **File → Load Volume… (1)**. The same menu also contains **Load Surface… (2)**, which we will use later.

![Freeview File menu: Load Volume is 1 and Load Surface is 2](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/freeview-menu-guide.png)

Paste the following path into **Select volume file (1)** in the **Load Volume** dialog:

```text
/opt/freesurfer-8.2.0/subjects/fsaverage/mri/T1.mgz
```

Leave **Color map** as **Grayscale**, then click **OK (2)**.

![Enter the T1 image path in the Load Volume dialog, then click OK](/static/tutorials/structural_imaging/freesurfer/freeview-load-volume-guide.png)

The image appears in sagittal, coronal and axial views, with a 3D view at the bottom right. Click within an anatomical view: the other slices follow the selected location, and the **Cursor** panel reports its coordinates and image value.

![The bundled anatomical image displayed in Freeview](/static/tutorials/structural_imaging/freesurfer/freeview-anatomy.png)

### 2. Add the segmentation

Choose **File → Load Volume…** again. Paste this path into **Select volume file (1)**:

```text
/opt/freesurfer-8.2.0/subjects/fsaverage/mri/aparc+aseg.mgz
```

Keep **Sample method → Nearest neighbor** selected. Set **Color map → Lookup Table (2)** and leave **Look up table → FreeSurferColorLUT**. Click **OK (3)**.

![Load the segmentation using the FreeSurfer colour lookup table](/static/tutorials/structural_imaging/freesurfer/freeview-load-segmentation-guide.png)

This file contains anatomical label numbers. The lookup table gives those labels distinct colours; nearest-neighbour sampling preserves the label values.

### 3. Inspect a labelled structure

Select **aparc+aseg** in the left-hand **Volumes** list. Its checkbox **(1)** hides or shows the overlay. Set **Opacity (2)** to **0.35** so the underlying T1 image remains visible.

Click a coloured structure in a slice and read the **aparc+aseg** row in the **Cursor** panel **(3)**. The screenshot shows label **51, Right-Putamen**; a different location will show a different label. If the panel is too small, drag its upper divider upward.

![Toggle the segmentation, adjust its opacity and read the clicked structure name](/static/tutorials/structural_imaging/freesurfer/freeview-segmentation-guide.png)

### 4. Add a cortical surface

Choose **File → Load Surface…**. In the file chooser, enter this path in **File name (1)**, then click **Open (2)**:

```text
/opt/freesurfer-8.2.0/subjects/fsaverage/surf/lh.pial
```

You can also select **lh.pial** from the displayed `surf` folder, as shown below. The surface appears under **Surfaces** in the left panel.

![Select the left-hemisphere pial surface and open it](/static/tutorials/structural_imaging/freesurfer/freeview-select-surface-guide.png)

### 5. Explore the surface in 3D

1. Clear the two **Volumes** checkboxes **(1)**, leaving **Surfaces → lh.pial** checked.
2. Click the **Single View** toolbar button **(2)**.
3. Click the **3D view** button, shown as a grey head **(3)**.
4. Drag within the 3D pane to rotate the surface and inspect its folds.

For the clean view shown here, turn off **View → Show Cursor** and **View → Show Slice Frames (3D View)**. These display options do not change the data.

![Show only the cortical surface in a single 3D pane](/static/tutorials/structural_imaging/freesurfer/freeview-surface-guide.png)

## What you have checked

You have opened the bundled anatomy, displayed its segmentation with named structures, and rotated a cortical surface. This is a viewing exercise using existing demonstration outputs. To inspect your own FreeSurfer results, repeat the same steps with files from your subject's `mri/` and `surf/` folders.

For more display options and guidance on inspecting reconstruction outputs, see the official [Freeview guide](https://surfer.nmr.mgh.harvard.edu/fswiki/FreeviewGuide/FreeviewIntroduction) and [FreeSurfer output-viewing tutorial](https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/OutputData_freeview).
