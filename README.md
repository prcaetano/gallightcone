# gallightcone

This code is a simple code to generate a lightcone from a simulation box.

To run this code use:

```python 
python build_gallightcone_multibox.py test.config X
```
Here test.config is a config file which contains:
```
[dir]
dir_out     directory where you want to place the outputs 
dir_gcat    directory where the input gcat files are located
file_alist  file that constains the list of scale factors
file_camb   camb configuration file

[sim]
boxL        Length of the ismulation box [Mpc/h]
shellwidth  width of shell [Mpc/h]

[sample]
galtype     type of galaxy used - 1=LRG,2=QSO,3=ELG 
```

X is the shell number (0 being z=0)
e.g. if you define shellwidth = 25 in the config file and choose X=1 then you are selecting the shell between 25-50 Mpc/h 

