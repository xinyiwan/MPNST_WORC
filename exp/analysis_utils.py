import pandas as pd
import scipy.stats
import numpy as np
import os


def get_rad(pid, rid=1):
    """
    Get evaluation from radiologists
    """
    if rid == 1:
        r_name = 'David'
    else:
        r_name = 'JanJaap'
    y_rad = []
    missing_id = []
    y_rad_all = pd.read_csv(f'/archive/xwan/radiologists/raw_data/MNST_Scores_{r_name}_231205_metadata.csv')
    for i in range(len(pid)):
        if len(y_rad_all.loc[y_rad_all['Patient']==pid[i], '1_mpnst'].values)==1:
            y_rad.append(int((y_rad_all.loc[y_rad_all['Patient']==pid[i], '1_mpnst'].item()-1)/2))
        else:
            missing_id.append(pid[i])
    return y_rad, missing_id


def get_list_from_text():
    list_pid = []
    y_predictions = []
    y_truths = []
    with open('/archive/xwan/cv_test/working/output/output_cli_final/cv_pid_100.txt') as f:
        for line in f:
            inner_list = [elt.strip('\'\n []') for elt in line.split(',')]
            list_pid.append(inner_list)

    with open("/archive/xwan/cv_test/working/output/output_cli_final/cv_y_predictions_100.txt") as f:
        for line in f:
            inner_list = [int(elt.strip('\'\n [].')) for elt in line.split(' ')]
            y_predictions.append(inner_list)

    with open("/archive/xwan/cv_test/working/output/output_cli_final/cv_y_truths_100.txt") as f:
        for line in f:
            inner_list = [int(elt.strip('\'\n [].')) for elt in line.split(' ')]
            y_truths.append(inner_list)
    
    return list_pid, y_predictions, y_truths


def get_mean_volume(ids):
    
    if len(ids)==0:
        return 0
    
    volumes_all = pd.read_csv('/archive/xwan/radiologists/results/meta/T1_meta.csv')
    volumes = []
    for id in ids:
        volumes.append(volumes_all.loc[volumes_all['pid']==id,'volume'].item())
    
    return round(sum(volumes)/len(volumes),3)



def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    return m, m-h, m+h
