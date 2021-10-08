
from .. workflows.bin import config
from os import path
from ..workflows.dti import dti_wf
from ..workflows.dki import dki_wf
import gc
from multiprocessing import Process, Manager, set_start_method
import platform

if platform.system() == 'Linux':
    set_start_method('forkserver') 

def main():
    """Initiating the program."""
    from pathlib import Path
    import sys
    import gc
    from .parser import parse_args
    
    parse_args()

# Saving config file in case to load for a child/forserver process

#print("Printing work_dirs: " + str(config.Out_work_dirs.workdirs))
    #if len(config.Output.workdir) > 1:
    #    config_file = path.join(str(config.Output.workdir[0]) + '/' + "config.toml")
    #    config.save_config(config_file)
    
    #if len(config.Output.workdir) == 1:
    if isinstance(config.Output.workdir, str):
        config_file = path.join(str(config.Output.workdir) + '/' + "config.toml")
        config.save_config(config_file)
    else:
        config_file = path.join(config.Output.workdir[0] + '/' + "config.toml")
        config.save_config(config_file)

#    print(config_file)
    # print("models---------")
    # print( config.Moptions.models)
    # print("b0-images---------")
    # print(config.Moptions.dti_b0_images)
    # print("b-values---------")
    # print(config.Moptions.dti_b_values)
    # print(config.Output.logdir)

# run dti workflow
    if 'dti' in config.Moptions.models:
        with Manager() as mgr:
                        
            p = Process(dti_wf())
            p.start()
            p.join()
              
        gc.collect()
# run dki workflow
    if 'dki' in config.Moptions.models:
        with Manager() as mgr:
        
            p = Process(dki_wf())
            p.start()
            p.join()
 #dki_workf.write_graph(graph2use='exec')
        gc.collect()



if __name__ == "__main__":
    raise RuntimeError(
        "dmri-models-fitter/client/run.py should not be run directly;\n"
        "Please `pip install` dmri-models-fitter and use the `dmri-models-fitter` command"
    )