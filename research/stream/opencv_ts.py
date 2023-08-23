import cv2

if __name__ == "__main__":
    
    capture = cv2.VideoCapture('/tmp/dive/90a153cd-9e34-41ca-9187-c4a8ca4eef20/medium/video.m3u8')
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