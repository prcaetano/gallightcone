# Requirements

* [Python](http://www.python.org) 3.5 or 3.6

* [Astropy](http://www.astropy.org)

* [configparser](https://docs.python.org/3/library/configparser.html)

* [CAMB](https://camb.readthedocs.io/en/latest/)

* [schwimmbad](https://schwimmbad.readthedocs.io/en/latest/)

(cf. environment.yml)

# gallightcone

This is a simple code to generate a lightcone from Shadab's HOD output.

To run this code use:

```python 
python build_gallightcone_multibox.py config.ini
```
The relevant section of config.ini will look like (see config.ini for an example):
```
[dir]
dir_out                  Output directory
dir_gcat                 Directory where the input out_*p.list.gcat files are located
input_name_template      Python template string describing names of input files
lightcone_name_template  Python template string describing names of output files
file_alist               File containing list of simulation scale factors
file_camb                CAMB configuration file

[sim]
boxL             Length of the simulation box [Mpc/h]
shellwidth       Width of shell [Mpc/h]
zmin             Minimum of redshift range to use
zmax             Maximum of redshift range
shellnums        Comma-separated list of numbers (if provided, ignores the redshift range specified above)
is_cutsky        If True, produce lightcones for cutsky mocks (uses same snapshot for all shells).
                 Otherwise, each shell uses the snapshot closest to the center of the shell.
snapshot_cutsky  Number of fixed snapshot to use if is_cutsky is True.
```

Each of these options can also be overriden by passing as arguments in the command call, check

```python
python build_gallightcone_multibox.py -h
```

The shell number are counted from z=0 (0 being z=0)
e.g. if you define shellwidth = 25 in the config file and choose shellnums=1 then you are selecting the shell between 25-50 Mpc/h 

The code will output galaxy catalogs in each shell, which you will have to combine.

An example job script to run on NERSC is on job.sh

If you have questions or comments please email yomori@stanford.edu

