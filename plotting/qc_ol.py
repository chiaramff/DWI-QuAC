#!/usr/bin/env python

#author: Chiara Maffei
#cmaffei@mgh.harvard.edu

import argparse

import nibabel as nb
import numpy as np
import matplotlib.pyplot as pltm
import pandas as pd
import seaborn as sns
############################
import os.path
from datetime import date
from PIL import Image
############################
date = date.today().strftime('%d%m%y')

parser = argparse.ArgumentParser(
        description='Create QC summary as PDF and saves updated dataframes with qc values for single subject')
parser.add_argument('ol_file', metavar='ol', type=str, 
                        help='Eddy File with information on total outliers ')
parser.add_argument('ol_std_file', metavar='ol_std', type=str,
                        help='Eddy File: number of std off the mean difference between observation and predictions')
parser.add_argument('params_file', metavar='params', type=str,
                        help='Eddy file with motion and EC parameters information')
parser.add_argument('bval_file', metavar='bval', help='Bval file')
parser.add_argument('mask_file', metavar='mask', help='Binary brain mask')
parser.add_argument('subj', metavar='subj', help='Subj ID')
parser.add_argument('pdf_output', metavar='pdf_output', type = str,
                        help='File with qc plots and screenshots')
parser.add_argument('txt_output', metavar='txt_output', type=str,
                        help='Text file with qc params')
#optional args
parser.add_argument('--cnr_eddy', default = None, metavar='cnr_eddy_file',type=str,
                        help='File with snr information after eddy')
parser.add_argument('--eddy_res', default = None, metavar='snr_img', type=str,
                        help='Eddy output residuals file')

args = parser.parse_args()

######### Load files  ########
print('Loading files...')
bval = np.loadtxt(args.bval_file)
ol = np.genfromtxt(args.ol_file,dtype=None, delimiter=" ", skip_header=1)
ol_std = np.genfromtxt(args.ol_std_file,dtype=float, delimiter=" ", skip_header=1)
params = np.loadtxt(args.params_file)
mask = nb.load(args.mask_file).get_fdata()
tot_ol = 100*np.count_nonzero(ol)/((bval > 100).sum()*ol.shape[1])
std_ec = np.std(params[:,6:9], axis = 0)
indb0 = bval < 50
if args.eddy_res:
    res = nb.load(args.eddy_res).get_fdata()

#Create figure
print('Creating PDF with QC output...')
fig = pltm.figure(dpi=300, tight_layout=True)
fig.set_size_inches(8.27, 11.69, forward=True) #A4 size
gs = fig.add_gridspec(5, 4, height_ratios=[2,2,3,2,2]) 

nvols = res.shape[3]
#Eddy outliers
ax1 = fig.add_subplot(gs[0,0:2])
ax1.plot(0.5+np.arange(0, nvols), 100*np.sum(ol, axis=1)/ol.shape[1], color = 'r')
ax1.set_xlabel('DWI Volume', fontsize = 11)
ax1.set_ylabel("% outliers",fontsize = 11)
ax1.set_ylim([0, 2+np.max(100*np.sum(ol, axis=1)/ol.shape[1])])
ax1.set_title('% Outliers per volume', fontsize = 12)
ax1.annotate('Tot OL='+str(tot_ol), xy = (0,1), fontsize=12);

ax2 = fig.add_subplot(gs[0,2:4]) 
sns.heatmap(np.transpose(ol_std), ax=ax2,  
            cbar_kws={"orientation": "vertical", "label": "No. std."}, 
            vmin=-4, vmax=4, xticklabels=int(bval.size/10), yticklabels=10, cmap='RdBu_r')
ax2.set_title('Outliers (Std off the mean slice diff)', fontsize=14)
ax2.set_ylabel("Slice", fontsize = 11)
ax2.set_xlabel("Volume", fontsize = 11)

# gs.tight_layout(fig,h_pad=0,w_pad=0)
fig.suptitle(' QC for Subject '+str(args.subj)+' '+str(date), fontsize = 18)
pltm.savefig(args.pdf_output, format = 'pdf')
print('PDF saved!')

####### Creating dataframe and save data
print('Creating dataframe...')
#storing subject data
new_row = {'Sub': str(args.subj),
	 'EC_LinearTerm(x)(std)': std_ec[0],
         'EC_LinearTerm(y)(std)': std_ec[1],
         'EC_LinearTerm(z)(std)': std_ec[2],
         'Total_Outliers': tot_ol}

#checking if dataframe exists
if not os.path.isfile(args.txt_output):
	print('Txt file with group QC measures not found. Creating new file...')
	df = pd.DataFrame()
	df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
else:
	print('Txt file with group QC measures found. Appending data...')
	df = pd.read_fwf(args.txt_output)
	df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

# if args.cnr_eddy:
# 	snr_eddy_mean = np.loadtxt(args.cnr_eddy)[:,0]
# 	snr_eddy_std = np.loadtxt(args.cnr_eddy)[:,1]
# 	df['Average_SNR (b<100)'] = snr_eddy_mean[0]
# if args.eddy_res:
#     res_sq = np.square(res)
#     msres = abs(np.mean(res_sq[mask>0],0))
#     df['Eddy_Residuals'] = msres

tfile = open(str(args.txt_output), 'w')
tfile.write(df.to_string())
tfile.close()


