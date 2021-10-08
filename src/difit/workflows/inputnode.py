
from . bin import config


def inputfiles():
    from nipype import Node, IdentityInterface

# print("inputnode started")
    
    inputnode = Node(IdentityInterface(fields=['fdwi', 'fbvals','fbvecs','fmask','foutdir'], mandatory_inputs=True),
                                       name="inputnode")
# print("inputnode set done")

    if isinstance(config.Input.dwi, str):
        inputnode.inputs.fdwi = config.Input.dwi
        inputnode.inputs.fbvals = config.Input.bval
        inputnode.inputs.fbvecs = config.Input.bvec
        inputnode.inputs.fmask = config.Input.mask
        inputnode.inputs.foutdir = config.Output.outdir
        

    else:    
        inputnode.synchronize = True
        inputnode.iterables = [("fdwi",config.Input.dwi),("fbvals",config.Input.bval), 
                            ("fbvecs",config.Input.bvec), ("fmask", config.Input.mask),
                             ("foutdir", config.Output.outdir)]

    return inputnode