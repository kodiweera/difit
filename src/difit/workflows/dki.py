from . bin import config
from .inputnode import   inputfiles
def dki_wf():
    """dti workflow"""
    
    from nipype import Workflow, Node, Function


    # Load data

    # Load data

    def data_loading(fdwi, fbvals, fbvecs, fmask, foutdir):
        
        from dipy.io.image import load_nifti
        from dipy.io.image import load_nifti_data
        from dipy.io.gradients import read_bvals_bvecs
        import numpy as np
        dwi, affine = load_nifti(fdwi)
        mask = load_nifti_data(fmask)
        bvals, bvecs = read_bvals_bvecs(fbvals, fbvecs)
    #data = [dwi, bvals, bvecs, mask, affine, foutdir]

    #del (dwi, affine, mask, bvals, bvecs)

        return dwi, bvals, bvecs, mask, affine, foutdir

    data_node = Node(Function(
    input_names=['fdwi', 'fbvals','fbvecs','fmask','foutdir'],
            output_names=['dwi','bvals','bvecs','mask','affine','foutdir'],
                function=data_loading), 
                    name='load_data'
                                )
      
    
    def dki_prepare(dwi, bvals, bvecs, mask, affine, foutdir, B0, B_values):
        
        from dipy.core.gradients import gradient_table
        import numpy as np
        
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
       
        dki_shell = np.array([False]*(len(bvals)))
    
        for l in shells:
            for m in range(len(bvals)):
                if l[m]:
                    dki_shell[m]= True
        
        for n in range(len(b0_images)):
            if b0_images[n]:
                dki_shell[n]=True

        print("dki gradient indices done.")
       
        dki_data = dwi[..., dki_shell]

        print("dki data done.")

        gtab = gradient_table(bvals[dki_shell], bvecs[dki_shell])

        print("dki gradient table done.")
      
           
        return dki_data, gtab, mask, affine, outdir


    dki_prep_node = Node(Function(
                    input_names=['dwi', 'bvals', 'bvecs', 'mask', 'affine', 'foutdir','B0','B_values'],
                    output_names=['dki_data', 'gtab', 'mask', 'affine', 'outdir'],
                    function=dki_prepare), 
                    name='dki_preparation'
                                )

    dki_prep_node.inputs.B0 = config.Moptions.dki_b0_images
    dki_prep_node.inputs.B_values = config.Moptions.dki_b_values


    def dki_model(dki_data, gtab, mask, affine, outdir):
        import dipy.reconst.dki as dki
        dkimodel = dki.DiffusionKurtosisModel(gtab)
        dkifit = dkimodel.fit(dki_data, mask=mask)

        dki_FA = dkifit.fa
        dki_MD = dkifit.md
        dki_AD = dkifit.ad
        dki_RD = dkifit.rd

        MK = dkifit.mk(0, 3)
        AK = dkifit.ak(0, 3)
        RK = dkifit.rk(0, 3)
        kFA = dkifit.kfa


        del dkifit
        return dki_FA, dki_MD, dki_AD, dki_RD, MK, AK, RK, kFA, affine, outdir

    dki_model_node = Node(Function(
                    input_names=['dki_data', 'gtab', 'mask', 'affine', 'outdir'],
                    output_names=['dki_FA', 'dki_MD', 'dki_AD', 'dki_RD', 'MK', 'AK', 'RK', 'kFA', 'affine', 'outdir'],
                    function=dki_model),
                    name='dki_model_fitter'
                            )

    def dki_save(dki_FA, dki_MD, dki_AD, dki_RD, MK, AK, RK, kFA, affine, outdir):
        from dipy.io.image import save_nifti
        from os import path, mkdir

        dki_dir = path.join(outdir, 'dki')
        if not path.exists(dki_dir):
            mkdir(dki_dir)

        save_nifti(path.join(outdir + '/dki/dki_FA.nii.gz'), dki_FA, affine)
        save_nifti(path.join(outdir + '/dki/dki_MD.nii.gz'), dki_MD, affine)
        save_nifti(path.join(outdir + '/dki/dki_AD.nii.gz'), dki_AD, affine)
        save_nifti(path.join(outdir + '/dki/dki_RD.nii.gz'), dki_RD, affine)

        save_nifti(path.join(outdir + '/dki/MK.nii.gz'), MK, affine)
        save_nifti(path.join(outdir + '/dki/AK.nii.gz'), AK, affine)
        save_nifti(path.join(outdir + '/dki/RK.nii.gz'), RK, affine)
        save_nifti(path.join(outdir + '/dki/kFA.nii.gz'), kFA, affine)

        return outdir

    dki_save_node = Node(Function(
                    input_names=['dki_FA', 'dki_MD', 'dki_AD', 'dki_RD', 'MK', 'AK', 'RK', 'kFA', 'affine', 'outdir'],
                    output_names=['outdir'],
                    function=dki_save),
                    name='dki_save_models'
                            )

    def dti_summary(outdir):
        from weasyprint import HTML, CSS
        from nilearn.plotting import plot_anat
        from os import path

        plot_anat(path.join(outdir + '/dki/dki_FA.nii.gz'), display_mode = 'mosaic', title='dki_FA',output_file=path.join(outdir + '/dki/dki_FA_mosaic.png'))
        plot_anat(path.join(outdir + '/dki/dki_MD.nii.gz'), display_mode = 'mosaic', title='dki_MD',output_file=path.join(outdir + '/dki/dki_MD_mosaic.png'))
        plot_anat(path.join(outdir + '/dki/dki_AD.nii.gz'), display_mode = 'mosaic', title='dki_AD',output_file=path.join(outdir + '/dki/dki_AD_mosaic.png'))
        plot_anat(path.join(outdir + '/dki/dki_RD.nii.gz'), display_mode = 'mosaic', title='dki_RD',output_file=path.join(outdir + '/dki/dki_RD_mosaic.png'))
        plot_anat(path.join(outdir + '/dki/MK.nii.gz'), display_mode = 'mosaic', title='dki_MK',output_file=path.join(outdir + '/dki/dki_MK_mosaic.png'))
        plot_anat(path.join(outdir + '/dki/AK.nii.gz'), display_mode = 'mosaic', title='dki_AK',output_file=path.join(outdir + '/dki/dki_AK_mosaic.png'))
        plot_anat(path.join(outdir + '/dki/RK.nii.gz'), display_mode = 'mosaic', title='dki_RK',output_file=path.join(outdir + '/dki/dki_RK_mosaic.png'))
        plot_anat(path.join(outdir + '/dki/kFA.nii.gz'), display_mode = 'mosaic', title='dki_kFA',output_file=path.join(outdir + '/dki/dki_kFA_mosaic.png'))

        # summary html report
        page_title = 'Summary plots of DKI metrics'
        title_text = 'Sample plots of DKI metrics'
        text = 'This document presents sample plots of DKI metrics as a quick way to visually check your results.'
        dki_fa = path.join(outdir + '/dki/dki_FA_mosaic.png')
        dki_md = path.join(outdir + '/dki/dki_MD_mosaic.png')
        dki_ad = path.join(outdir + '/dki/dki_AD_mosaic.png')
        dki_rd = path.join(outdir + '/dki/dki_RD_mosaic.png')
        dki_mk = path.join(outdir + '/dki/dki_MK_mosaic.png')
        dki_ak = path.join(outdir + '/dki/dki_AK_mosaic.png')
        dki_rk = path.join(outdir + '/dki/dki_RK_mosaic.png')
        dki_kfa = path.join(outdir + '/dki/dki_kFA_mosaic.png')

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
                    <img src={dki_fa} alt='dti_fa' >
                    <br><br><br>
                    <img src={dki_md} alt='dti_md' >
                    <br><br><br>
                    <img src={dki_ad} alt='dti_ad' >
                    <br><br><br>
                    <img src={dki_rd} alt='dti_rd' >
                    <br><br><br>
                    <img src={dki_mk} alt='dti_fa' >
                    <br><br><br>
                    <img src={dki_ak} alt='dti_md' >
                    <br><br><br>
                    <img src={dki_rk} alt='dti_ad' >
                    <br><br><br>
                    <img src={dki_kfa} alt='dti_rd' >
                    
                </body>
            </html>
            '''
        with open(path.join(outdir + '/dki/dki_summary_plots.html'), 'w') as f:
            f.write(html)

    dki_summary_node = Node(Function(
                    input_names=['outdir'],
                    output_names=['out'],
                    function=dti_summary),
                    name = 'dti_summary_plots'
                        )

    dki_workf = Workflow('dki')

    if isinstance(config.Output.workdir, str):
        dki_workf.base_dir = config.Output.workdir
    else:
        dki_workf.base_dir = config.Output.workdir[0]

    dki_workf.config['execution']['parameterize_dirs'] = False #avoid long name error

    # loading data_node

    inputnode = inputfiles()


    dki_workf.connect([(inputnode, data_node, [ ('fdwi','fdwi'), ('fbvals','fbvals'), ('fbvecs', 'fbvecs'), ('fmask','fmask'), ('foutdir', 'foutdir')])])
    dki_workf.connect([(data_node, dki_prep_node, [ ('dwi','dwi'), ('bvals','bvals'), ('bvecs', 'bvecs'), ('mask','mask'),('affine','affine'), ('foutdir', 'foutdir')])])
    dki_workf.connect([(dki_prep_node, dki_model_node, [ ('dki_data','dki_data'), ('gtab','gtab'), ('mask', 'mask'), ('affine','affine'), ('outdir', 'outdir')])])
    dki_workf.connect([(dki_model_node, dki_save_node, [ ('dki_FA','dki_FA'), ('dki_MD','dki_MD'), ('dki_AD','dki_AD'), ('dki_RD','dki_RD'), 
                                                        ('MK','MK'), ('AK', 'AK'), ('RK','RK'), ('kFA', 'kFA'), ('affine','affine'), ('outdir', 'outdir')])])

    dki_workf.connect(dki_save_node, "outdir", dki_summary_node, "outdir")
        
    dki_workf.write_graph(graph2use='exec')
    dki_workf.run(**config.Nipype.get_plugin())
    