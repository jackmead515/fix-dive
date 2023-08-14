import subprocess
import multiprocessing
import tempfile
from concurrent.futures import ProcessPoolExecutor
import os
import pickle
import gzip
import logging

import s3fs

import config
import util.video_info as video_info
from pipes.download import download_video
from pipes.features import compute_features
from pipes.generate_project import generate_project


def process_video(
    s3_file_path: str,
    s3_features_file: str,
    options: dict
):
    s3 = s3fs.S3FileSystem(
        anon=False,
        key=config.AWS_ACCESS_KEY_ID,
        secret=config.AWS_SECRET_ACCESS_KEY,
    )
    
    with tempfile.NamedTemporaryFile(dir='/tmp/dive') as temp_file:
        
        download_video(s3, s3_file_path, temp_file)
        
        video_details = video_info.details(temp_file.name)
        
        print(video_details)
        
        compute_features(s3, s3_features_file, temp_file.name, video_details, options)


if __name__ == "__main__":

    config.initialize()
    
    logging.basicConfig(level=logging.INFO)
    
    options = {
        'skip_frames': 10,
        'resize': 0.5,
        'force_recompute': False,
    }

    pool = ProcessPoolExecutor(max_workers=4)
    
    project_files = generate_project('1234567890')
    
    # for files in file_pairs:
    #     pool.submit(process_video, files[0], files[1])
        
    # pool.shutdown(wait=True)
    # pool = ProcessPoolExecutor(max_workers=4) 
    
    for files in project_files:
        process_video(files[0], files[1], options)
        #pool.submit(process_features, files[0], files[1], files[2])

    #pool.shutdown(wait=True)