#!/bin/bash
##SBATCH --qos=debug
##SBATCH --time=30
#SBATCH --qos=regular
#SBATCH --time=60
#SBATCH --nodes=1
#SBATCH --tasks-per-node=32
#SBATCH --cpus-per-task=2
#SBATCH --constraint=haswell
#SBATCH --mail-type=begin,end,fail
#SBATCH --mail-user=pcaetano@ifi.unicamp.br
#SBATCH --account=desi
#SBATCH --job-name=lightcones

. $HOME/.bashrc
mydesienv 19.12
. envvars

conda activate lightcone 

export DIR_OUT=/global/cscratch1/sd/prc/data/mock_challenge/lightcones/v2/
export DIR_GCAT=/global/cfs/cdirs/desi/cosmosim/UNITSIM/fixedAmp_001_lowres/Gcat-wpmax-v3/

srun --cpu-bind=cores build_gallightcone_multibox.py --dir_out ${DIR_OUT} --dir_gcat ${DIR_GCAT} config.ini

