---
title: Connectome Workbench
linkTitle: Connectome Workbench
weight: 1
tags:
- Connectome Workbench
- functional imaging
aliases:
- /static/tutorials/functional_imaging/connectomeworkbench
description: A tutorial for accessing and visualizing the 7T HCP Retinotopy Dataset
  on Connectome Workbench.
authors:
- name: Fernanda L. Ribeiro
- name: "Mich\xE8le Masson-Trottier"
date: '2026-10-21'
execute:
  skip: true
doi: 10.5281/zenodo.18718440
github: https://github.com/neurodesk/neurodeskedu/blob/main/books/tutorials/functional_imaging/connectomeWorkbench.md
edit_url: https://github.com/neurodesk/neurodeskedu/edit/main/books/tutorials/functional_imaging/connectomeWorkbench.md
downloads:
- url: /edu/_sources/tutorials/functional_imaging/connectomeWorkbench.md
  title: Download source
  filename: connectomeWorkbench.md
  static: false
---
# Connectome Workbench




:::{admonition} Learning Objectives
:class: tip

By the end of this tutorial you will be able to:

- Download and open an HCP retinotopy scene.
- Switch between group and participant maps.
- Compare polar angle, eccentricity, pRF size and myelin maps.
:::


A tutorial for accessing and visualizing the 7T HCP Retinotopy Dataset on Connectome Workbench.

> _This tutorial was created by Fernanda L. Ribeiro._ 
>
> Email: fernanda.ribeiro@uq.edu.au
>
> Github: \@felenitaribeiro
>
> Twitter: \@NandaRibeiro93
>
<!-- Fill in your personal details above so that we can credit the tutorial to you. Feel free to add any additional contact details i.e. website, or remove those that are irrelevant -->

This tutorial documents how to use Connectome Workbench on neurodesk for visualizing the 7T HCP Retinotopy Dataset. 

[Getting Set Up with Neurodesk](https://neurodesk.org/getting-started/)

## Download data

1. Review the [HCP Open Access data-use terms](https://www.humanconnectome.org/study/hcp-young-adult/data-use-terms) and register for a [BALSA account](https://balsa.wustl.edu/) if you do not already have one.

2. In **Firefox inside Neurodesk**, open the [HCP 7T Retinotopy study](https://balsa.wustl.edu/study/9Zkk), sign in and click **Download**. Downloading inside Neurodesk places the archive in the instance, where Workbench can access it.

3. The full study is about 7.75 GB. This walkthrough uses `Retinotopy_HCP_7T_181_Fit1.scene`, available with its required data as an approximately 650 MB selection. In the download dialog, follow the numbered targets:

   **1** Clear the checkbox beside the study title. **2** Select `Retinotopy_HCP_7T_181_Fit1.scene` to include all of its scenes and data. **3** Click **Download Selected**.

![Select the Fit1 scene and download its required files](/static/tutorials/functional_imaging/connectomeworkbench/download-fit1-annotated.svg)

These files contain preprocessed group and individual maps from 181 participants, including retinotopic, curvature, midthickness and myelin maps.

4. In Firefox’s download panel, click the folder icon beside the completed download to open **Downloads**. **1** Right-click the ZIP file, then **2** choose **Extract Here**. Keep the scene file and the accompanying data folders together; Workbench uses their relative paths.

![Right-click the ZIP archive and select Extract Here](/static/tutorials/functional_imaging/connectomeworkbench/extract-archive-annotated.svg)


## Visualizing scene files

Using Connectome Workbench, you can load ".scene" files and visualize all individuals' retinotopic maps. 
To do so, follow the next steps:

1. In the application menu, navigate to **1** Neurodesk → **2** Functional Imaging → **3** connectomeworkbench → **4** connectomeworkbench 1.5.0

![Follow the four numbered menu targets to launch Workbench 1.5.0](https://raw.githubusercontent.com/neurodesk/media/neurodesk-shared-gui-controls-2026-10-20/screenshots/neurodesk/launch-workbench-guide.png)

2. On the terminal shell that pops up, type in:

```bash
wb_view
```

![Type wb_view in the Workbench container terminal](/static/tutorials/functional_imaging/connectomeworkbench/start-viewer.jpg)


3. Click **Open Other**, marked **1** below.

![Workbench startup dialog with Open Other at the bottom](/static/tutorials/functional_imaging/connectomeworkbench/open-other-annotated.svg)

In the file chooser, **1** change **Files of type** from **Specification Files** to **Scene Files**. Otherwise the scene is hidden.

Navigate into the extracted archive, then follow:

```text
S1200_7T_Retinotopy181/MNINonLinear/fsaverage_LR32k/
```

**2** Select `Retinotopy_HCP_7T_181_Fit1.scene`, then **3** click **Open**.

![Set the Scene Files filter, select the Fit1 scene and click Open](/static/tutorials/functional_imaging/connectomeworkbench/select-scene-annotated.svg)

4. In the **Scenes** window, **1** select the first scene, **Spheres: Group avg Angle (0–360), Eccentricity, pRF, Myelin**, then **2** click **Show**.

![Select the first group-average scene and click Show](/static/tutorials/functional_imaging/connectomeworkbench/show-scene-annotated.svg)

The default scene displays the group-average maps.

5. To show individual participants, **1** open the **File** dropdown on the first checked overlay row in the **Overlay ToolBox**. In this scene that row contains the polar-angle map; the unchecked R² row above it is a different layer.

![Group-average maps with the first checked overlay's File control marked](/static/tutorials/functional_imaging/connectomeworkbench/group-average-annotated.svg)

**2** Select `S1200_7T_Retinotopy181.All.Fit1_PolarAngle_MSMAll.32k_fs_LR.dscalar.nii`. The `All` file contains the individual-participant maps.

![Select the All.Fit1_PolarAngle file](/static/tutorials/functional_imaging/connectomeworkbench/choose-individual-file-annotated.svg)

6. On the same overlay row, **1** enter a map index or **2** select a map from the name dropdown. Index **1** is participant **100610**. The polar-angle spheres at the top left now show that participant; the other variables remain group averages until you change their tabs too.

![Map index and map-name dropdown for participant 100610](/static/tutorials/functional_imaging/connectomeworkbench/individual-map-1-annotated.svg)

Set the index to **5** and press **Enter** to show participant **105923**:

![Participant 105923 at map index 5](/static/tutorials/functional_imaging/connectomeworkbench/individual-map-5.jpg)

7. Use the tabs at the top, marked **1**, to repeat the file and map selection for the other variables. Choose the file containing the following stem; each begins with `S1200_7T_Retinotopy181.` and ends with `.32k_fs_LR.dscalar.nii`.

| Tab | Individual-participant file stem |
| --- | --- |
| Eccentricity | `All.Fit1_Eccentricity_MSMAll` |
| pRF size | `All.Fit1_ReceptiveFieldSize_MSMAll` |
| Myelin | `All.MyelinMap_BC_MSMAll` |

Set map index **5** in each tab and check that its map name begins with **105923**. The view below shows all four variables for that participant.

![Use the map tabs to display all four variables for participant 105923](/static/tutorials/functional_imaging/connectomeworkbench/other-maps-annotated.svg)
