#!/usr/bin/env python

#author: Chiara Maffei
#cmaffei@mgh.harvard.edu

import argparse
###############################
import nibabel as nb
import numpy as np
import matplotlib.pyplot as pltm
import pandas as pd
import seaborn as sns
################################
import os.path
from datetime import date
from PIL import Image
date = date.today().strftime('%d%m%y')

parser = argparse.ArgumentParser(
        description='Create Motion QC summary from eddy outputs as PDF and saves updated dataframes with qc values for single subject')
parser.add_argument('s2v_file', metavar='s2v',type=str, 
			help='File with motion over time information')
parser.add_argument('rms_file', metavar='rms', type=str,
			help='File with volume to volume motion information')
parser.add_argument('res_rms_file', metavar='res_rms', type=str, 
			help='File with volume to volume restricted motion information')
parser.add_argument('params_file', metavar='params', type=str,
			help='File with motion and EC parameters information')
parser.add_argument('nslices', metavar='nslices',type=int, help='Number of slices')
parser.add_argument('bval_file', metavar='bval', help='Bval file')
parser.add_argument('subj', metavar='subj', help='Subj ID')
parser.add_argument('pdf_output', metavar='pdf_output', type = str,
			help='File with motion plots')
parser.add_argument('txt_output', metavar='txt_output', type=str,
			help='Text file with qc motion params')
args = parser.parse_args()

#loading rms files
print('Loading files...')
rms_abs = np.loadtxt(args.rms_file)[:,0]
rms_rel = np.loadtxt(args.rms_file)[:,1]
rms_re_abs = np.loadtxt(args.res_rms_file)[:,0]
rms_re_rel = np.loadtxt(args.res_rms_file)[:,1]

#loading bval
bval = np.loadtxt(args.bval_file)

#loading sv2 file and computing std
s2v = np.genfromtxt(args.s2v_file, dtype=float)
s2v[:,3:6] = np.rad2deg(s2v[:,3:6])
ex_check = np.arange(0,args.nslices)
s2v_var = np.full((bval.size,6), -1.0)
for i in np.arange(0, bval.size):
    tmp = s2v[i*args.nslices:(i+1)*args.nslices]
    s2v_var[i] = np.var(tmp[ex_check], ddof=1, axis=0)

#store rotations and translations in dataframe for visualization
df = pd.DataFrame()
df['x'] =s2v_var[:,0]
df['y'] = s2v_var[:,1]
df['z'] = s2v_var[:,2]
df_s2v_tr = df.melt(var_name = 'Axis', value_name = 'Translation')
df = pd.DataFrame()
df['x'] = np.rad2deg(s2v_var[:,3])
df['y'] = np.rad2deg(s2v_var[:,4])
df['z'] = np.rad2deg(s2v_var[:,5])
df_s2v_rot = df.melt(var_name = 'Axis', value_name = 'Rotation')
    
#loading params file and temporarily store them in dataframe for visualization
params = np.loadtxt(args.params_file)
df = pd.DataFrame()
df['x'] = params[:,0]
df['y'] = params[:,1]
df['z'] = params[:,2]
df_tr = df.melt(var_name = 'Axis', value_name = 'Translation')
df = pd.DataFrame()
df['x'] = params[:,3]
df['y'] = params[:,4]
df['z'] = params[:,5]
df_rot = df.melt(var_name = 'Axis', value_name = 'Rotation')

#Creating motion dataframe and save data
print('Creating dataframe...')
mean_params = np.mean(params[:,0:6], axis = 0)
mean_s2v_var = np.mean(s2v_var[:,0:6], axis = 0)

new_row = {'Sub': str(args.subj),
         'Mean_Vol2Vol_Translations(x)': mean_params[0],
         'Mean_Vol2Vol_Translations(y)': mean_params[0],
         'Mean_Vol2Vol_Translations(z)': mean_params[2],
         'Mean_Vol2Vol_Rotations(x)': mean_params[3],
         'Mean_Vol2Vol_Rotations(y)': mean_params[4],
         'Mean_Vol2Vol_Rotations(z)': mean_params[5],
         'Average_Absolute_Motion': np.mean(rms_abs),
         'Average_Relative_Motion': np.mean(rms_rel),
         'Average_Absolute_Restricted_Motion': np.mean(rms_re_abs),
	 'Average_Relative_Restricted_Motion': np.mean(rms_re_rel)}

#checking if dataframe exists
if not os.path.isfile(args.txt_output):
        print('Txt file with group QC measures not found. Creating new file...')
        df = pd.DataFrame()
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
else:
        print('Txt file with group QC measures found. Appending data...')
        df = pd.read_fwf(args.txt_output)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

tfile = open(str(args.txt_output), 'w')
tfile.write(df.to_string())
tfile.close()

