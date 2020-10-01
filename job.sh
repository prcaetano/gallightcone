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

srun --cpu-bind=cores build_gallightcone_multibox.py config.ini

