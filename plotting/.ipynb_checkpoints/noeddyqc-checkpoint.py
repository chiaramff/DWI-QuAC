#!/usr/bin/env python

#author: Chiara Maffei
#cmaffei@mgh.harvard.edu

import argparse
##########################
import nibabel as nib
import numpy as np
import matplotlib.pyplot as pltm
import pandas as pd
import seaborn as sns
##########################
import os.path
from datetime import date
from PIL import Image
date = date.today().strftime('%d%m%y')

parser = argparse.ArgumentParser(
        description='Create QC summary as PDF and saves updated dataframes with qc values for single subject')
parser.add_argument('qcdir', metavar='qcdir',type=str, 
                        help='QC directory')
parser.add_argument('subj', metavar='subj', help='Subj ID')
parser.add_argument('pdf_output', metavar='pdf_output', type = str,
                        help='File with qc plots and screenshots')
parser.add_argument('txt_output', metavar='txt_output', type=str,
                        help='Text file with qc params')
parser.add_argument('wm_mask', metavar='wm_mask', type=str,
                        help='White Matter Binary Mask')
parser.add_argument('bvals', metavar='bvals', type=str,
                        help='Bval file')
parser.add_argument('data', metavar='data', type=str,
                        help='DWI data')
#optional args
parser.add_argument('--gm_mask', default = None, metavar='gm_mask',type=str,
                        help='Gray Matter Binary Mask')
parser.add_argument('--csf_mask', default = None, metavar='csf_mask',type=str,
                        help='Gray Matter Binary Mask')

args = parser.parse_args()
############### Directories ################
qcdir = args.qcdir
dtdir = qcdir+'/dtifit'
ssdir = qcdir+'/screenshots'
########### Loading data #############
print('Plotting DTIFIT Results')
wm = nib.load(args.wm_mask).get_fdata()
if args.gm_mask:
    gm = nib.load(args.gm_mask).get_fdata()
if args.csf_mask:
    csf = nib.load(args.csf_mask).get_fdata()
fa = nib.load(dtdir+'/dtifit_FA.nii.gz').get_fdata()
md = nib.load(dtdir+'/dtifit_MD.nii.gz').get_fdata()
res = nib.load(dtdir+'/dtifit_residuals.nii.gz').get_fdata()
tsnr = nib.load(qcdir+'/bzeros_snr.nii.gz').get_fdata()
snr = np.loadtxt(qcdir+'/tsnr_orig.txt')
cnr_wm = np.loadtxt(qcdir+'/cnrwm.txt')
cnr_wm = np.divide(cnr_wm[:,0],cnr_wm[:,1])
bval = np.loadtxt(args.bvals)
data = nib.load(args.data).get_fdata()
########### Plot DTIFIT Results #############
print('Creating QC PDF')
fig = pltm.figure(dpi=300, tight_layout=True)
fig.set_size_inches(8.27, 11.69, forward=True) #A4 size
gs = fig.add_gridspec(5, 4, height_ratios=[3,2,3,2,2])

#tSNR
ax1 = fig.add_subplot(gs[0,0:2])
ax1.set_title('SNR b=0 s/mm$^2$', fontsize=12)
pltm.setp(ax1.get_xticklabels(), visible=False);
pltm.setp(ax1.get_yticklabels(), visible=False);
pltm.tick_params(axis='both',which='both',length=0)
y = int(tsnr.shape[1]/2)
img = ax1.imshow(tsnr[:,y,:].T, cmap=pltm.cm.jet, interpolation='nearest', origin='lower', vmin = 0, vmax=35)
pltm.colorbar(img)
ax1.annotate('Mean:'+str("{:.2f}".format(snr[0]))+'+/-'+str("{:.2f}".format(snr[1])),(0, 0), c = 'w')

#CNR
ax2 = fig.add_subplot(gs[0,2:4])
ax2 = sns.boxplot(x=bval,y=cnr_wm)
ax2.set_xlabel('b-value', fontsize = 12, labelpad=0)
ax2.set_ylabel('CNR', fontsize = 12)
ax2.tick_params(labelsize=8, labelrotation = 35, axis='x')
ax2.tick_params(axis='y', direction = "in", pad = -22)
ax2.set_title('CNR in WM per shell', fontsize = 12)

#FA MD screenshots
ax3 = fig.add_subplot(gs[1,0:1])
ax4 = fig.add_subplot(gs[1,1:2])
z = int(tsnr.shape[2]/2)
ax3.imshow(fa[:,:,z].T, cmap=pltm.cm.gray, interpolation='nearest', origin='lower', vmin = 0, vmax=0.6)
ax3.tick_params(axis='both',which='both',length=0);
ax4.imshow(md[:,:,z].T, cmap=pltm.cm.gray, interpolation='nearest', origin='lower', vmin = 0)
ax3.set_title('FA')
ax4.set_title('MD')
pltm.setp(ax3.get_xticklabels(), visible=False); pltm.setp(ax4.get_xticklabels(), visible=False);
pltm.setp(ax3.get_yticklabels(), visible=False); pltm.setp(ax4.get_yticklabels(), visible=False);
ax4.tick_params(axis='both',which='both',length=0); 

