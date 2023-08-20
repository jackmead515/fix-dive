import cv2
import os
import time

if __name__ == "__main__":
    
    playlist_url = 'http://minio-api.kubby.ninja/fix-dive-storage/projects/1234567890/playlists/main.m3u8'
    
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'protocol_whitelist;file,rtp,udp,crypto,data,http,https,tcp,tls'
    
    capture = cv2.VideoCapture(playlist_url)
    
    
    start_time = time.perf_counter()
    #capture.set(cv2.CAP_PROP_POS_FRAMES, 1000)
    
    # self to half way through video without using frames
    capture.set(cv2.CAP_PROP_POS_AVI_RATIO, 0.5)
    
    print('seek time', time.perf_counter() - start_time)
    
    capture.release() 