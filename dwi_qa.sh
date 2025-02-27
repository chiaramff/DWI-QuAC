#!/bin/bash

# AUTHOR: Chiara Maffei
# Contact: cmaffei@mgh.harvard.edu 

#TODO
# --> add option to fit tensor in one shell only

set -e # The script will terminate after the first line that fails

#only internal to MARTINOS!!! need to fix
export FREESURFER_HOME=/usr/local/freesurfer/7.3.0
source $FREESURFER_HOME/SetUpFreeSurfer.sh
source /usr/pubsw/packages/mrtrix/env.sh 

####### Help Function ###############################
Help()
{
echo "This script performs a QA check of your dMRI data"
echo "Add description"
echo "Script assume bvec and bval to be named as data"
echo "If not. provide path to bvec and bval files"
echo "Syntax: $0 -i dmri_data [-e|o|b|r|h]"
echo
echo "Options:"
echo "h   Print this Help"
echo "i   Input DWI data"
echo "e   path to eddy output folder"
echo "o   path to output directory"
echo "r   path to bvec file"
echo "b   path to bval file"
echo "g   performs MRtrix gradients check"
echo "s   provide subject id"
echo "f   specify threshold for WM mask. Default=0.2"
echo "q	  specify location group QC outputs"
}
######## Checking args ###############################
NO_ARGS=0
if [ $# -eq "$NO_ARGS" ]; then
    echo "ERROR: you must provide dMRI original data"
    echo "USAGE: $0 -h for help"
    exit 1
fi
######## Checking options ##############################
while getopts "he:o:b:r:i:gs:q:f:" option; do
	case $option in
	   h) # display Help
	      Help
	      exit;;
	   \?) # Invalid option
	      echo "Error: invalid option"
	      exit;;
	   i) #Enter path to dMRI data
	      data=${OPTARG};;
	   e) #Enter path to eddy folder
	      eddyout=${OPTARG};;
	   o) #Enter path to output folder
	      outdir=${OPTARG};;
	   b) #Enter path to bval file
	      bval=${OPTARG};;
	   r) #Enter path to bvec file
	      bvec=${OPTARG};;
	   g) #Do MRtrix grad check
	      dogradcheck=1;;
	   s) #Provide subj id
	      subjid=${OPTARG};;
	   q) #Enter path to group dataframes
	      fgrpq=${OPTARG};;
	   f) #Threshold WM mask
	      thr=${OPTARG};;
  	esac
done

codedir=`realpath $0`
codedir=`dirname $codedir`
echo $codedir
#########################################################
############# Check original data ########################
echo "############# dMRI data ############################"
if [[ $data ]]; then
	data=`realpath $data`
	if [[ ! -f $data ]]; then
        	echo "ERROR: dMRI data not found."
        	exit 1
	else
		echo "dMRI data are:" $data
	        dim4=`fslhd $data | grep -w "dim4" | awk '{print $2}'`
        	if [[ $dim4 == 1 ]]; then
                	echo "ERROR: Provided data do not look as dMRI data"
			exit 1
        	else
                	echo "dMRI volumes:" $dim4
        	fi
	fi
else
	echo "You need to provide original dMRI data path"
	exit 1
fi	
############## Check outdir #########################
wdir=`pwd`
if [[ $outdir ]]; then
	outdir=`realpath $outdir`
	if [[ ! -d $outdir ]]; then
		echo "ERROR: Output directory does not exist"
		exit 1
	else
		echo "Output directory is" $outdir
	fi
else
	echo "Output directory not specified"
	echo "Creating output directory:" $wdir/dwi_qa
	if [[ -d $wdir/dwi_qa ]]; then 
		echo "WARNING: Output directory exists. Data will be overwritten"
	fi
	outdir=$wdir/dwi_qa
	mkdir -p $outdir
fi
############### Create log file ########################
touch $outdir/log.txt
LF=$outdir/log.txt
######## Check bval and bvec ########################
if [[ $bval ]]; then
	bval=`realpath $bval`
	echo "bvals are:" $bval
else
	fdata=${data%%.*}
	bval=${fdata}.bval
	if [[ ! -f $bval ]]; then
		echo "ERROR: Bval file not found. Please specify path using -b option"
		exit 1
	else
		echo "bvals are:" $bval
	fi
