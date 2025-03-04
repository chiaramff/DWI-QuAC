# DWI-QuAC
This repository contains scripts to run QC assessment of your diffusion MRI data and plot results into pdf files. 

## Table of Contents

- [Prerequisites](#prerequisites)
- [Running DWi-QuAC](#running-the-pre-processing-gui)
- [Usage Instructions](#usage-instructions)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Prerequisites
- **Freesurfer** > 7.4.0  
- **MRtrix3** > 3.0.3 

- **Seaborn** > 0.12.2
- **Matplotlib** > 3.8.0
- **Numpy** > 1.26.4
- **Nibabel** > 5.2.1
- **Pandas** > 2.1.4

Ensure FREESURFER environment is properly sourced:
source $FREESURFER_HOME/SetUpFreeSurfer.sh

## Usage instructions

This script performs a QA check of your dMRI data

Script assume bvec and bval to be named as data
If not. provide path to bvec and bval files
Syntax: ./dwi_qa.sh -i dmri_data [-e|o|b|r|h]

Arguments:
-h   Print this Help
-i   Input DWI data
-b   path to bval file
-r   path to bvec file
Options:
-o   path to output directory
-e   path to eddy output folder
-g   performs MRtrix gradients check
-s   provide subject id
-f   specify threshold for WM mask. Default=0.2
-q	  specify directory group QC outputs

Usage: dwiqa.sh -i input -r bvecs -b bvals

If no output directory is specified, a folder named dwi_qa is created in the current directory
If no eddy directory folder is provided, only one report is created that includes SNR measures and DTIFIT results.
If an eddy directory folder is provided, two additional reports are created that report eddy qc measures.

## Acknowledgements
Thanks to the development teams of Freesurfer, MRtrix3, and Miniforge3.
Special appreciation to the contributors who have made this pipeline possible.
