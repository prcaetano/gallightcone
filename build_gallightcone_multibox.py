#!/usr/bin/env python

# Generate lightcone for DESI mocks
# from HOD catalogues generated by Shadab

import sys
import os
import camb
import numpy as np
import healpy as hp
import numexpr as ne
from camb import model, initialpower
from astropy.io import fits
import configparser
import argparse
from schwimmbad.mpi import MPIPool
from itertools import product, repeat

parser = argparse.ArgumentParser()
parser.add_argument("config", help="ini file holding configuration",
                    type=str)
parser.add_argument("--dir_out", type=str, help="output directory (overrides config file)")
parser.add_argument("--dir_gcat", type=str, help="input directory (same)")
parser.add_argument("--input_name_template", type=str, help="template for name of input catalogs (same)")
parser.add_argument("--lightcone_name_template", type=str, help="template for name of output catalogs (same)")
parser.add_argument("--shellnums", type=str, help="list of comma separated shell numbers to compute (same)")
parser.add_argument("--is_cutsky", type=bool, help="if True, uses same snapshot over all shells, otherwise uses the snapshot with closest redshift (same)")
parser.add_argument("--snapshot_cutsky", type=int, help="Snapshot number to use if is_cutsky set to True (same)")
args = parser.parse_args()


configfile = str(args.config) # config file

config     = configparser.ConfigParser()
config.read(configfile)

dir_out                 = args.dir_out
dir_gcat                = args.dir_gcat
input_name_template     = args.input_name_template
lightcone_name_template = args.lightcone_name_template
shellnums               = args.shellnums
is_cutsky               = args.is_cutsky
snapshot_cutsky         = args.snapshot_cutsky
if dir_out is None:
    dir_out       =  config.get('dir','dir_out')
if dir_gcat is None:
    dir_gcat      =  config.get('dir','dir_gcat')
if input_name_template is None:
    input_name_template =  config.get('dir','input_name_template')
if lightcone_name_template is None:
    lightcone_name_template = config.get('dir', 'lightcone_name_template')
if shellnums is None:
    try:
        shellnums = config.get('sim', 'shellnums')
    except:
        shellnums = None

if is_cutsky is None:
    is_cutsky = config.getboolean('sim', 'is_cutsky', fallback=False)

if is_cutsky:
    if snapshot_cutsky is None:
        snapshot_cutsky = config.getint('sim', 'snapshot_cutsky')

file_alist     =  config.get('dir','file_alist')
file_camb      =  config.get('dir','file_camb')
boxL           =  config.getint('sim','boxL')
shellwidth     =  config.getint('sim','shellwidth')
if shellnums is None:
    zmin       =  config.getfloat('sim', 'zmin')
    zmax       =  config.getfloat('sim', 'zmax')
alist          = np.loadtxt(file_alist)

zlist   = 1/alist[:,1]-1.
origin  = [0,0,0]
clight  = 299792458.

def tp2rd(tht,phi):
    """ convert theta,phi to ra/dec """
    ra  = phi/np.pi*180.0
    dec = -1*(tht/np.pi*180.0-90.0)
    return ra,dec

def checkslicehit(chilow,chihigh,xx,yy,zz):
    """ pre-select so that we're not loading non-intersecting blocks """
    bvx=np.array([0,boxL,boxL,   0,   0,boxL,boxL,   0])
    bvy=np.array([0,   0,boxL,boxL,   0,   0,boxL,boxL])
    bvz=np.array([0,   0,   0,   0,boxL,boxL,boxL,boxL])

    boo = 0
    r   = np.zeros(8)
    for i in range(0,8):
        sx  = (bvx[i] - origin[0] + boxL * xx);
        sy  = (bvy[i] - origin[1] + boxL * yy);
        sz  = (bvz[i] - origin[2] + boxL * zz);
        r[i]= np.sqrt(sx*sx + sy*sy + sz*sz)
    if chihigh<np.min(r):
        boo=boo+1
    if chilow>np.max(r):
        boo=boo+1
    #print(chilow,chihigh,np.min(r),np.max(r))
    if (boo==0):
        return True
    else:
        return False

def getnearestsnap(alist,zmid):
    """ get the closest snapshot """
    zsnap  = 1/alist[:,1]-1.
    return alist[np.argmin(np.abs(zsnap-zmid)),0]


