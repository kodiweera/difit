.. image:: ../logo.png
    :width: 400
    :align: center
    :alt: ReadTheDocs
    :target: https://difit.readthedocs.io/en/stable/

*difit*: **A diffusion MRI models fitting software**
====================================================

*difit* is being developed as an attempt to bring in major diffusion models into one place (*v1.0.0* can do DTI and DKI models). *difit* allows to choose b-values and b0-images from multi-shell data as the user desires. This enable the user to test different combinations easily without splitting data prior to the model fitting.

Major software packages in the background
-----------------------------------------
*difit's* versions of DTI and DKI models come from `dipy <https://dipy.org/>`_. Nodes were built using `nipype <https://nipype.readthedocs.io/en/latest/>`_. Other dependancies are listed in the setup.cfg file. 

Installation
------------
``pip install difit``

Models fitting command
-------------------------

DTI
***
``python -m difit 'path/to/input/dir' 'path/to/output/dir' 'path/to/work/dir' --models dti --dti_b_values 1000 --dti_b0_images 3 --mem 6 --nprocs 2``

DKI
***
``python -m difit 'path/to/input/dir' 'path/to/output/dir' 'path/to/work/dir' --models dki --dki_b_values 500 1000 3000 --dki_b0_images 4 --mem 9 --nprocs 2``

Both DTI and DKI
****************
It is possible to fit more than one model in one run. DTI followed by DKI will be fitted with the below command.

``python -m difit 'path/to/input/dir' 'path/to/output/dir' 'path/to/work/dir' --models dti dki --dki_b_values 500 1000 2000 --dki_b0_images 3 --dti_b_values 1000 --dti_b0_images 3 --mem 12 --nprocs 2``


Parallel Processing
---------------------
difit can fit multiple subjects in parallel. If you have more than one subject, you can issue the command similar to below with the wildcard (*). If you want to fit few of the available subjects, you can use the curly bracket notaions to specify the subjects.

``python -m difit 'path/to/input/sub*/data' 'path/to/output/sub*/out' 'path/to/work/dir' --models dti dki --dki_b_values 500 1000 2000 --dki_b0_images 3 --dti_b_values 1000 --dti_b0_images 3 --mem 32 --nprocs 8``

Input dwi data files
---------------------

*difit* searches for files ending with `*_dwi.nii.gz`, `*_dwi.bval`, `*_dwi.bvec` and `*_mask.nii.gz` in the input directory. Make sure to name your files with the same endings. If you use `qsiprep <https://qsiprep.readthedocs.io/en/latest/installation.html>`_ to preprocess data, you will end up with the above format which uses `BIDS <https://bids.neuroimaging.io/>`_  convention. If you used a different software to preprocess your data, name your files to match the above convention. The `*` indicate any name/s before the underscore can take place.


An example for multi models and multi subjects parallel processing
******************************************************************
Assume there are two subject directories namely **sub01** and **sub02** and in each directory there are *data* and *out* directories available. In this example, diffusion data have four shells (500,1000,2000,3000) and 6 b0 images. But we are going to use only one shell for DTI and three shells for DKI model. The both models will use 3 b0 images (consecutive).

::

 projectdifit
    ├── sub01
    │   ├── data
    │   │   ├── example_dwi.bval
    │   │   ├── example_dwi.bvec
    │   │   ├── example_dwi.nii.gz
    │   │   └── example_mask.nii.gz
    │   └── out
    ├── sub02
    │   ├── data
    │   │   ├── example_dwi.bval
    │   │   ├── example_dwi.bvec
    │   │   ├── example_dwi.nii.gz
    │   │   └── example_mask.nii.gz
    │   └── out
    └── work


``python -m difit '/projectdifit/sub*/data' '/projectdifit/sub*/out' '/projectdifit/work' --models dti dki --dki_b_values 500 1000 2000 --dki_b0_images 3 --dti_b_values 1000 --dti_b0_images 3 --mem 32 --nprocs 8``

Output files
************
::

    out
    ├── dki
    │   ├── AK.nii.gz
    │   ├── dki_AD_mosaic.png
    │   ├── dki_AD.nii.gz
    │   ├── dki_AK_mosaic.png
    │   ├── dki_FA_mosaic.png
    │   ├── dki_FA.nii.gz
    │   ├── dki_kFA_mosaic.png
    │   ├── dki_MD_mosaic.png
    │   ├── dki_MD.nii.gz
    │   ├── dki_MK_mosaic.png
    │   ├── dki_RD_mosaic.png
    │   ├── dki_RD.nii.gz
    │   ├── dki_RK_mosaic.png
    │   ├── dki_summary_plots.html
    │   ├── kFA.nii.gz
    │   ├── MK.nii.gz
    │   └── RK.nii.gz
    └── dti
        ├── dti_AD_mosaic.png
        ├── dti_AD.nii.gz
        ├── dti_FA_mosaic.png
        ├── dti_FA.nii.gz
        ├── dti_MD_mosaic.png
        ├── dti_MD.nii.gz
        ├── dti_RD_mosaic.png
        ├── dti_RD.nii.gz
        └── dti_summary_plots.html


*difit* creates **dti** and **dki** directories in the out directory to store the above output files for each subject.

HELP
*****
``python -m difit -h``

::

    dmri models fitter work flow

    positional arguments:
      input_dir             Input data directory. This directory must contain *_dwi.nii.gz, *_mask.nii.gz, *_dwi.bval,
                        *_dwi.bvec. Multiple subjects can be list with wild cards e.g. ~/data/sub_*/data ; each
                        subject directory contain its own set of diffusion files.

      output_dir            The output directory for models metrices. In this directory seperate subdirectories will be
                        created for each model; For multiple subjects, output can be given with a wildcard e.g.
                        ~/data/sub_*/out

      work_dir              directory for intermediate results

   optional arguments:
      -h, --help            show this help message and exit
      --models MODELS [MODELS ...]
                        Choose the model or models you want to fit to your data. Choose one or a combination from dti,
                        dki (default: None)

   Options for choosing shell numbers for DTI processing:
      --dti_b_values DTI_B_VALUES [DTI_B_VALUES ...]
                        Choose a b-value/s of multishell data to use for DTI model fitting (default: None)
      --dti_b0_images DTI_B0_IMAGES
                        If dwi data contain more than one b0 images, choose how many you want to use for DTI model
                        fitting (default: 1)

   Options for choosing shell numbers and b0 images for DKI processing:
      --dki_b_values DKI_B_VALUES [DKI_B_VALUES ...]
                        Choose a b-values of multishell data to use for DKI model fitting (default: None)
      --dki_b0_images DKI_B0_IMAGES
                        If dwi data contain more than one b0 images, choose how many you want to use for DKI model
                        fitting (default: 1)

   Options to specify computer resources:
      --nprocs NPROCS       maximum number of cpus across all processes (default: None)
      --omp-nthreads OMP_NTHREADS
                        maximum number of threads per-process (default: None)
      --mem MEMORY_GB       upper bound memory limit (GB) for difit models fitting (default: None)
      --use-plugin FILE     nipype plugin configuration file (default: None)

Future Additions
****************
*MSMT-CSD particle filtering tractography*, *NODDI* and *FSL PROBTRACKX*. 


Note
****

This project has been set up using PyScaffold 4.1. For details and usage
information on PyScaffold see https://pyscaffold.