fi

if [[ $bvec ]]; then
	bvec=`realpath $bvec`
        echo "bvecs are:" $bvec
else
        fdata=${data%%.*}
        bvec=${fdata}.bvec
        if [[ ! -f $bvec ]]; then
                echo "ERROR: Bvec file not found. Please specify path using -r option"
        	exit 1
		else
			echo "bvecs are:" $bvec
	fi
fi
######## Check number of directions match ####################
nbval=`wc -l $bval | awk '{print $1}'`
nbvec=`wc -l $bvec | awk '{print $1}'`
if [[ $nbval == 1 ]]; then #rows
	cmd="$codedir/row2col.sh $bval $outdir/bvals"
	echo ${cmd}; eval ${cmd}
 	echo ${cmd} >> $LF
	nbval=`wc -l $outdir/bvals | awk '{print $1}'`
fi
if [[ $nbval -ne $dim4 ]]; then 

	echo "ERROR: Bval file does not have the same length as DWI"
	exit 1
fi

if [[ $nbvec == 3 ]]; then #rows
        cmd="$codedir/row2col.sh  $bvec $outdir/bvecs"
		echo ${cmd}; eval ${cmd}
 		echo ${cmd} >> $LF
        nbvec=`wc -l $outdir/bvecs | awk '{print $1}'`
fi

if [[ $nbvec -ne $dim4 ]]; then
        echo "ERROR: Bvec file does not have the same length as DWI"
        exit 1
fi

######## Creating brain mask #######################################
echo "Creating brain mask..."
cmd="dwiextract $data -bzero -force -fslgrad $bvec $bval $outdir/bzeros.nii.gz"
echo ${cmd}; eval ${cmd};
echo ${cmd} >> $LF

cmd="fslmaths $outdir/bzeros.nii.gz -Tmean $outdir/bzeros_tmean.nii.gz"
echo ${cmd}; eval ${cmd};
echo ${cmd} >> $LF

cmd="bet2 $outdir/bzeros_tmean.nii.gz $outdir/lowb_brain -m"
echo ${cmd}; eval ${cmd}
echo ${cmd} >> $LF

mask=$outdir/lowb_brain_mask.nii.gz

######### Run DWIGRADCHECK ###################################
if [[ $dogradcheck ]]; then 
	echo "Performing MRtrix grad check"
	# Mrtrix likes them in rows and not columns....
	cmd="$codedir/transpose_gradients.py $bval $outdir/tmp.bval_row"
	echo ${cmd}; eval ${cmd}
 	echo ${cmd} >> $LF
	bval=$outdir/tmp.bval_row
	if ! command -v dwigradcheck &> /dev/null; then 
        	echo "WARNING: MRtrix command not found. Skipping grad check"
			rm -rf $outdir/tmp.bval_row
	else
		if  [[ -v $eddyout ]]; then
			echo "Eddy-corrected bvecs found. Running gradient check on them"
			bvec=`echo $eddyout\*eddy_rotated_bvecs`
		else
        		bvec=$bvec
		fi		
	cmd="$codedir/transpose_gradients.py $bvec $outdir/tmp.bvec_row"
	echo ${cmd}; eval ${cmd}
    echo ${cmd} >> $LF
	bvec=$outdir/tmp.bvec_row
	bvalc=$outdir/bvals_c
    bvecc=$outdir/bvecs_c
    cmd="dwigradcheck $data -mask $mask -fslgrad $bvec $bval -force -export_grad_fsl $bvecc $bvalc"
    echo ${cmd}; eval ${cmd}
    echo ${cmd} >> $LF
	fi
fi

######### Run QA on original data #############################
echo "########## Running QA on original data #################"

if [[ $subjid ]]; then 
	subj="Subject: $subjid"
else
	subj="Data: `basename $data`"
fi

####### DTIFIT ########
dtidir=$outdir/dtifit
ssdir=$outdir/screenshots
mkdir -p $ssdir
mkdir -p $dtidir

if [[ -f $outdir/bvecs_c ]]; then
	bvec=$outdir/bvecs_c
	bval=$outdir/bvals_c
else
	bvec=$outdir/bvecs
	bval=$outdir/bvals
fi

cmd="dtifit -k $data -o $dtidir/dtifit --save_tensor -b $bval -r $bvec -m $mask"
echo ${cmd}; eval ${cmd}
echo ${cmd} >> $LF

