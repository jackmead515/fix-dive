import sys
import logging
import psutil
import os

import s3fs
import cv2
import numpy as np
import pandas as pd

sys.path.append('../..')

from common.project import Project
from common.s3_project import convert_to_http
import common.video_info as video_info

import config
from models.motion import Motion
from models.objects import Objects
from models.blur import Blur
from models.colors import Colors

preprocess_columns = [
    'frame_index',
    'blur',
    'total_objects',
    'median_motion',
    'std_motion',
    'red',
    'orange',
    'yellow',
    'green',
    'blue',
    'purple',
    'white',
    'black',
    'brown'
]

objects_columns = [
    'frame_index',
    'x',
    'y',
    'width',
    'height'
]

def save_dataframe(data, columns, s3_file_path):
    df = pd.DataFrame(data, columns=columns)
    with s3.open(s3_file_path, 'wb') as f:
        df.to_parquet(f, index=False, compression='gzip')


if __name__ == "__main__":

    config.initialize()
    
    logging.basicConfig(level=logging.INFO)
    
    project = Project(
        bucket_name=config.S3_BUCKET,
        project_id=config.PROJECT_ID,
    )
    
    logging.info(f'Processing Project: {project}')
    
    s3 = s3fs.S3FileSystem(
        anon=False,
        key=config.S3_ACCESS_KEY_ID,
        secret=config.S3_SECRET_ACCESS_KEY,
        use_ssl=False,
        client_kwargs={
            'endpoint_url': config.S3_ENDPOINT_URL
        }
    )
    
    options = {
        'skip_frames': 10,
        'resize': 0.5,
        'force_recompute': False,
    }
    
    motion_model = Motion({})
    objects_model = Objects({})
    blur_model = Blur({})
    colors_model = Colors({})
    
    http_playlist_path = convert_to_http(project.main_playlist_path, config.S3_ENDPOINT_URL.replace('http://', ''))
    
    video_info = video_info.details(http_playlist_path)
    
    logging.info(f'video path: {http_playlist_path}')
    logging.info(f'video info: {video_info}')
    
    capture = cv2.VideoCapture(http_playlist_path)
    
    total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)

    # skip to halfway through the video
    #capture.set(cv2.CAP_PROP_POS_FRAMES, total_frames / 2)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 10)
    
    # set the capture to halfway through the video with CAP_PROP_POS_AVI_RATIO
    # capture.set(cv2.CAP_PROP_POS_AVI_RATIO, 0.5)
    
    preprocess_data = []
    objects_data = []
    
    skip_frames = options.get('skip_frames', 1)
    resize = options.get('resize', 1.0)
    
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) * resize)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) * resize)
    video_area = width * height
    
    small_area_threshold = 0.01 * video_area
    large_area_threshold = 0.95 * video_area
    
    logging.info('starting compute features')
    
    frame_index = 0
    
    while True:

        success = capture.grab()
        
        if not success:
            break

        if frame_index % skip_frames != 0:
            frame_index += 1
            continue
        
        success, frame = capture.retrieve()
        
        if not success:
            break

        if resize != 1.0:
            frame = cv2.resize(frame, (0,0), fx=resize, fy=resize, interpolation=cv2.INTER_LANCZOS4)
        
        # compute all the features
        motion = motion_model(frame)
        objects = objects_model(frame)
        blur = blur_model(frame)
        colors = colors_model(frame)

        median_motion = np.nan if motion is None else np.median(motion)
        std_motion = np.nan if motion is None else np.std(motion)

        preprocess_data.append([
            frame_index,
            blur,
            len(objects),
            median_motion,
            std_motion,
            *colors,
        ])
        
        # save the objects to a seperate dataset
        for object in objects:
            x, y, w, h = object
            area = w * h
            if area < small_area_threshold or area > large_area_threshold:
                continue
            objects_data.append([frame_index, x, y, w, h])

        progress = round((frame_index / total_frames) * 100, 2)
        logging.info(f'compute features progress: {progress}%')
        logging.info(f'total objects: {len(objects_data)}')

        frame_index += 1

    capture.release()

    features_path = project.features_path
    preprocess_file_path = f'{features_path}/preprocess/preprocess.gzip.parquet'
    objects_file_path = f'{features_path}/objects/objects.gzip.parquet'
    
    logging.info(f'writing objects features to {objects_file_path}')
    
    save_dataframe(objects_data, objects_columns, objects_file_path)
    
    logging.info(f'writing preprocess features to {preprocess_file_path}')
    
    save_dataframe(preprocess_data, preprocess_columns, preprocess_file_path)