# Prepare figure
print('Creating QC motion PDF')
fig = pltm.figure(constrained_layout =True, figsize=(8.27,11.69))# Standard portrait A4 sizes
gs = fig.add_gridspec(5,4)

vols = len(bval)
ax1= fig.add_subplot(gs[0,:-1])
ax1.plot(np.sqrt(s2v_var[:,0]), 'r', linewidth=2, label="x")
ax1.plot(np.sqrt(s2v_var[:,1]), 'g', linewidth=2, label="y")
ax1.plot(np.sqrt(s2v_var[:,2]), 'b', linewidth=2, label="z")
ax1.set_xbound(1, bval.size)
ax1.set_xlabel("Volumes")
ax1.set_ylabel("Std translation [mm]")
ax1.set_xlim(0,vols)
ax1.set_title("Eddy estimated within volume translations (mm)")
ax1.legend(loc='best', frameon=True, framealpha=0.5)
ax1.set_ylim(bottom = 0)

ax2 = fig.add_subplot(gs[1,:-1])
ax2.plot(np.sqrt(s2v_var[:,3]), 'r', linewidth=2, label="x")
ax2.plot(np.sqrt(s2v_var[:,4]), 'g', linewidth=2, label="y")
ax2.plot(np.sqrt(s2v_var[:,5]), 'b', linewidth=2, label="z")
ax2.set_xbound(1, bval.size)
ax2.set_xlabel("Volumes")
ax2.set_ylabel("Std rotation [deg]")
ax2.set_xlim(0,vols)
ax2.set_title("Eddy estimated within volume rotations (deg)")
ax2.legend(loc='best', frameon=True, framealpha=0.5)
ax2.set_ylim(bottom = 0)

ax3 = fig.add_subplot(gs[0:1,-1])
sb = sns.violinplot(x='Axis', y='Translation', data = df_tr, ax = ax3, cut = 0)
ax4 = fig.add_subplot(gs[1:2,-1])
sb = sns.violinplot(x='Axis', y='Rotation', data = df_rot, ax = ax4, cut = 0)

ax5 = fig.add_subplot(gs[2,:-1])
ax5.plot(params[:,0], 'r', linewidth=2, label="x")
ax5.plot(params[:,1], 'g', linewidth=2, label="y")
ax5.plot(params[:,2], 'b', linewidth=2, label="z")
ax5.legend(loc='best', frameon=True, framealpha=0.5)
ax5.set_xlabel("Volumes")
ax5.set_ylabel("Translation [mm]")
ax5.set_xlim(0,vols)
ax5.set_title("Eddy estimated volume to volume translations (mm)")

ax6 = fig.add_subplot(gs[3,:-1])
ax6.plot(params[:,3], 'r', linewidth=2, label="x")
ax6.plot(params[:,4], 'g', linewidth=2, label="y")
ax6.plot(params[:,5], 'b', linewidth=2, label="z")
ax6.legend(loc='best', frameon=True, framealpha=0.5)
ax6.set_xlabel("Volumes")
ax6.set_ylabel("Rotation [deg]")
ax6.set_xlim(0,vols)
ax6.set_title("Eddy estimated volume to volume rotations (deg)")

ax7 = fig.add_subplot(gs[2:3,-1])
sb = sns.violinplot(x='Axis', y='Translation', data = df_tr, ax = ax7, cut = 0)
ax8 = fig.add_subplot(gs[3:4,-1])
sb = sns.violinplot(x='Axis',y= 'Rotation', data = df_rot, ax = ax8, cut = 0)

ax9 = fig.add_subplot(gs[4,:-1])
ax9.plot(rms_abs, label = 'Absolute ('+f"{rms_abs.mean():.3}"+')')
ax9.plot(rms_rel, label= 'Relative ('+f"{rms_rel.mean():.2}"+')')
ax9.set_xlabel('Volumes', fontsize = 10)
ax9.set_ylabel('Displacement [mm]', fontsize =10)
ax9.set_xlim(0,vols)
ax9.legend(fontsize = 14)

df = pd.DataFrame()
df['Rel.'] = rms_re_abs
df['Abs.'] = rms_re_rel
df_res = df.melt(var_name = 'Ax', value_name = 'Displacement [mm]')

ax10 = fig.add_subplot(gs[4,3:4])
sb = sns.violinplot(x='Ax', y='Displacement [mm]',  data = df_res, ax = ax10, cut = 0)
sb.set_xlabel(' ')
sb.set_title('Restricted Motion')

fig.suptitle(' Motion QC for Subject '+str(args.subj)+' '+str(date), fontsize = 12)
#save pdf
pltm.savefig(args.pdf_output, format = 'pdf')
print('QC motion PDF saved!')