cmd="dtigen -t $dtidir/dtifit_tensor.nii.gz -o $dtidir/dtifit_pred --s0=$dtidir/dtifit_S0.nii.gz -b $bval -r $bvec -m $mask"
echo ${cmd}; eval ${cmd}
echo ${cmd} >> $LF

cmd="fslmaths $data -sub $dtidir/dtifit_pred.nii.gz $dtidir/dtifit_residuals.nii.gz"
echo ${cmd}; eval ${cmd}
echo ${cmd} >> $LF

####### Run Synthseg ########################################
if ! command -v mri_synthseg &> /dev/null; then
        echo "WARNING: FreeSurfer Synthseg command not found."
        echo "WARNING: WM mask will be obtained from FA mask"
	
	if [[ $thr ]]; then
        	thr=$thr
	else
        	thr=0.2
	fi
        cmd="fslmaths $dtidir/dtifit_FA.nii.gz -thr $thr -uthr 1 -bin $outdir/wm_mask.nii.gz"
        echo ${cmd}; eval ${cmd};
        echo ${cmd} >> $LF
else
        cmd="mri_synthseg --i $outdir/lowb_brain.nii.gz --o $outdir/synthseg_out.nii.gz --parc --threads 5"
        echo ${cmd}; eval ${cmd}
        echo ${cmd} >> $LF
        #Extract WM mask
        cmd="mri_extract_label $outdir/synthseg_out.nii.gz 2 41 $outdir/wm_mask.nii.gz"
        echo ${cmd}; eval ${cmd};
        echo ${cmd} >> $LF
        cmd="mri_convert $outdir/wm_mask.nii.gz -rl $outdir/lowb_brain.nii.gz -rt nearest $outdir/wm_mask.nii.gz "
        echo ${cmd}; eval ${cmd};
        echo ${cmd} >> $LF
        cmd="fslmaths $outdir/wm_mask.nii.gz -bin $outdir/wm_mask.nii.gz"
        echo ${cmd}; eval ${cmd};
        echo ${cmd} >> $LF

	cmd="fslmaths $outdir/synthseg_out.nii.gz -thr 100 $outdir/cortex_mask.nii.gz"
	echo ${cmd}; eval ${cmd};
	echo ${cmd} >> $LF
	cmd="mri_convert $outdir/cortex_mask.nii.gz -rt nearest -rl $outdir/lowb_brain.nii.gz $outdir/cortex_mask.nii.gz"
	echo ${cmd}; eval ${cmd};
	echo ${cmd} >> $LF
	cmd="fslmaths $outdir/cortex_mask.nii.gz -bin $outdir/cortex_mask.nii.gz"
	echo ${cmd}; eval ${cmd};
	echo ${cmd} >> $LF

	cmd="mri_extract_label $outdir/synthseg_out.nii.gz 14 15 $outdir/ventricles_mask.nii.gz"
	echo ${cmd}; eval ${cmd};
        echo ${cmd} >> $LF
	cmd="mri_convert $outdir/ventricles_mask.nii.gz -rt nearest -rl $outdir/lowb_brain.nii.gz $outdir/ventricles_mask.nii.gz"
        echo ${cmd}; eval ${cmd};
        echo ${cmd} >> $LF
	cmd="fslmaths $outdir/ventricles_mask.nii.gz -bin $outdir/ventricles_mask.nii.gz"
        echo ${cmd}; eval ${cmd};
        echo ${cmd} >> $LF
	
fi
####### CNR IN WM ###########
echo "~~~~~~~~~ Computing CNR in WM ~~~~~~~"
cmd="fslstats -t $data -k $outdir/wm_mask.nii.gz -m -s"
echo ${cmd}; eval ${cmd};
echo ${cmd} >> $LF
${cmd} > $outdir/cnrwm.txt 

######### SNR ###########
echo "~~~~~~~~~ Computing Temporal SNR ~~~~~~~"

cmd="fslmaths $outdir/bzeros.nii.gz -Tstd $outdir/bzeros_tstd.nii.gz"
echo ${cmd}; eval ${cmd};
echo ${cmd} >> $LF

