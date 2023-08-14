import cv2

from util.profile_time import profile_time

class Objects():

    def __init__(self, config):
        self.config = config

    @profile_time('objects')
    def __call__(self, frame):
        resized = cv2.resize(frame, (0, 0), fx=0.2, fy=0.2, interpolation=cv2.INTER_LANCZOS4)
        ss = cv2.ximgproc.segmentation.createSelectiveSearchSegmentation()
        ss.setBaseImage(resized)
        #ss.switchToSelectiveSearchFast(base_k=1000, inc_k=1000, sigma = 0.8)
        ss.switchToSingleStrategy(k=100, sigma=0.8)
        rects = ss.process()
        return rects