import WORC
from WORC import BasicWORC
from classes import switch
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
import sys
from filestofastr import filetosources, filetosourceslocal
import glob
import json
import pandas as pd


# TODO:
# - Logger

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# Print the parent folder
filedir = os.path.dirname(os.path.realpath(__file__))

# Just make it for cluster environments
if 'xwan' in filedir:
    location = 'Cluster'
elif 'martijn' in filedir:
    location = 'PC'
elif 'mstar' in filedir:
    location = 'Cartesius'


fproject = 'MPNSTRadiomics'


def editconfig(config):
    config['General']['Segmentix'] = 'True'
    config['General']['AssumeSameImageAndMaskMetadata'] = 'True'
    config['General']['tempsave'] = 'True'

    config['Classification']['fastr'] = 'True'
    config['Classification']['fastr_plugin'] = 'DRMAAExecution'

    config['ImageFeatures']['image_type'] = 'MRI'

    config['Labels']['label_names'] = 'MPNST'
    config['Labels']['modus'] = 'singlelabel'


    ## Lines below are used for semantic model only!
    # config['SelectFeatGroup']['semantic_features'] = 'True'
    # config['SelectFeatGroup']['shape_features'] = 'False'
    # config['SelectFeatGroup']['histogram_features'] = 'False'
    # config['SelectFeatGroup']['orientation_features'] = 'False'
    # config['SelectFeatGroup']['texture_Gabor_features'] = 'False'
    # config['SelectFeatGroup']['texture_GLCM_features'] = 'False'
    # config['SelectFeatGroup']['texture_GLDM_features'] = 'False'
    # config['SelectFeatGroup']['texture_GLCMMS_features'] = 'False'
    # config['SelectFeatGroup']['texture_GLRLM_features'] = 'False'
    # config['SelectFeatGroup']['texture_GLSZM_features'] = 'False'
    # config['SelectFeatGroup']['texture_GLDZM_features'] = 'False'
    # config['SelectFeatGroup']['texture_NGTDM_features'] = 'False'
    # config['SelectFeatGroup']['texture_NGLDM_features'] = 'False'
    # config['SelectFeatGroup']['texture_LBP_features'] = 'False'
    # config['SelectFeatGroup']['dicom_features'] = 'False'
    # config['SelectFeatGroup']['vessel_features'] = 'False'
    # config['SelectFeatGroup']['phase_features'] = 'False'
    # config['SelectFeatGroup']['fractal_features'] = 'False'
    # config['SelectFeatGroup']['location_features'] = 'False'
    # config['SelectFeatGroup']['rgrd_features'] = 'False'
    # config['SelectFeatGroup']['original_features'] = 'True'
    # config['SelectFeatGroup']['wavelet_features'] = 'False'
    # config['SelectFeatGroup']['log_features'] = 'False'

   ## Lines below are used for shape / feature model only!
    # config['SelectFeatGroup']['shape_features'] = 'False'
    # config['SelectFeatGroup']['histogram_features'] = 'False'
    # config['SelectFeatGroup']['orientation_features'] = 'False'
    # config['SelectFeatGroup']['texture_Gabor_features'] = 'True'
    # config['SelectFeatGroup']['texture_GLCM_features'] = 'True'
    # config['SelectFeatGroup']['texture_GLDM_features'] = 'True'
    # config['SelectFeatGroup']['texture_GLCMMS_features'] = 'True'
    # config['SelectFeatGroup']['texture_GLRLM_features'] = 'True'
    # config['SelectFeatGroup']['texture_GLSZM_features'] = 'True'
    # config['SelectFeatGroup']['texture_GLDZM_features'] = 'True'
    # config['SelectFeatGroup']['texture_NGTDM_features'] = 'True'
    # config['SelectFeatGroup']['texture_NGLDM_features'] = 'True'
    # config['SelectFeatGroup']['texture_LBP_features'] = 'True'
    # config['SelectFeatGroup']['dicom_features'] = 'False'
    # config['SelectFeatGroup']['vessel_features'] = 'False'
    # config['SelectFeatGroup']['phase_features'] = 'False'
    # config['SelectFeatGroup']['fractal_features'] = 'False'
    # config['SelectFeatGroup']['location_features'] = 'False'
    # config['SelectFeatGroup']['rgrd_features'] = 'False'
    # config['SelectFeatGroup']['original_features'] = 'True'
    # config['SelectFeatGroup']['wavelet_features'] = 'False'
    # config['SelectFeatGroup']['log_features'] = 'False'

    return config


