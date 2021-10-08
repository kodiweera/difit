"""parser"""

from .. workflows.bin import config

def _build_parser():
    """Build parser object."""
    from functools import partial
    from pathlib import Path
    from argparse import (
	ArgumentParser,
	ArgumentDefaultsHelpFormatter,
   )

    def _path_exists(path, parser):
	    """Ensure the path exists."""
	    if path is None or not Path(path).exists():
		    raise parser.error(f"The path does not exist: <{path}>.")
	    return Path(path).absolute()

    def _is_file(path, parser):
	    """Makesure the given path exists and it's a file."""
	    path = _path_exists(path, parser)
	    if not path.is_file():
		    raise parser.error(f"The path should point to a file: <{path}>.")
	    return path

    parser = ArgumentParser(
	    description="dmri models fitter work flow",
	    formatter_class=ArgumentDefaultsHelpFormatter,
		)
    PathExists = partial(_path_exists, parser=parser)
    IsFile = partial(_is_file, parser=parser)

    parser.add_argument(
        "input_dir",
        action="store",
        type=Path,
        help="Input data directory. This directory must contain "
		"*_dwi.nii.gz, *_mask.nii.gz, *_dwi.bval, *_dwi.bvec. Multiple subjects can be list with wild cards"
        " e.g. ~/data/sub_*/data ; each subject directory contain its own set of diffusion files.",
    )

    parser.add_argument(
        "output_dir",
        action="store",
        type=Path,
        help="The output directory for models metrices. In this directory seperate subdirectories will be created for each model; For multiple subjects, output can be given with a wildcard"
        " e.g. ~/data/sub_*/out",
   )

    parser.add_argument(
        "work_dir",
        action="store",
        type=Path,
        help="directory for intermediate results",
    )

    parser.add_argument(
        "--models",
        nargs='+',
	    type=str,
        help="Choose the model or models you want to fit to your data."
                " Choose one or a combination from dti, dki ",
    )

    

   # DTI  options
    g_dti = parser.add_argument_group("Options for choosing shell numbers for DTI processing")
        
    g_dti.add_argument(
        "--dti_b_values",
	    nargs='+',
	    type=int,
        help="Choose a b-value/s of multishell data to use for DTI model fitting",
    )  

    g_dti.add_argument(
        "--dti_b0_images",
        type=int,
        default=1,
        help="If dwi data contain more than one b0 images, choose how many you want to use for DTI model fitting",
    )


    # DKI options

    # DTI  options
    g_dki = parser.add_argument_group("Options for choosing shell numbers and b0 images for DKI processing")
           
    g_dki.add_argument(
        "--dki_b_values",
	    nargs='+',
	    type=int,
        help="Choose a b-values of multishell data to use for DKI model fitting",
    )  

    g_dki.add_argument(
        "--dki_b0_images",
        type=int,
        default=1,
        help="If dwi data contain more than one b0 images, choose how many you want to use for DKI model fitting",
    )

    g_resources = parser.add_argument_group("Options to specify computer resources")
    g_resources.add_argument(
        "--nprocs",
        dest = 'nprocs',
        action = "store",
        type = int,
        help = "maximum number of cpus across all processes",
    )
    g_resources.add_argument(
        "--omp-nthreads",
        action = "store",
        type = int,
        help = "maximum number of threads per-process"
    )

    g_resources.add_argument(
        "--mem",
        dest="memory_gb",
        action = "store",
        help = "upper bound memory limit (GB) for difit models fitting"
    )

    
    g_resources.add_argument(
        "--use-plugin",
        action = "store",
        metavar = "FILE",
        type = IsFile,
        help = "nipype plugin configuration file"
    )



    return parser



#--------------------------

def parse_args(args=None, namespace=None):
    """Parse args preparation"""
    parser = _build_parser()
    options = parser.parse_args(args, namespace)
    config.loader(vars(options))
    


