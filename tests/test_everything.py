import pytest
import sys

from denoising import DenoisingPipeline
from denoising.config import load_config
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')

def test_pipeline():

    config = load_config('/home/tm/projects/Denoising/configs/strategy_4.yaml')
    pipeline = DenoisingPipeline(config)

    # Update these paths to your data
    bold_path = r"/data/Projects/ABIDE2/ABIDEII-BNI_1/derivatives/sub-29006/ses-1/func/sub-29006_ses-1_task-rest_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    output_dir = "/home/tm/projects/Denoising/output"

    # Run the pipeline
    output_file = pipeline.process_subject(bold_path, output_dir)

    print('done')


def test_confounds():
    config = load_config('/home/tm/projects/Denoising/configs/strategy_4.yaml')
    pipeline = DenoisingPipeline(config)
    bold_path = r"/data/Projects/ABIDE2/ABIDEII-BNI_1/derivatives/sub-29006/ses-1/func/sub-29006_ses-1_task-rest_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    print('cosine', pipeline.confounds_handler.config.cosine)
    confounds, sample_mask = pipeline.confounds_handler.load_and_select(bold_path)
    print(confounds.columns)
    print(sample_mask)

def test_batch():
    config = load_config('/home/tm/projects/Denoising/configs/strategy_4.yaml')
    pipeline = DenoisingPipeline(config)

    # Define subjects to process
    subjects = [
        {"bold_path": "/data/Projects/ABIDE2/ABIDEII-BNI_1/derivatives/sub-29006/ses-1/func/sub-29006_ses-1_task-rest_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz",
        },
        {"bold_path": "/data/Projects/ABIDE2/ABIDEII-BNI_1/derivatives/sub-29007/ses-1/func/sub-29007_ses-1_task-rest_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz",
        }
    ]
    output_dir = "/home/tm/projects/Denoising/output"
    # Run batch processing

    outputs = pipeline.process_batch(subjects, output_dir)
    print(f"Processed {len([o for o in outputs if o])} subjects successfully")

#test_batch()
test_confounds()
#test_pipeline()