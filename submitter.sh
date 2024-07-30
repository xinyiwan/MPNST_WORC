#!/bin/bash
#$ -N WORC_MPNST_T1_240302_texture
#$ -e /home/../logs/error_$JOB_ID.log
#$ -o /home/../logs/out_$JOB_ID.log
#$ -q week
#$ -l h_vmem=3G

# echo 'This script is running on'
# choose venv
source /home/xwan/worc/bin/activate

## Training locally
# train model with T1,T2 sequences
python /home/xwan/MPNST_WORC/src/train.py T1_T2 MPNST_T1_T2[date]
# train model with T1 with interactive segmentations
python /home/xwan/MPNST_WORC/src/train.py T1_Interactive_OnlySufficient MPNST_T1_Interactive_OnlySufficient_[date]
# train model with T2, T2fs and STIR sequences
python /home/xwan/MPNST_WORC/src/train.py T2_T2fs+STIR MPNST_T2_T2fsSTIR_[date]
# train model with T1, T2, T2fs and STIR sequences
python /home/xwan/MPNST_WORC/src/train.py T1_T2_T2fs+STIR MPNST_T1_T2_T2fsSTIR_[date]


## Training on CPU server
# bigrsub -q week -R 6G -N WORC_MPNST_T1_T2 python /home/xwan/MPNST-cpu/WORC3_MPNST.py T1_T2 MPNST_T1_T2_231010
# bigrsub -q week -R 6G -N WORC_MPNST_T1_T2_T1fsgd+SPIRgd python /home/xwan/MPNST-cpu/WORC3_MPNST.py T1_T2_T1fsgd+SPIRgd MPNST_T1_T2_T1fsgdSPIRgd_231010


