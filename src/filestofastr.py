from classes import switch
import json
import csv
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
import pandas as pd
import numpy as np
import glob


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def oldloadcsv():
    if case('.csv'):
        with open(filename, 'r+') as csv_file:
            reader = csv.reader(csv_file)
            # print(dir(reader))
            header = reader.next()

            Anon_ind = header.index('AnonID')
            session_ind = header.index('XNATSession')
            scan_ind = header.index(seriesname)
            taskstatus_ind = header.index('TaskStatus')
            segmentation_ind = header.index(segmentation)
            files = dict()

            pinfo = reader.next()
            while pinfo:
                taskstatus = pinfo[taskstatus_ind]
                if 'Done' in taskstatus:
                    task = dict()
                    task['segmentation'] = pinfo[segmentation_ind]
                    if task['segmentation'] != 'None' and task['segmentation'] != '':
                        task["experiment"] = pinfo[session_ind]
                        task["scan"] = pinfo[scan_ind]

                        # Create label
                        n = 0
                        subjectID = pinfo[Anon_ind] + '_' + str(n)
                        if subjectID in files.keys():
                            n = 1
                            while str(subjectID + '_' + str(n)) in files.keys():
                                n += 1

                            subjectID = str(subjectID + '_' + str(n))

                        files[subjectID] = task

                try:
                    pinfo = reader.next()
                except StopIteration:
                    pinfo = []


def dwicheck(nifti_files, mode):
    if 'high' in mode:
        # Check if there is a dwi_bhigh file
        highs = [i for i in nifti_files if 'high' in i]
        if len(highs) == 1:
            filename = highs[0]
        else:
            # No high in filename, look for highest B-value
            nifti_files = [i for i in nifti_files if i != 'dwi.nii.gz']
            bvalues = [int(i[5:-7]) for i in nifti_files]
            highest = bvalues.index(max(bvalues))
            filename = nifti_files[highest]
    elif 'low' in mode:
        # Check if there is a dwi_blow file
        lows = [i for i in nifti_files if 'low' in i]
        if len(lows) == 1:
            filename = lows[0]
        else:
            # No low in filename, look for lowest B-value
            nifti_files = [i for i in nifti_files if i != 'dwi.nii.gz']
            bvalues = [int(i[5:-7]) for i in nifti_files]
            lowest = bvalues.index(min(bvalues))
            filename = nifti_files[lowest]

    return filename


