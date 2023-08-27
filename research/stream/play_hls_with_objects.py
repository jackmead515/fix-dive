import cv2
import os
import pandas as pd

import s3fs

if __name__ == "__main__":
    
    #playlist_url = "http://172.23.0.100:30140/fix-dive-storage/projects/1234567890/playlists/Y2h1bmsubXA0MTUxZGI3ODQ2NjJjOTU3ZGY1NDMwNDY5YWRkMmU4NTE=/video.m3u8"
    playlist_url = 'http://minio-api.kubby.ninja/fix-dive-storage/projects/1234567890/playlists/low.m3u8'
    
    #df = pd.read_parquet('http://minio-api.kubby.ninja/fix-dive-storage/projects/1234567890/features/objects/objects.gzip.parquet')
    
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'protocol_whitelist;file,rtp,udp,crypto,data,http,https,tcp,tls'
    
    capture = cv2.VideoCapture(playlist_url)
    
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_area = width * height
    
    small_area_threshold = 0.01 * video_area
    large_area_threshold = 0.95 * video_area
    
    frame_index = 0
    
    while True:
        
        success = capture.grab()
        
        if not success:
            break

        # find all rows in df with frame_index
        #objects = df.loc[df['frame_index'] == frame_index]
        
        # if len(objects) == 0:
        #     frame_index += 1
        #     continue
        
        success, frame = capture.retrieve()
        
        if not success:
            break
        
        resize = 0.2
        resized = cv2.resize(frame, (0,0), fx=resize, fy=resize, interpolation = cv2.INTER_AREA)
        
        model = cv2.ximgproc.segmentation.createSelectiveSearchSegmentation()
        model.setBaseImage(resized)
        #model.switchToSelectiveSearchFast()
        model.switchToSingleStrategy()
        rects = model.process()
        
        rects = rects.astype('float32')
        rects[:, :] /= resize

        for rect in rects:
            x, y, w, h = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
            area = w * h
            if area < small_area_threshold or area > large_area_threshold:
                continue
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 1, cv2.LINE_AA)
        
        cv2.imshow('frame', frame)
        
        if cv2.waitKey(33) & 0xFF == ord('q'):
            break
        
        frame_index += 1
    
    capture.release() 