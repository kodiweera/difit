from . bin import config
from .inputnode import inputfiles
from os import path

def dti_wf():
    """dti workflow"""
    
    from nipype import Workflow, Node, Function
    
    # Load data

    def data_loading(fdwi, fbvals, fbvecs, fmask, foutdir):
        
        from dipy.io.image import load_nifti
        from dipy.io.image import load_nifti_data
        from dipy.io.gradients import read_bvals_bvecs
        import numpy as np
        dwi, affine = load_nifti(fdwi)
        mask = load_nifti_data(fmask)
        bvals, bvecs = read_bvals_bvecs(fbvals, fbvecs)
    

        return dwi, bvals, bvecs, mask, affine, foutdir

    data_node = Node(Function(
    input_names=['fdwi', 'fbvals','fbvecs','fmask','foutdir'],
            output_names=['dwi','bvals','bvecs','mask','affine','foutdir'],
                function=data_loading), 
                    name='load_data'
                                ) 

    # prepare dti
    
    def dti_prepare(dwi, bvals, bvecs, mask, affine, foutdir, B0, B_values):
        
        from dipy.core.gradients import gradient_table
        import numpy as np
        import gc
        
        outdir = foutdir  
        
        b0 = B0
           
        b0_images = np.array([False]*len(bvals))
        b0_logical = (bvals < 50)
    
        for i in range(len(b0_logical)):
            if np.count_nonzero(b0_images)<b0 and b0_logical[i]:
                b0_images[i] = True

         
        b_values = B_values    
        
        bval_num = len(b_values)
        shells = np.array([[False]*(len(bvals))]*bval_num)
    
        for k,p in zip(range(bval_num), b_values):
            shells[k] = np.logical_and(p-50 < bvals, bvals< p+50)
       
        dti_shell = np.array([False]*(len(bvals)))
    
        for l in shells:
            for m in range(len(bvals)):
                if l[m]:
                    dti_shell[m]= True
        
        for n in range(len(b0_images)):
            if b0_images[n]:
                dti_shell[n]=True

        dti_data = dwi[..., dti_shell]
        gtab = gradient_table(bvals[dti_shell], bvecs[dti_shell])
            
        del (dwi, dti_shell, b_values, bval_num)
        gc.collect()
        return dti_data, gtab, mask, affine, outdir

    dti_prep_node = Node(Function(
                    input_names=['dwi', 'bvals', 'bvecs', 'mask', 'affine', 'foutdir','B0','B_values'],
                    output_names=['dti_data', 'gtab', 'mask', 'affine', 'outdir'],
                    function=dti_prepare), 
                    name='dti_preparation'
                                )

    dti_prep_node.inputs.B0 = config.Moptions.dti_b0_images
    dti_prep_node.inputs.B_values = config.Moptions.dti_b_values


    def dti_model(dti_data, gtab, mask, affine, outdir):
        import dipy.reconst.dti as dti
        import gc

        tenmodel = dti.TensorModel(gtab)
        tenfit = tenmodel.fit(dti_data, mask=mask)
        dti_FA = tenfit.fa
        dti_MD = tenfit.md
        dti_AD = tenfit.ad
        dti_RD = tenfit.rd

        del (dti_data, gtab, mask, tenfit)
        gc.collect()
        return dti_FA, dti_MD, dti_AD, dti_RD, affine, outdir

    dti_model_node = Node(Function(
                    input_names=['dti_data', 'gtab', 'mask', 'affine', 'outdir'],
                    output_names=['dti_FA', 'dti_MD', 'dti_AD', 'dti_RD', 'affine', 'outdir'],
                    function=dti_model),
                    name='dti_model_fitter'
                            )

    def dti_save(dti_FA, dti_MD, dti_AD, dti_RD, affine, outdir):
        from dipy.io.image import save_nifti
        from os import path, mkdir
        import gc
        
        

        dti_dir = path.join(outdir, 'dti')

        if not path.exists(dti_dir):
            mkdir(dti_dir)
       
        save_nifti(path.join(outdir + '/dti/dti_FA.nii.gz'), dti_FA, affine)
        save_nifti(path.join(outdir + '/dti/dti_MD.nii.gz'), dti_MD, affine)
        save_nifti(path.join(outdir + '/dti/dti_AD.nii.gz'), dti_AD, affine)
        save_nifti(path.join(outdir + '/dti/dti_RD.nii.gz'), dti_RD, affine)

        del (dti_FA, dti_MD, dti_AD, dti_RD, affine)

        return outdir

    dti_save_node = Node(Function(
                    input_names=['dti_FA', 'dti_MD', 'dti_AD', 'dti_RD', 'affine', 'outdir'],
                    output_names=['outdir'],
                    function=dti_save),
                    name='dti_save_models'
                            )

    def dti_summary(outdir):
        from weasyprint import HTML, CSS
        from nilearn.plotting import plot_anat
        from os import path

        plot_anat(path.join(outdir + '/dti/dti_FA.nii.gz'), display_mode = 'mosaic', title='dti_FA',output_file=path.join(outdir + '/dti/dti_FA_mosaic.png'))
        plot_anat(path.join(outdir + '/dti/dti_MD.nii.gz'), display_mode = 'mosaic', title='dti_MD',output_file=path.join(outdir + '/dti/dti_MD_mosaic.png'))
        plot_anat(path.join(outdir + '/dti/dti_AD.nii.gz'), display_mode = 'mosaic', title='dti_AD',output_file=path.join(outdir + '/dti/dti_AD_mosaic.png'))
        plot_anat(path.join(outdir + '/dti/dti_RD.nii.gz'), display_mode = 'mosaic', title='dti_RD',output_file=path.join(outdir + '/dti/dti_RD_mosaic.png'))

        # summary html report
        page_title = 'Summary plots of DTI metrics'
        title_text = 'Sample plots of DTI metrics'
        text = 'This document presents sample plots of DTI metrics as a quick way to visually check your results.'
        fa = path.join(outdir + '/dti/dti_FA_mosaic.png')
        md = path.join(outdir + '/dti/dti_MD_mosaic.png')
        ad = path.join(outdir + '/dti/dti_AD_mosaic.png')
        rd = path.join(outdir + '/dti/dti_RD_mosaic.png')

        html = f'''
            <html>
                <head>
                    <title>{page_title}</title>
                </head>
                <body>
                    <h1>{title_text}</h1>
                    <br>
                    <p>{text}</p>
                    <br><br>
                    <img src={fa} alt='dti_fa' >
                    <br><br><br>
                    <img src={md} alt='dti_md' >
                    <br><br><br>
                    <img src={ad} alt='dti_ad' >
                    <br><br><br>
                    <img src={rd} alt='dti_rd' >
                    
                </body>
            </html>
            '''
        with open(path.join(outdir + '/dti/dti_summary_plots.html'), 'w') as f:
            f.write(html)

    dti_summary_node = Node(Function(
                    input_names=['outdir'],
                    output_names=['out'],
                    function=dti_summary),
                    name = 'dti_summary_plots'
                        )


    dti_workf = Workflow('dti')

    if isinstance(config.Output.workdir, str):
        dti_workf.base_dir = config.Output.workdir
    else:
        dti_workf.base_dir = config.Output.workdir[0]

    dti_workf.config['execution']['parameterize_dirs'] = False #avoid long name error

    # loading data_node

    inputnode = inputfiles()
    

    dti_workf.connect([(inputnode, data_node, [ ('fdwi','fdwi'), ('fbvals','fbvals'), ('fbvecs', 'fbvecs'), ('fmask','fmask'), ('foutdir', 'foutdir')])])

    dti_workf.connect([(data_node, dti_prep_node, [ ('dwi','dwi'), ('bvals','bvals'), ('bvecs', 'bvecs'), ('mask','mask'), ('affine','affine'), ('foutdir', 'foutdir')])])

    dti_workf.connect([(dti_prep_node, dti_model_node, [ ('dti_data','dti_data'), ('gtab','gtab'), ('mask', 'mask'), ('affine','affine'), ('outdir', 'outdir')])])

    
    dti_workf.connect([(dti_model_node, dti_save_node, [ ('dti_FA','dti_FA'), ('dti_MD','dti_MD'), ('dti_AD','dti_AD'), ('dti_RD','dti_RD'), 
                                                        ('affine','affine'), ('outdir', 'outdir')])])

    dti_workf.connect(dti_save_node, "outdir", dti_summary_node, "outdir")
       
    dti_workf.write_graph(graph2use='exec')
    dti_workf.run(**config.Nipype.get_plugin())
   