def filetosources(filename, project='CLMRadiomics',
                  url='xnat://bigr-rad-xnat.erasmusmc.nl',
                  segmentation='L_s1_Michel',
                  blacklist=[],
                  seriesname='SeriesID',
                  verbose=True):
    extension = os.path.splitext(filename)[1]
    for case in switch(extension):
        if case('.json'):
            with open(filename) as fp:
                files = json.load(fp)
            break

        if case('.csv'):
            with open(filename, 'r+') as csv_file:
                reader = csv.reader(csv_file)
                header = reader.next()

                Anon_ind = header.index('AnonID')
                session_ind = header.index('XNATSession')
                scan_ind = header.index(seriesname)
                taskstatus_ind = header.index('TaskStatus')
                segmentation_ind = header.index(segmentation)
                project_ind = header.index('Project')
                files = dict()

                pinfo = reader.next()
                while pinfo:
                    taskstatus = pinfo[taskstatus_ind]
                    if 'Done' in taskstatus:
                        task = dict()
                        task['segmentation'] = pinfo[segmentation_ind]
                        if task['segmentation'] != 'None' and task['segmentation'] != '':
                            task["experiment"] = pinfo[session_ind]
                            task["scan"] = pinfo[scan_ind]
                            task["project"] = pinfo[project_ind]

                            n = 0
                            subjectID = pinfo[Anon_ind]
                            while str(subjectID + '_' + str(n)) in list(files.keys()):
                                n += 1

                            subjectID = str(subjectID + '_' + str(n))

                            files[subjectID] = task

                    try:
                        pinfo = reader.next()
                    except StopIteration:
                        pinfo = []
            break

        else:
            print("No valid source file extension given!")

    subjectIDs = files.keys()
    subjectIDs = [x for x in subjectIDs if x not in blacklist]

    images = dict()
    metadatas = dict()
    segmentations = dict()
    # session = xnat.connect(url, verify=False)
    subjectIDs.sort()

    if project == 'Project':
        selectproject = True

    for i_patient in subjectIDs:
        i_patient = str(i_patient)
        data = files[i_patient]
        if '_' in i_patient:
            patientID = i_patient.split('_')[0]
        else:
            patientID = i_patient

        if str(data['segmentation']) != 'None':
            # Use DICOM as not all patients yet got nifti
            # TODO: Get this working with DICOM
            if selectproject:
                project = data['project']

            im = 'http://bigr-rad-xnat.erasmusmc.nl/data/archive/projects/' + project + '/subjects/' + patientID + '/experiments/' + str(data['experiment']) + '/scans/' + str(data['scan']) + '/resources/NIFTI'

            # Check if NIFTI exists
            if requests.get(im).status_code == 200:
                if verbose:
                    print(('Patient {}, found segmentation {} on session {}, scan {}').format(patientID, str(data['segmentation']), str(data['experiment']), str(data['scan'])))

                # Robustness to spaces in Excel
                data['segmentation'] = data['segmentation'].replace(' ', '')

                seg = 'http://bigr-rad-xnat.erasmusmc.nl/data/archive/projects/' + project + '/subjects/' + patientID + '/experiments/' + str(data['experiment']) + '/scans/' + str(data['scan']) + '/resources/PySNAP/files/' + str(data['segmentation'])
                if requests.get(seg).status_code == 200:
                    im = url + '/data/archive/projects/' + project + '/subjects/' + patientID + '/experiments/' + str(data['experiment']) + '/scans/' + str(data['scan']) + '/resources/NIFTI/files/image.nii.gz?insecure=true'
                    seg = url + '/data/archive/projects/' + project + '/subjects/' + patientID + '/experiments/' + str(data['experiment']) + '/scans/' + str(data['scan']) + '/resources/PySNAP/files/' + str(data['segmentation']) + '?insecure=true'
                    images[i_patient] = im
                    segmentations[i_patient] = seg

                    num = 0
                    success = False
                    while not success:
                        if num < 10:
                            mdurl = 'http://bigr-rad-xnat.erasmusmc.nl/data/archive/projects/' + project + '/subjects/' + patientID + '/experiments/' + str(data['experiment']) + '/scans/' + str(data['scan']) + ('/resources/DICOM/files/0000{}.dcm').format(num)
                            metadata = url + '/data/archive/projects/' + project + '/subjects/' + patientID + '/experiments/' + str(data['experiment']) + '/scans/' + str(data['scan']) + ('/resources/DICOM/files/0000{}.dcm?insecure=true').format(num)
                        else:
                            mdurl = 'http://bigr-rad-xnat.erasmusmc.nl/data/archive/projects/' + project + '/subjects/' + patientID + '/experiments/' + str(data['experiment']) + '/scans/' + str(data['scan']) + ('/resources/DICOM/files/000{}.dcm').format(num)
                            metadata = url + '/data/archive/projects/' + project + '/subjects/' + patientID + '/experiments/' + str(data['experiment']) + '/scans/' + str(data['scan']) + ('/resources/DICOM/files/000{}.dcm?insecure=true').format(num)

                        if requests.get(mdurl).status_code == 200:
                            success = True
                        else:
                            num += 1

                    metadatas[i_patient] = metadata
                else:
                    if verbose:
                        print(('Patient {}, invalid segmentation {} on session {}, scan {}').format(patientID, str(data['segmentation']), str(data['experiment']), str(data['scan'])))
            else:
                experimentID = data["experiment"]
                scanID = data["scan"]
                if verbose:
                    print("Patient " + patientID + ', sessions ' + experimentID + ', session ' + scanID + ' has no NIFTI.')

    if verbose:
        print("Found " + str(len(images.keys())) + ' patients with segmentation.')

    return images, metadatas, segmentations


