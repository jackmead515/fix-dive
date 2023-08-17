import cv2

class Blur():


    def __init__(self, config):
        self.config = config


    def __call__(self, frame):
        
        # detect blur in frame
        blur = cv2.Laplacian(frame, cv2.CV_64F).var()
        
        return blur