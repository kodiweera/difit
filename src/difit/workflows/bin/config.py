# Intitiall created on 8/24/2021 by Chandana Kodiweera, Dartmouth Brain Imagng Center
""" Common configuration for all models"""

import os
#from multiprocessing import set_start_method

#try:
 #   set_start_method("forkserver")
#except RuntimeError:
#    pass 
#finally:
import sys
import random
from uuid import uuid4
from time import strftime
from pathlib import Path
from nipype import __version__ as _nipype_ver
from os import path, mkdir
from nipype import SelectFiles, Node


#CONFIG_FILENAME = "difit.toml"

class _ArgsConfig:
    """Arguments getter and setter"""

    _dirs = tuple()

    def __init__(self):
        """Don't run stand alone"""
        raise RuntimeError("Not callable")

    @classmethod
    def setter(cls, argsdict, init=True, ignore=None):
        """Assigning user inputs to class attributes"""
        ignore = ignore or {}
        for k, v in argsdict.items():
            if k in ignore or v is None:
                continue
            if k in cls._dirs:
                setattr(cls, k, Path(v).absolute())
            elif hasattr(cls, k):
                setattr(cls, k, v)

        if init:
            try:
                cls.init()
            except AttributeError:
                pass

    @classmethod
    def getter(cls):
        """Obtaining assinged settings such as class attributes."""
        
        out = {}
        for k, v in cls.__dict__.items():
            if k.startswith("_") or v is None:
                continue
            if callable(getattr(cls, k)):
                continue
            if k in cls._dirs:
                v = str(v)
            out[k] = v
        return out


class Input(_ArgsConfig):
    input = None
    dwi = None
    bval = None
    bvec = None
    mask = None

    _dirs = ("input_dir")

    @classmethod
    def init(cls):
        """Set input data files for lists of dwi, bval, bvec and mask"""
        #from os import path
        #from nipype import SelectFiles, Node
        
        template = {'dwi': path.join(str(cls.input_dir) + '/' + '*_dwi.nii.gz'), 'bval': path.join(str(cls.input_dir) + '/' + '*_dwi.bval'), 
        'bvec': path.join(str(cls.input_dir) + '/' + '*_dwi.bvec'), 'mask': path.join(str(cls.input_dir) + '/' + '*_mask.nii.gz')}

        # Create SelectFiles node
        sf = Node(SelectFiles(template),
          name='Select-dwi-input-files')
        datafiles = sf.run().outputs
        cls.dwi = datafiles.dwi
        cls.bval = datafiles.bval
        cls.bvec = datafiles.bvec
        cls.mask = datafiles.mask

# configuration of output directories and work directories 

class Output(_ArgsConfig):
    output_dir = None
    work_dir = None
    outdir = None
    workdir = None
    logdir = None
    log_dir = None

    _dirs = ("output_dir", "work_dir")

    
    @classmethod
    def init(cls):
        
        template = {'outdirs':str(cls.output_dir), 'workdirs':str(cls.work_dir)}

        sf = Node(SelectFiles(template),
          name='output-and-work-directories')
        dirs = sf.run().outputs
        cls.outdir = dirs.outdirs
        cls.workdir = dirs.workdirs
        
        if isinstance(dirs.workdirs, str):
            cls.logdir = dirs.workdirs
        else:
            cls.logdir = dirs.workdirs[0]

        # create the log directory in the work directory
        cls.log_dir = path.join(cls.logdir, 'log')
        if not path.exists(cls.log_dir):
            mkdir(cls.log_dir)


class Moptions(_ArgsConfig):
    """Setting models options from user requests"""
    models = None
    dti_b_values = None
    dti_b0_images = None
    dki_b_values = None
    dki_b0_images = None



class Nipype(_ArgsConfig):
    """Nipype Settings"""

    crashfile_format = "txt"
    """ format for crashfiles"""
    get_linked_libs = False
    memory_gb = None
    nprocs = os.cpu_count()
    omp_threads = None
    plugin = "MultiProc"
    """ Execution plugin for Nipype"""
    plugin_args = {"maxtaskperchild" : 1,
                   "raise_insufficient": False,
                   }
    resource_monitor = False
    stop_on_first_crash = True

    @classmethod
    def init(cls):
        """Setting Nipype Configurations"""
        from nipype import config as npcfg

        if cls.resource_monitor:
            npcfg.update_config(
                {
                    "monitoring": {
                        "enabled": cls.resource_monitor,
                        "sample_frequency": "0.5",
                        "summary_append": True
                    }
                }
            )
            npcfg.enable_resource_monitor()


        # log and execution
        npcfg.update_config(
            {
                "execution":{
                    "crashdump_dir": str(Output.log_dir),
                    "crashfile_format":cls.crashfile_format,
                    "get_linked_libs": cls.get_linked_libs,
                    "stop_on_first_crash": cls.stop_on_first_crash,
                    "check_version": False,
                }
            }
        )
            
        if cls.omp_threads is None:
            cls.omp_threads = min(
                cls.nprocs - 1 if cls.nprocs > 1 else os.cpu_count(), 8
            )

    @classmethod
    def get_plugin(cls):
        """dictionary input for nipype workflow run"""
        out = {
            "plugin": cls.plugin,
            "plugin_args": cls.plugin_args,
        }
        if cls.plugin in ("MultiProc", "LegacyMultiProc"):
            out["plugin_args"]["n_procs"] = int(cls.nprocs)
            if cls.memory_gb:
                out["plugin_args"]["memory_gb"] = float(cls.memory_gb)
        return out


        

def loader(argsDict):
    """Read user inputs from a flat dictionary."""
    Input.setter(argsDict)
    Moptions.setter(argsDict)
    Output.setter(argsDict)
    Nipype.setter(argsDict)

# Storing configuration file in toml ( Tom's mark down file) fromat

def scoupsettings(flat=False):
    """Collecting settings as a dictionary"""
    settings = {"Input": Input.getter(),
                "Output": Output.getter(),
                "Moptions": Moptions.getter(),
                "Nipype" : Nipype.getter()
                }
    
    return settings
    
def totoml():
    """Convert settings to toml format"""
    from toml import dumps

    return dumps(scoupsettings())

def save_config(filename):
    """ Save config file"""
    filename = Path(filename)
    filename.write_text(totoml())

def read_saved_config(filename, skip=None):
    """ Read and load settings from a saved conig file"""
    from toml import loads
    settings = loads(filename.read_text())
    for sectionname, configs in settings.items():
        section = getattr(sys.modules[__name__], sectionname)
        ignore = skip.get(sectionname)
        section.load(configs, ignore=ignore)
     



    

              