def selectsources(option, settings, name):
    # Change this for your personal settings
    filedir = os.path.dirname(os.path.realpath(__file__))

    # Just make it for cluster
    if 'xwan' in filedir:
        location = 'Cluster'
    elif 'mstarmans' in filedir:
        location = 'PC'
    elif 'mstar' in filedir:
        location = 'Cartesius'

    if location == 'Cluster':
        # Cluster
        filename = '/home/xwan/mstarmans/MPNST/MPNSTRadiomics_Review_All_220714_withsequences.csv'
        path = '/archive/mstarmans/Data/MPNSTRadiomics'
        # 
        label_file = '/home/xwan/mstarmans/MPNST/pinfo_MPNST.csv'

    print(name)
    network = WORC.WORC(name)
    network.labels_train.append(label_file)

    project = 'MPNSTRadiomics'
    url = 'xnat://bigr-rad-xnat.erasmusmc.nl'

    config = network.defaultconfig()
    config = editconfig(config)

    segmentation = 'Segmentation'

    labels = ['MPNST']
    if option in labels:
        label_data =\
            load_labels(pinfo, [option])

        segmentation = 'Segmentation'
        blacklist = []

        if settings['File'] == 'local':
            images_m1, metadata, segmentations_m1 =\
             filetosourceslocal(filename=filename,
                                segmentation=segmentation,
                                blacklist=blacklist,
                                path=path, project=fproject,
                                seriesname='T1')
        else:
            images_m1, metadata, segmentations_m1 =\
             filetosources(filename=filename,
                           project=project,
                           url=url,
                           segmentation=segmentation,
                           blacklist=blacklist,
                           seriesname='T1')

        images_m1, metadata, segmentations_m1 =\
            selectpatients(images_m1,
                           metadata,
                           segmentations_m1,
                           label_data)

        network.images_train.append(images_m1)
        network.segmentations_train.append(segmentations_m1)
        network.metadata_train.append(metadata)

        config = network.defaultconfig()
        config = editconfig(config)

        config['Labels']['label_names'] = option
        network.configs.append(config)

    elif 'Interactive' in option:
        # Interactive T1 segmentation experiment
        # First check all segmentations
        segmentations_T1 = glob.glob('/scratch/.../MPNST_T1/labels/Ibtissam/MPNSTRad*.nii.gz')
        segmentations_T1 = {os.path.splitext(os.path.splitext(os.path.basename(i))[0])[0]: i for i in segmentations_T1}
        
        # Empty segmentations, so blacklist
        blacklist = ['MPNSTRad-002_1', 'MPNSTRad-002_2', 'MPNSTRad-021_1']
        for b in blacklist:
            if b in segmentations_T1.keys():
                print(f"Blacklisted {b}.")
                del segmentations_T1[b]

        if 'OnlySufficient' in option:
            # Only select segmentations with a sufficient score
            scores = pd.read_csv('/scratch/.../MPNST_T1/results.csv')
            for pnum, pid in enumerate(scores['Sample']):
                if scores['Score'][pnum] not in ['Sufficient', 'Excellent']:
                    print(f"Deleted patient {pid}.")
                    for i in range(10):
                        key = f'{pid}'
                        if key in segmentations_T1.keys():
                            del segmentations_T1[pid]
                            
        # Only include images with a segmentations
        images_T1 = {k: f'/scratch/.../MPNST_T1/{k}.nii.gz' for k in segmentations_T1.keys()}
        
        network.images_train.append(images_T1)
        network.segmentations_train.append(segmentations_T1)
        network.metadata_train.append(metadata)

        config = network.defaultconfig()
        config = editconfig(config)
        network.configs.append(config)

    else:
        # Multimodal classification
        series = option.split('_')
        series1 = series[0]
        if len(series) == 2:
            series2 = series[1]
        elif len(series) == 3:
            series2 = series[1]
            series3 = series[2]
            
        segmentation = 'Segmentation'

        # Series 1
        def getsources(seriesnames):
            images = dict()
            metadata = dict()
            segmentations = dict()
            for seriesname in seriesnames:
                print(f"Selecting sources for series {seriesname}.")
                blacklist = []
                images_temp, metadata_temp, segmentations_temp =\
                filetosourceslocal(filename=filename,
                                    segmentation=segmentation,
                                    blacklist=blacklist,
                                    path=path, project=fproject,
                                    seriesname=seriesname,
                                    skipseg=True)

                # Exclude blacklisted scans
                blacklist = getblacklist([seriesname])
            
                for b in blacklist:
                    if b in images_temp.keys():
                        print(f"Blacklisted {b}.")
                        del images_temp[b]
                        del metadata_temp[b]
                        del segmentations_temp[b]

                # Get the registered segmentations
                segfolder = f"/archive/.../Output/WORC_MPNST_Registerto_{seriesname}_220914"
                if not os.path.exists(segfolder):
                    raise ValueError(f"Folder {segfolder} does not exist.")
                for key, value in segmentations_temp.items():
                    if value is None:
                        # Get a registered segmentation
                        searchterm = os.path.join(segfolder, "Elastix", f"seg*{key}*.nii.gz")
                        found_segmentations = glob.glob(searchterm)
                        if len(found_segmentations) != 1:
                            raise ValueError(f"Did not find one segmentation with {searchterm}, but {found_segmentations}.")
                        
                        segmentations_temp[key] = found_segmentations[0]

                # If we already have an m2, dont add it
                for k in images_temp.keys():
                    if k not in images.keys() or '#N/A' in images[k]:
                        # Patient not yet in there, or Patient is there, but with N/A
                        images[k] = images_temp[k]
                        metadata[k] = metadata_temp[k]
                        segmentations[k] = segmentations_temp[k]

            return images, metadata, segmentations

        images_m1, metadata_m1, segmentations_m1 = getsources(series1.split('+'))
        for k in images_m1.keys():
            images_m1[k] = images_m1[k].replace('vfs://data', '/archive/.../Data')
            segmentations_m1[k] = segmentations_m1[k].replace('vfs://data', '/archive/.../Data')
            metadata_m1[k] = metadata_m1[k].replace('vfs://data', '/archive/.../Data')

        #     print(k, images_m1[k], segmentations_m1[k])     

        # temp_dict = {'images': images_m1, 'segmentations': segmentations_m1}
        # with open('/home/mstarmans/RadTools/MPNST/MPNST_T2_Douwe.json', 'w') as fp:
        #         json.dump(temp_dict, fp, indent=4)

        # raise IOError
        if len(series) >= 2:
            images_m2, metadata_m2, segmentations_m2 = getsources(series2.split('+'))

            for k in images_m2.keys():
                images_m2[k] = images_m2[k].replace('vfs://data', '/archive/.../Data')
                segmentations_m2[k] = segmentations_m2[k].replace('vfs://data', '/archive/.../Data')
                metadata_m2[k] = metadata_m2[k].replace('vfs://data', '/archive/.../Data')

            # If series is not found, add dummy image
            for k, v in images_m1.items():
                if 'Dummy' not in k and k not in images_m2.keys():
                    # If m2 not present, the m1 image as a dummy
                    images_m2[k + '_Dummy'] = images_m1[k]
                    metadata_m2[k + '_Dummy'] = metadata_m1[k]
                    segmentations_m2[k + '_Dummy'] = segmentations_m1[k]

            # If series is not found, add dummy image
            for k, v in images_m2.items():
                if 'Dummy' not in k and k not in images_m1.keys():
                    # If m1 not present, the m2 image as a dummy
                    images_m1[k + '_Dummy'] = images_m2[k]
                    metadata_m1[k + '_Dummy'] = metadata_m2[k]
                    segmentations_m1[k + '_Dummy'] = segmentations_m2[k]
                
        if len(series) == 3:
            images_m3, metadata_m3, segmentations_m3 = getsources(series3.split('+'))
            
            for k in images_m3.keys():
                images_m3[k] = images_m3[k].replace('vfs://data', '/archive/.../Data')
                segmentations_m3[k] = segmentations_m3[k].replace('vfs://data', '/archive/.../Data')
                metadata_m3[k] = metadata_m3[k].replace('vfs://data', '/archive/.../Data')

            # If series is not found, add dummy image
            for k, v in images_m1.items():
                if 'Dummy' not in k and k not in images_m3.keys():
                    images_m3[k + '_Dummy'] = images_m1[k]
                    metadata_m3[k + '_Dummy'] = metadata_m1[k]
                    segmentations_m3[k + '_Dummy'] = segmentations_m1[k]

            for k, v in images_m2.items():
                if 'Dummy' not in k and k not in images_m3.keys():
                    images_m3[k + '_Dummy'] = images_m2[k]
                    metadata_m3[k + '_Dummy'] = metadata_m2[k]
                    segmentations_m3[k + '_Dummy'] = segmentations_m2[k]
                    
            # If series is not found, add dummy image
            for k, v in images_m3.items():
                if 'Dummy' not in k and k not in images_m1.keys() and k not in images_m2.keys():
                    # If not present in m1 and thus m2, add as Dummy image
                    images_m1[k + '_Dummy'] = images_m3[k]
                    metadata_m1[k + '_Dummy'] = metadata_m3[k]
                    segmentations_m1[k + '_Dummy'] = segmentations_m3[k]
                    images_m2[k + '_Dummy'] = images_m3[k]
                    metadata_m2[k + '_Dummy'] = metadata_m3[k]
                    segmentations_m2[k + '_Dummy'] = segmentations_m3[k]
        
        # raise IOError
        network.images_train.append(images_m1)
        network.segmentations_train.append(segmentations_m1)
        network.metadata_train.append(metadata_m1)

        config = network.defaultconfig()
        config = editconfig(config)
        network.configs.append(config)


        if len(series) >= 2:
            network.images_train.append(images_m2)
            network.segmentations_train.append(segmentations_m2)
            network.metadata_train.append(metadata_m2)
            network.configs.append(config)
            
        if len(series) == 3:
            network.images_train.append(images_m3)
            network.segmentations_train.append(segmentations_m3)
            network.metadata_train.append(metadata_m3)
            network.configs.append(config)

    return network, config


