import sys
import logging
import psutil
import os
import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor

import s3fs
import cv2
import numpy as np
import pandas as pd
from dask import dataframe as dd
import dask

sys.path.append('../..')

from common.project import Project

import config
import dask_util

preprocess_columns = [
    'frame_index',
    'blur',
    'total_objects',
    'median_motion',
    'std_motion',
    'features',
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

@dask.delayed
def read_stream(
    options: dict,
    video_segment: dict
):
    
    # for caching large objects
    from distributed.worker import thread_state
    
    # will get included as part of the dask worker
    from motion import Motion
    from objects import Objects
    from blur import Blur
    from colors import Colors
    from features import Features
    
    logging.basicConfig(level=logging.INFO)
    
    object_resize = options.get('object_resize', 0.2)
    feature_skip = options.get('feature_skip', 10)
    skip_frames = options.get('skip_frames', 1)
    resize = options.get('resize', 1.0)

    motion_model = Motion({})
    objects_model = Objects({ 'resize': object_resize })
    blur_model = Blur({})
    colors_model = Colors({})
    
    # cache the features model. This is a large DL model
    if not hasattr(thread_state, 'features_model'):
        thread_state.features_model = Features({ 'skip_frames': feature_skip })
    features_model =  thread_state.features_model

    start_frame = video_segment['start_frame']
    frames_to_read = video_segment['total_frames']
    http_segment_path = video_segment['file_path']

    capture = cv2.VideoCapture(http_segment_path)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 10)
    
    frame_index = start_frame
    frames_read = 0

    preprocess_data = []
    objects_data = []
    
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) * resize)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) * resize)
    video_area = width * height
    
    small_area_threshold = 0.01 * video_area
    large_area_threshold = 0.95 * video_area
    
    logging.info('starting compute features')
    
    while True:
        
        if frames_read >= frames_to_read:
            break

        success = capture.grab()
        
        if not success:
            break

        if frame_index % skip_frames != 0:
            frames_read += 1
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
        features = features_model(frame)

        median_motion = np.nan if motion is None else np.median(motion)
        std_motion = np.nan if motion is None else np.std(motion)
        byte_features = np.nan if features is None else features.tobytes()

        preprocess_data.append([
            frame_index,
            blur,
            len(objects),
            median_motion,
            std_motion,
            byte_features,
            *colors,
        ])
        
        # save the objects to a seperate dataset
        for object in objects:
            x, y, w, h = object
            area = w * h
            if area < small_area_threshold or area > large_area_threshold:
                continue
            objects_data.append([frame_index, x, y, w, h])

        progress = round((frames_read / frames_to_read) * 100, 2)
        logging.info(f'compute features progress: {progress}%')

        frames_read += 1
        frame_index += 1

    capture.release()
    
    pre_df = pd.DataFrame(preprocess_data, columns=preprocess_columns)
    obj_df = pd.DataFrame(objects_data, columns=objects_columns)
    
    return pre_df, obj_df



if __name__ == "__main__":

    config.initialize()
    
    logging.basicConfig(level=logging.INFO)
    
    project = Project(
        bucket_name=config.S3_BUCKET,
        project_id=config.PROJECT_ID,
    )
    
    logging.info(f'Processing Project: {project}')
    
    options = {
        'skip_frames': 1, # every frame
        'feature_skip': 10, # every 10 frames
        'object_resize': 0.2, # 20% of original size
        'resize': 1.0, # 100% of original size
        'force_recompute': False,
    }
    
    s3_client = s3fs.S3FileSystem(
        anon=False,
        key=config.S3_ACCESS_KEY_ID,
        secret=config.S3_SECRET_ACCESS_KEY,
        use_ssl=False,
        client_kwargs={
            'endpoint_url': config.S3_ENDPOINT_URL
        }
    )

    variant_details_path = project.get_variant_playlist_details('low')
    variant_segments_path = project.get_variant_playlist_segments('low')
    
    if not s3_client.exists(variant_details_path):
        logging.info('playlist details not found')
        exit(0)
        
    if not s3_client.exists(variant_segments_path):
        logging.info('playlist segments not found')
        exit(0)
        
    video_segments = json.loads(s3_client.cat(variant_segments_path))
    video_details = json.loads(s3_client.cat(variant_details_path))
    
    logging.info(f'video details: {video_details}')
    logging.info(f'video segments: {video_segments}')

    logging.info('starting distributed processing')
    start_processing = time.perf_counter()
    
    dask_client = dask_util.get_dask_client()
    
    features = []

    for video_segment in video_segments:
        features.append(read_stream(options, video_segment))
        
    dask_client.upload_file('models/motion.py')
    dask_client.upload_file('models/objects.py')
    dask_client.upload_file('models/blur.py')
    dask_client.upload_file('models/colors.py')
    dask_client.upload_file('models/features.py')

    features = dask.compute(*features)
    
    logging.info('finished distributed processing')
    logging.info(f'processing time: {time.perf_counter() - start_processing} seconds')

    features_path = project.features_path
    preprocess_file_path = f'{features_path}/preprocess/preprocess.gzip.parquet'
    objects_file_path = f'{features_path}/objects/objects.gzip.parquet'

    # combine all the features into a single dataframe
    # for writing to parquet files in s3
    preprocess_df = pd.concat([pre_data for pre_data, _ in features])
    objects_df = pd.concat([obj_data for _, obj_data in features])

    s3_client = s3fs.S3FileSystem(
        anon=False,
        key=config.S3_ACCESS_KEY_ID,
        secret=config.S3_SECRET_ACCESS_KEY,
        use_ssl=False,
        client_kwargs={
            'endpoint_url': config.S3_ENDPOINT_URL
        }
    )
    
    logging.info(f'writing objects features to {objects_file_path}')
    
    with s3_client.open(objects_file_path, 'wb') as f:
        objects_df.to_parquet(f, index=False, compression='gzip')
    
    logging.info(f'writing preprocess features to {preprocess_file_path}')
    
    with s3_client.open(preprocess_file_path, 'wb') as f:
        preprocess_df.to_parquet(f, index=False, compression='gzip')