def filetosourceslocal(filename,
                       segmentation='L_s1_Michel',
                       blacklist=[],
                       path='/media/martijn/DATA',
                       project='CLM',
                       seriesname='SeriesID',
                       verbose=True,
                       imagename='image.nii.gz',
                       taskstatus='TaskStatus',
                       use_sequence=False,
                       skipseg=False):
    extension = os.path.splitext(filename)[1]
    for case in switch(extension):
        if case('.json'):
            with open(filename) as fp:
                files = json.load(fp)
            break

        if case('.csv'):
            data = pd.read_csv(filename)
            taskstatus = data[taskstatus].values
            done_patients = [i for i in range(len(taskstatus)) if str(taskstatus[i]) in ['TRUE', 'True', 'Done']]

            files = dict()
            for i in done_patients:
                task = dict()
                task['experiment'] = data['XNATSession'].values[i]
                if segmentation != 'NotNeeded':
                    task['segmentation'] = data[segmentation].values[i]
                else:
                    task['segmentation'] = 'Skip'

                # Replace nan by None
                if not type(task['segmentation']) is str:
                    if np.isnan(task['segmentation']):
                        task['segmentation'] = 'None'

                task['Project'] = data['Project'].values[i]
                if imagename in list(data.keys()):
                    task['Filename'] = data[imagename].values[i]
                else:
                    task['Filename'] = imagename

                try:
                    task['scan'] = str(int(data[seriesname].values[i]))
                except ValueError:
                    # Probably a string inside the scan number or nan
                    task['scan'] = data[seriesname].values[i]

                n = 0
                subjectID = data['AnonID'].values[i]
                while str(subjectID + '_' + str(n)) in list(files.keys()):
                    n += 1

                subjectID = str(subjectID + '_' + str(n))

                if type(task['scan']) == str:
                    files[subjectID] = task
                elif not np.isnan(task['scan']):
                    files[subjectID] = task

            break

        else:
            print("No valid source file extension given!")

    # HCCAMS inphase
    if imagename == 'inphase':
        files_temp = dict()
        for k, v in files.iteritems():
            v['scan'] = str(int(v['scan']) - 1)
            v['Filename'] = 'image.nii.gz'
            v['segmentation'] = 'Skip'
            files_temp[k] = v
        imagename = 'image.nii.gz'
        files = files_temp

    subjectIDs = list(files.keys())
    subjectIDs.sort()
    subjectIDs = [x for x in subjectIDs if x not in blacklist]
    subjectIDs.sort()
    if verbose:
        print(("Found {} segmentations, selecting available ones.").format(len(subjectIDs)))

    images = dict()
    segmentations = dict()
    metadatas = dict()
    # session = xnat.connect(url, verify=False)
    for i_patient in subjectIDs:
        i_patient = str(i_patient)
        data = files[i_patient]
        if '_' in i_patient:
            patientID = i_patient.split('_')[0]
        else:
            patientID = i_patient

        if use_sequence:
            # Use sequence name in PatientID
            experimentname = data['experiment'].replace('MR', '')
            i_patient = i_patient[0:-2] + experimentname

        imagename = data['Filename']
        if str(data['segmentation']) != 'None':
            # Use DICOM as not all patients yet got nifti
            # TODO: Get this working with DICOM
            if 'BLT' in project:
                project = data['Project']
                im = os.path.join(os.path.dirname(path), project, patientID, str(data['experiment']), str(data['scan']), imagename)
            else:
                im = os.path.join(path, patientID, str(data['experiment']), str(data['scan']), imagename)

            if 'dwi' in imagename:
                # look for high b-value
                nifti_files = glob.glob(os.path.join(path, patientID, str(data['experiment']), str(data['scan']), 'dwi*.nii.gz'))
                print(os.path.join(path, patientID, str(data['experiment']), str(data['scan']), 'dwi*.nii.gz'))
                folder = os.path.dirname(nifti_files[0])
                nifti_files = [os.path.basename(i) for i in nifti_files]
                imagename = dwicheck(nifti_files, imagename)
                im = os.path.join(folder, imagename)

            # Check if NIFTI exists
            if os.path.isfile(im):

                # Robustness to spaces in Excel
                data['segmentation'] = data['segmentation'].replace(' ', '')

                if 'BLT' in project:
                    seg = os.path.join(os.path.dirname(path), project, patientID, str(data['experiment']), str(data['scan']), str(data['segmentation']))
                else:
                    seg = os.path.join(path, patientID, str(data['experiment']), str(data['scan']), str(data['segmentation']))

                if os.path.isfile(seg) or data['segmentation'] == 'Skip':
                    if verbose:
                        print(('Patient {}, found segmentation {} on session {}, scan {}').format(patientID, str(data['segmentation']), str(data['experiment']), str(data['scan'])))
                    im = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), imagename)
                    seg = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), str(data['segmentation']))

                    num = 0
                    success = False
                    while not success:
                        if num < 10:
                            if 'BLT' in project:
                                mdpath = os.path.join(os.path.dirname(path), project, patientID, str(data['experiment']), str(data['scan']), ('0000{}.dcm').format(num))
                            else:
                                mdpath = os.path.join(path, patientID, str(data['experiment']), str(data['scan']), ('0000{}.dcm').format(num))
                            metadata = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), ('0000{}.dcm').format(num))
                        else:
                            if 'BLT' in project:
                                mdpath = os.path.join(os.path.dirname(path), project, patientID, str(data['experiment']), str(data['scan']), ('000{}.dcm').format(num))
                            else:
                                mdpath = os.path.join(path, patientID, str(data['experiment']), str(data['scan']), ('000{}.dcm').format(num))
                            metadata = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), ('000{}.dcm').format(num))

                        if os.path.isfile(mdpath):
                            success = True
                        else:
                            num += 1

                    images[i_patient] = im
                    segmentations[i_patient] = seg
                    metadatas[i_patient] = metadata
                elif os.path.isfile(seg[:-1]):
                    if verbose:
                        print(('Patient {}, found segmentation {} on session {}, scan {}').format(patientID, str(data['segmentation'][:-1]), str(data['experiment']), str(data['scan'])))
                    im = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), imagename)
                    seg = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), str(data['segmentation'][:-1]))

                    num = 0
                    while not success:
                        if num < 10:
                            if 'BLT' in project:
                                mdpath = os.path.join(os.path.dirname(path), project, patientID, str(data['experiment']), str(data['scan']), ('0000{}.dcm').format(num))
                            else:
                                mdpath = os.path.join(path, patientID, str(data['experiment']), str(data['scan']), ('0000{}.dcm').format(num))
                            metadata = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), ('0000{}.dcm').format(num))
                        else:
                            if 'BLT' in project:
                                mdpath = os.path.join(os.path.dirname(path), project, patientID, str(data['experiment']), str(data['scan']), ('000{}.dcm').format(num))
                            else:
                                mdpath = os.path.join(path, patientID, str(data['experiment']), str(data['scan']), ('000{}.dcm').format(num))
                            metadata = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), ('000{}.dcm').format(num))

                        if os.path.isfile(mdpath):
                            success = True
                        else:
                            num += 1

                    images[i_patient] = im
                    segmentations[i_patient] = seg
                    metadatas[i_patient] = metadata
                elif os.path.isfile(seg[:-2]):
                    if verbose:
                        print(('Patient {}, found segmentation {} on session {}, scan {}').format(patientID, str(data['segmentation'][:-2]), str(data['experiment']), str(data['scan'])))
                    im = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), imagename)
                    seg = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), str(data['segmentation'][:-2]))

                    num = 0
                    success = False
                    while not success:
                        if num < 10:
                            mdpath = os.path.join(path, patientID, str(data['experiment']), str(data['scan']), ('0000{}.dcm').format(num))
                            metadata = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), ('0000{}.dcm').format(num))
                        else:
                            mdpath = os.path.join(path, patientID, str(data['experiment']), str(data['scan']), ('000{}.dcm').format(num))
                            metadata = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), ('000{}.dcm').format(num))

                        if os.path.isfile(mdpath):
                            success = True
                        else:
                            num += 1

                    images[i_patient] = im
                    segmentations[i_patient] = seg
                    metadatas[i_patient] = metadata
                elif skipseg:
                    # Return the image and metadata normally, but return None as seg
                    im = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), imagename)
                    seg = None

                    num = 0
                    success = False
                    while not success:
                        if num < 10:
                            if 'BLT' in project:
                                mdpath = os.path.join(os.path.dirname(path), project, patientID, str(data['experiment']), str(data['scan']), ('0000{}.dcm').format(num))
                            else:
                                mdpath = os.path.join(path, patientID, str(data['experiment']), str(data['scan']), ('0000{}.dcm').format(num))
                            metadata = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), ('0000{}.dcm').format(num))
                        else:
                            if 'BLT' in project:
                                mdpath = os.path.join(os.path.dirname(path), project, patientID, str(data['experiment']), str(data['scan']), ('000{}.dcm').format(num))
                            else:
                                mdpath = os.path.join(path, patientID, str(data['experiment']), str(data['scan']), ('000{}.dcm').format(num))
                            metadata = ('vfs://data/{}/{}/{}/{}/{}').format(project, patientID, str(data['experiment']), str(data['scan']), ('000{}.dcm').format(num))

                        if os.path.isfile(mdpath):
                            success = True
                        else:
                            num += 1

                    images[i_patient] = im
                    segmentations[i_patient] = seg
                    metadatas[i_patient] = metadata
                else:
                    if verbose:
                        print(("Invalid: Patient {}, file {} not found.").format(patientID, seg))
            else:
                if verbose:
                    print(("Invalid: Patient {}, file {} not found.").format(patientID, im))

    if verbose:
        print("Found " + str(len(images.keys())) + ' patients with segmentation.')

    return images, metadatas, segmentations
