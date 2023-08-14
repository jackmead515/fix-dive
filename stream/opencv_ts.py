import cv2

if __name__ == "__main__":
    
    capture = cv2.VideoCapture('video_0.ts')
    
    while True:
        
        success, frame = capture.read()
        
        if not success:
            break
        
        cv2.imshow('frame', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    capture.release() 