cmd="fslmaths $outdir/bzeros_tmean.nii.gz -div $outdir/bzeros_tstd.nii.gz $outdir/bzeros_snr.nii.gz"
echo ${cmd}; eval ${cmd};
echo ${cmd} >> $LF

cmd="fslstats $outdir/bzeros_snr.nii.gz -k $mask -M -S"
echo ${cmd}; eval ${cmd};
echo ${cmd} >> $LF
${cmd} > $outdir/tsnr_orig.txt

########## TAKE SCREENSHOTS ###################
if ! command -v freeview &> /dev/null; then
        echo "WARNING: freeview command not found."
	echo "screenshots will not be taken"
else
	#I think the following only if mrtrix env is sourced
	cmd="env -u LD_LIBRARY_PATH sh $codedir/qc_screenshots.sh $outdir $data"
	if [[ $eddyout ]]; then
		cmd="$cmd $eddydir"
	fi
	echo ${cmd}; eval ${cmd};
	echo ${cmd} >> $LF
fi

######## CREATE PDF DTI/GRAD/SNR  ###############
#create PDF and dataframe for dti/gradient/snr qc

######### Run QA on EDDY Outputs ############################
if [[ $eddyout ]]; then
	eddyout=`realpath $eddyout`
	if [[ ! -d $eddyout ]]; then 
		echo "ERROR: Eddy directory does not exist"
		exit 1 
	else 
        	echo "Eddy directory is" $eddyout
        	echo "QA will include motion qa and eddy qa"
	fi
	
	### Create PDF and dataframe for motion QC ###
        fs2v=`echo $eddyout/*.eddy_movement_over_time`
        frms=`echo $eddyout/*.eddy_movement_rms`
        fres_rms=`echo $eddyout/*.eddy_restricted_movement_rms`
        fparams=`echo $eddyout/*.eddy_parameters`
        dim3=`fslinfo $data | grep -w "dim3" | awk '{print $2}'`
	pdf_output=$outdir/qc_motion.pdf

	# Assigning group QC directory output #
	if [[ $fgrp ]]; then
		fgrp=`realpath $fgrp`
		if [[ -d $fgrp ]]; then
			fgrp=$fgrp
		else
			echo "Warning: path to group dataframes directory inexistent"
			echo "Group dataframes will be saved in $outdir"
			fgrp=$outdir
		fi
	else	
		echo "Path to group QC not specified. Output will be saved in $outdir"
		fgrp=$outdir
	fi	
	fgrpm=$fgrp/group_motion.txt
	fgrq=$fgrp/group_eddyoutliers.txt
        fgrd=$fgrp/group_dti,snr.txt

        echo "nslices is $dim3"
        cmd="python $codedir/qc_motion.py $fs2v $frms $fres_rms $fparams $dim3 $bvalc $subjid $pdf_output $fgrpm"
        echo ${cmd}; eval ${cmd};
        echo ${cmd} >> $LF

	#create PDF and dataframe for outlier/top up qc
	ol_file=`echo $eddyout/*.eddy_outlier_map`
	ol_std_file=`echo $eddyout/*.eddy_outlier_n_stdev_map`
	res_file=`echo $eddyout/*.eddy_residuals.nii.gz`
	if [[ ! -f $res_file ]]; then
		echo "WARNING: Eddy residuals file not found. Specify --residuals when running Eddy"
		echo "Residuals plot omitted by QC" 
	fi

	######### SNR EDDY ###########
	cnrmaps=`echo $eddyout/*.eddy_cnr_maps.nii.gz`
	if [[ ! -f $cnrmaps ]]; then
        	echo "WARNING: CNR maps not found in eddy output dir. Specify cnr_maps when running Eddy"
		echo "Eddy CNR plots omitted by QC"
	else
    		cmd="fslstats -t $cnrmaps -k $mask -n -m -s"
    		echo ${cmd}; eval ${cmd};
    		echo ${cmd} >> $LF
    		${cmd} > $outdir/cnr_maps.txt
	fi

	cmd="python $codedir/qc_ol.py $ol_file $ol_std_file"

else
        echo "Eddy directory not provided"
        echo "QA will not include motion and eddy qa"
fi
############ Remove tmp files ##########################
rm -rf $outdir/tmp.bvec_row
rm -rf $outdir/tmp.bval_row
######################################
echo "DWI QA done!"
######################################
