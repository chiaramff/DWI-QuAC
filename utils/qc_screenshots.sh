#!/bin/bash

# AUTHOR: Chiara Maffei
# Contact: cmaffei@mgh.harvard.edu 

#set -e # The script will terminate after the first line that fails

#-------------------- TAKE SCREENSHOTS ---------------------------------------
qcdir=$1
data=$2
if [[ $3 ]]; then
	eddydir=$3
fi
echo "Data is $data"
#tSNR pre-eddy 
sc=$qcdir/screenshots/tsnr.png
cmd="freeview $qcdir/bzeros_snr.nii.gz:colormap=pet:colorscale=0,35 -nocursor -layout 1 -colorscale -subtitle SNR -viewport coronal -ss $sc"
echo ${cmd}; eval ${cmd};

#DTI screenshots
sc=$qcdir/screenshots/dti_v1_coronal.png
fa=$qcdir/dtifit/dtifit_FA.nii.gz
md=$qcdir/dtifit/dtifit_MD.nii.gz
v1=$qcdir/dtifit/dtifit_V1.nii.gz
x=`fslinfo $data | grep -w "dim1" | awk '{print $2/2}'`
y=`fslinfo $data | grep -w "dim2" | awk '{print $2/2}'`
z=`fslinfo $data | grep -w "dim3" | awk '{print $2/2}'`
cmd="freeview $fa $v1:vector=1:render=line -nocursor -layout 1 -viewport coronal -zoom 4 -slice $x $y $z -cc -ss $sc 0.4 1"
echo ${cmd}; eval ${cmd};

sc=$qcdir/screenshots/dti_fa_coronal.png
cmd="freeview $fa -nocursor -layout 1 -viewport coronal -zoom 1 -slice $x $y $z -cc -ss $sc 0.4 1"
echo ${cmd}; eval ${cmd};

sc=$qcdir/screenshots/dti_md_coronal.png
cmd="freeview $md -nocursor -layout 1 -viewport coronal -zoom 1 -slice $x $y $z -cc -ss $sc 0.4 1"
echo ${cmd}; eval ${cmd};

sc=$qcdir/screenshots/dti_v1_axial.png
cmd="freeview $fa $v1:vector=1:render=line -nocursor -layout 1 -viewport axial -zoom 3 -slice $x $y $z -cc -ss $sc 1 1"
echo ${cmd}; eval ${cmd};

sc=$qcdir/screenshots/brain_mask.png
cmd="freeview $qcdir/lowb_brain.nii.gz $qcdir/lowb_brain_mask.nii.gz -nocursor -layout 1 -viewport coronal -cc -ss $sc 0.4 1"
echo ${cmd}; eval ${cmd};

#TOP UP
if [[ $eddydir ]]; then
	cmd=`echo $eddydir/*.eddy_command_txt`
	if [[ 'grep 'topup' $cmd' ]]; then
		topup_base=`cat $cmd | sed 's:.*topup=::' | awk '{print $1}'`
		sc=$qcdir/screenshots/topup_unwarp.png
		topup_un=${topup_base}_b0_unwarp.nii.gz
		cmd="freeview $topup_un -nocursor -layout 1 -viewport axial -zoom 1 -slice $x $y $z -cc -ss $sc 0.4 1"
		echo ${cmd}; eval ${cmd};
	fi
fi
	
sc=$qcdir/screenshots/lowb_orig.png
cmd="freeview $qcdir/lowb_brain.nii.gz -nocursor -layout 1 -viewport axial -zoom 1 -slice $x $y $z -cc -ss $sc 0.4 1"
echo ${cmd}; eval ${cmd};












echo "Screenshots Done"