def main(options, names):
    # Change this for your personal settings
    tempdir_PC = '/Users/.../Desktop/mnt/'
    tempdir_cluster = '/archive/.../tmp'
    tempdir_cartesius = '/archive/.../tmp/'

    settings = dict()

    # Do you have the files locally?
    settings['File'] = 'local'

    # Use ring segmentation or normal?
    settings['Seg'] = 'Normal'

    for option, name in zip(options, names):
        network, config = selectsources(option, settings, name)

        if location == 'PC':
            tempdir = os.path.join(tempdir_PC, name)
            network.fastr_plugin = 'ProcessPoolExecution'
        elif location == 'Cluster':
            tempdir = os.path.join(tempdir_cluster, name)
            network.fastr_plugin = 'DRMAAExecution'
        else:
            tempdir = os.path.join(tempdir_cartesius, name)
            network.fastr_plugin = 'ProcessPoolExecution'

        network.fastr_tempdir = tempdir
        # network.set_tmpdir = tempdir
        network.build()
        network.add_evaluation(label_type=config['Labels']['label_names'])
        network.set()
        network.execute()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        options = ['MPNST']
        names = ['MPNST_200813']
    elif len(sys.argv) != 3:
        raise IOError("This function accepts two arguments")
    else:
        options = [str(sys.argv[1])]
        names = [str(sys.argv[2])]
    main(options, names)
