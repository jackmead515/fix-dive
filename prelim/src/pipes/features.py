import cv2
import logging

import numpy as np
import pandas as pd

from models.motion import Motion
from models.objects import Objects
from models.blur import Blur
from models.colors import Colors
from util.profile_time import profile_time


@profile_time('process_frames')
def process_frames(
    s3_file_path: str,
    file_name: str,
    video_details: dict,
    options: dict
):
    motion_model = Motion({})
    objects_model = Objects({})
    blur_model = Blur({})
    colors_model = Colors({})
    
    capture = cv2.VideoCapture(file_name)
    
    total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_index = 0
    
    df_data = []
    
    skip_frames = options.get('skip_frames', 1)
    resize = options.get('resize', 1.0)
    
    while True:
        
        success, frame = capture.read()
        
        if not success:
            break

        if frame_index % skip_frames != 0:
            frame_index += 1
            continue
        
        # TODO: add option to resize frames
        if resize != 1.0:
            frame = cv2.resize(frame, (0,0), fx=resize, fy=resize, interpolation=cv2.INTER_LANCZOS4)
        
        motion = motion_model(frame)
        objects = objects_model(frame)
        blur = blur_model(frame)
        colors = colors_model(frame)
        
        median_motion = np.nan if motion is None else np.median(motion)
        
        df_data.append([
            s3_file_path,
            frame_index,
            blur,
            len(objects),
            median_motion,
            *colors,
        ])
        
        progress = round((frame_index / total_frames) * 100, 2)
        print(f'compute features progress: {progress}%', end='\r')
        
        frame_index += 1
        
    capture.release()
    
    return df_data
    

@profile_time('upload_features')
def upload_features(s3_client, s3_file_path, df_data):
    df = pd.DataFrame(df_data, columns=['file_path', 'frame_index', 'blur', 'total_objects', 'median_motion', 'red', 'orange', 'yellow', 'green', 'blue', 'purple', 'white', 'black', 'brown'])

    if s3_client.exists(s3_file_path):
        s3_client.rm(s3_file_path)

    with s3_client.open(s3_file_path, 'wb') as f:
        df.to_parquet(f, index=False, compression='gzip')


def compute_features(
    s3_client,
    s3_file_path,
    file_name,
    video_details,
    options
):
    
    force_recompute = options.get('force_recompute', False)
    
    features_exist = s3_client.exists(s3_file_path)
    
    if force_recompute:
        logging.info('force recompute enabled')
        
        if features_exist:
            logging.info('deleting existing features')
            s3_client.rm(s3_file_path)
            
    elif features_exist:
        logging.info('features already computed')
        return
    
    df_data = process_frames(s3_file_path, file_name, video_details, options)
    
    upload_features(s3_client, s3_file_path, df_data)

    print('features computed and uploaded successfully')
    
