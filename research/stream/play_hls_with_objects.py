import cv2
import os
import pandas as pd

import s3fs

if __name__ == "__main__":
    
    #playlist_url = "http://172.23.0.100:30140/fix-dive-storage/projects/1234567890/playlists/Y2h1bmsubXA0MTUxZGI3ODQ2NjJjOTU3ZGY1NDMwNDY5YWRkMmU4NTE=/video.m3u8"
    playlist_url = 'http://minio-api.kubby.ninja/fix-dive-storage/projects/1234567890/playlists/main.m3u8'
    
    df = pd.read_parquet('http://minio-api.kubby.ninja/fix-dive-storage/projects/1234567890/features/objects/objects.gzip.parquet')
    
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'protocol_whitelist;file,rtp,udp,crypto,data,http,https,tcp,tls'
    
    capture = cv2.VideoCapture(playlist_url)
    
    # get total number of frames
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print('total frames', total_frames)
    
    frame_index = 0
    
    while True:
        
        success = capture.grab()
        
        if not success:
            break

        # find all rows in df with frame_index
        objects = df.loc[df['frame_index'] == frame_index]
        
        if len(objects) == 0:
            frame_index += 1
            continue
        
        success, frame = capture.retrieve()
        
        if not success:
            break
        
        # resize frame by 50%
        frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_LANCZOS4)
        
        for row in objects.itertuples():
            x, y, w, h = int(row.x), int(row.y), int(row.width), int(row.height)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        cv2.imshow('frame', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        frame_index += 1
    
    capture.release() 