# FA Histograms 
ax5 = fig.add_subplot(gs[1,2:3])
ax5.hist(fa[wm>0], histtype='stepfilled', alpha = 0.3, ec='k', label='WM', bins = 100, color = 'b')
ax5.hist(fa[gm>0], histtype='stepfilled', alpha = 0.3, ec='k', label='GM', bins = 100, color = 'g')
ax5.set_xlim(0,1)
ax5.annotate('WM:'+str("{:.2f}".format(np.abs(np.mean(fa[wm>0]))))+'(+/-'+str("{:.2f}".format(np.abs(np.std(fa[wm>0]))))+')',
                 (0.0, ax5.get_ylim()[1]/2), fontsize = 9)
ax5.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
ax5.set_title('FA', fontsize=9)
# MD Histograms 
ax6 = fig.add_subplot(gs[1,3:4])
ax6.hist(md[wm>0], histtype='stepfilled', alpha = 0.3, ec='k', label='WM', bins = 100, color = 'b')
ax6.hist(md[gm>0], histtype='stepfilled', alpha = 0.3, ec='k', label='GM', bins = 100, color = 'g')
ax6.ticklabel_format(style='sci', axis = 'x', scilimits = (0,0))
ax6.set_xlim(0,md.max())
ax6.annotate('WM:'+str("{:.2e}".format(np.abs(np.mean(md[wm>0]))))+'(+/-'+str("{:.2e}".format(np.abs(np.std(md[wm>0]))))+')',
                 (0.0001, ax6.get_ylim()[1]/2), fontsize = 9)
ax6.set_title('MD [s/mm$^2$]', fontsize=9)
ax6.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
ax5.legend(); 

# DTIFIT V1
ax7 = fig.add_subplot(gs[2:3,0:2])
ax8 = fig.add_subplot(gs[2:3,2:4])
ax7.imshow(Image.open(ssdir+'/dti_v1_coronal.png'), resample = False, interpolation = None, filternorm = True)
ax7.set_title('DTIFit V1 - coronal')
ax7.tick_params(axis='both', which='both',length=0);
ax8.imshow(Image.open(ssdir+'/dti_v1_axial.png'), resample = False, interpolation = None, filternorm = True)
ax8.set_title('DTIFit V1 - axial')
pltm.setp(ax7.get_xticklabels(), visible=False); pltm.setp(ax8.get_xticklabels(), visible=False);
pltm.setp(ax7.get_yticklabels(), visible=False); pltm.setp(ax8.get_yticklabels(), visible=False)
ax8.tick_params(axis='both', which='both',length=0);

#DTIFIT residuals
ax9 = fig.add_subplot(gs[3,0:2])
x = list(range(1,len(bval)+1,1))
y = abs(np.mean(res[wm>0],0))
err = np.std(res[wm>0],0)
ax9.errorbar(x,y,err, linestyle = None, marker = 'o', markersize = 3, linewidth = 0.3)
ax9.set_xlabel('DWI Volume', fontsize = 12)
ax9.set_title('Residual [a.u.]', fontsize = 12)

#signal
ax10 = fig.add_subplot(gs[3,2:3])
ax11 = fig.add_subplot(gs[3,3:4])
if args.gm_mask:
    rois = [wm,gm,csf]
    roinames = ['WM', "GM", "CSF"]
    colors = ['b','g','r']
else:
    rois = [wm]
    roinames = ['WM']
    colors = ['b']
    
data_norm = np.zeros(data.shape)
np.seterr(divide='ignore', invalid='ignore')
import warnings
#temp. should behandled in seaborn 0.13
warnings.filterwarnings("ignore", "use_inf_as_na")
for i in range(0, data.shape[3]):
    data_norm[:,:,:,i] = data[:,:,:,i]/data[:,:,:,0]
for i in range(0, len(rois)):
        r = rois[i]
        df = pd.DataFrame()
        df['bval'] = bval
        df['Signal [-]'] = np.mean(data[r==1],0)
        df['log'] = np.log(df['Signal [-]'])
        df['Norm. Signal [-]'] = np.mean(data_norm[r==1],0)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        sns.lineplot(x='bval',y='log',data=df, legend='brief', marker='o',label = roinames[i],  markersize = 5,
            err_style='bars', errorbar = 'sd', color = colors[i], ax=ax10)
        sns.lineplot(x='bval',y='Signal [-]',data=df, legend='brief', marker='o',label = roinames[i],  
                     markersize = 5, err_style='bars', errorbar = 'sd', color = colors[i], ax=ax11)
ax11.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
ax10.set_ylabel('[]');  ax11.set_ylabel('[]');
ax10.set_title('Norm. Signal [-]', fontsize = 10); ax11.set_title('Signal [-]', fontsize = 10)

###### Saving PDF
fig.suptitle(' QC for Subject '+str(args.subj)+' '+str(date), fontsize = 14)
pltm.savefig(args.pdf_output, format = 'pdf')
print('PDF saved!')

####### Creating dataframe and save data
print('Creating dataframe...')
#storing subject data
new_row = {'Sub': str(args.subj),
         'Average_SNR(b<100)': snr[0],
	     'Mean_FA_WM': np.abs(np.mean(fa[wm>0])),
         'Mean_MD_WM': np.abs(np.mean(md[wm>0]))}

#checking if dataframe exists
if not os.path.isfile(args.txt_output):
	print('Txt file with group QC measures not found. Creating new file...')
	df = pd.DataFrame()
	df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

else:
	print('Txt file with group QC measures found. Appending data...')
	df = pd.read_fwf(args.txt_output)
	df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
#### Saving Dataframe
tfile = open(str(args.txt_output), 'w')
tfile.write(df.to_string())
tfile.close()