def generate_lightcone_shell(args):
    """ Generates and saves a single lightcone shell """
    (galtype, shellnum), nearestsnap = args

    #out_file = dir_out+'lightcone_multibox_galtype%d_%d.fits'%(galtype,shellnum)
    out_file = dir_out+lightcone_name_template.format(galtype, shellnum)

    # Don't reprocess files already done
    if os.path.isfile(out_file):
        return

    preffix = f"[shellnum={shellnum},galtype={galtype}] "

    chilow = shellwidth*(shellnum+0)
    chiupp = shellwidth*(shellnum+1)
    chimid = 0.5*(chilow+chiupp)
    ntiles = int(np.ceil(chiupp/boxL))
    print(preffix + "tiling [%dx%dx%d]"%(2*ntiles,2*ntiles,2*ntiles))
    print(preffix + 'Generating map for halos in the range [%3.f - %.3f Mpc/h]'%(chilow,chiupp))

    if nearestsnap is None:
        zmid        = results.redshift_at_comoving_radial_distance(chimid/h)
        nearestsnap = getnearestsnap(alist,zmid)
        print(preffix + 'Using snapshot %d (closest to the middle of the shell)'%(nearestsnap))
    else:
        print(preffix + 'Using snapshot %d, as provided'%(nearestsnap))


    #--------------Loading the binary data file------------------------
    try:
        in_file = dir_gcat+input_name_template.format(int(nearestsnap))
        d     = np.loadtxt(in_file)
    except IOError:
        print(preffix + f"WARNING: Couldn't open {in_file} for galtype {galtype}, shellnum {shellnum}.",
              file=sys.stderr)
        return
    gtype = d[:,9]
    idx   = np.where(gtype==galtype)[0] #only selecting certain galaxies
    ngalbox=len(idx)
    px    = d[idx,0]
    py    = d[idx,1]
    pz    = d[idx,2]
    vx    = d[idx,3]
    vy    = d[idx,4]
    vz    = d[idx,5]
    print(preffix + "using %d halos"%len(idx))
    del d
    #-------------------------------------------------------------------

    totra   = np.array([])
    totdec  = np.array([])
    totz    = np.array([])
    totm    = np.array([])
    totdz   = np.array([])
    totvlos = np.array([])

    for xx in range(-ntiles,ntiles):
        for yy in range(-ntiles,ntiles):
            for zz in range(-ntiles,ntiles):

                slicehit = checkslicehit(chilow,chiupp,xx,yy,zz)             # Check if box intersects with shell

                if slicehit==True:

                    sx  = ne.evaluate("px -%d + boxL * xx"%origin[0])
                    sy  = ne.evaluate("py -%d + boxL * yy"%origin[1])
                    sz  = ne.evaluate("pz -%d + boxL * zz"%origin[2])
                    r   = ne.evaluate("sqrt(sx*sx + sy*sy + sz*sz)")
                    zi  = results.redshift_at_comoving_radial_distance(r/h) # interpolated distance from position
                    idx = np.where((r>chilow) & (r<chiupp))[0]              # only select halos that are within the shell

                    if idx.size!=0:
                        ux=sx[idx]/r[idx]
                        uy=sy[idx]/r[idx]
                        uz=sz[idx]/r[idx]
                        qx=vx[idx]*1000.
                        qy=vy[idx]*1000.
                        qz=vz[idx]*1000.
                        zp=zi[idx]
                        tht,phi = hp.vec2ang(np.c_[ux,uy,uz])
                        ra,dec  = tp2rd(tht,phi)
                        vlos    = ne.evaluate("qx*ux + qy*uy + qz*uz")
                        dz      = ne.evaluate("(vlos/clight)*(1+zp)")

                        totra   = np.append(totra,ra)
                        totdec  = np.append(totdec,dec)
                        totz    = np.append(totz,zp)
                        totdz   = np.append(totdz,dz)
                        totvlos = np.append(totvlos,vlos/1000.) # to convert back to km/s

    # Writing out the output fits file
    c1 = fits.Column(name='RA'     , array=totra    , format='E')
    c2 = fits.Column(name='DEC'    , array=totdec   , format='E')
    c3 = fits.Column(name='Z'      , array=totz     , format='D')
    c4 = fits.Column(name='DZ'     , array=totdz    , format='E')
    c5 = fits.Column(name='VEL_LOS', array=totvlos  , format='E')

    hdu             = fits.BinTableHDU.from_columns([c1, c2, c3,c4,c5])
    hdr             = fits.Header()
    hdr['NGALBOX']  = ngalbox # total number defined as length of ra array
    primary_hdu     = fits.PrimaryHDU(header=hdr)
    hdul            = fits.HDUList([primary_hdu, hdu])

    hdul.writeto(out_file, overwrite=True)


#-------- Running camb to get comoving distances -----------
#Load all parameters from camb file 
pars = camb.read_ini(file_camb)
h    = pars.h
pars.set_for_lmax(2000, lens_potential_accuracy=3)
pars.set_matter_power(redshifts=[0.], kmax=200.0)
pars.NonLinearModel.set_params(halofit_version='takahashi')
camb.set_feedback_level(level=100)
results   = camb.get_results(pars)

if shellnums is None:
    shellnum_min = int(results.comoving_radial_distance(zmin)*h // shellwidth)
    shellnum_max = int(results.comoving_radial_distance(zmax)*h // shellwidth + 1)
    shellnums = list(range(shellnum_min, shellnum_max+1))
else:
    shellnums = list(map(int, shellnums.split(",")))


try:
    pool = MPIPool()
except:
    pool = None

if is_cutsky:
    args = zip(product([1,2,3], shellnums), repeat(snapshot_cutsky))
else:
    args = zip(product([1,2,3], shellnums), repeat(None))

if pool is not None:
    if not pool.is_master():
        pool.wait()
        sys.exit(0)
    pool.map(generate_lightcone_shell, args)
else:
    map(generate_lightcone_shell, args)


