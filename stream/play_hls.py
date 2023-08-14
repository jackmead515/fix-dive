import cv2
import os

import s3fs

if __name__ == "__main__":
    
    # need to follow this: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-overview.html

    #playlist_url = "http://172.23.0.100:30140/fix-dive-storage/projects/1234567890/playlists/Y2h1bmsubXA0MTUxZGI3ODQ2NjJjOTU3ZGY1NDMwNDY5YWRkMmU4NTE=/video.m3u8"
    playlist_url = 'main.m3u8'
    
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'protocol_whitelist;file,rtp,udp,crypto,data,http,https,tcp,tls'
    
    capture = cv2.VideoCapture(playlist_url)
    #capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # set ffmpeg
    #capture.set(cv2.CAP_FFMPEG, 1)
    
    # get total number of frames
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print('total frames', total_frames)
    
    frame_index = 0
    
    while True:
        
        success, frame = capture.read()
        
        if not success:
            break
        
        print(frame_index, frame.shape)
        
        frame_index += 1
        
        # resize frame to 640x480
        frame = cv2.resize(frame, (640, 480))
        
        cv2.imshow('frame', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    capture.release() 