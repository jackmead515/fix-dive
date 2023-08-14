import cv2

from util.profile_time import profile_time

class Blur():

    def __init__(self, config):
        self.config = config

    @profile_time('blur')
    def __call__(self, frame):
        
        # detect blur in frame
        blur = cv2.Laplacian(frame, cv2.CV_64F).var()
        
        return blur