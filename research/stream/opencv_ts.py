import cv2

if __name__ == "__main__":
    
    url = 'http://172.23.0.100:30140/fix-dive-storage/projects/1234567890/playlists/151db784662c957df5430469add2e851/view/video.m3u8'
    
    capture = cv2.VideoCapture(url)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    fps = capture.get(cv2.CAP_PROP_FPS)
    
    while True:
        
        success, frame = capture.read()
        
        if not success:
            break
        
        cv2.imshow('frame', frame)
        
        if cv2.waitKey(33) & 0xFF == ord('q'):
            break
    
    capture.release() 