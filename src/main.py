import cv2
import numpy as np
import math
import pandas as pd

from features.motion import Motion
from features.objects import Objects
from clean.stabilize import Stabilize

if __name__ == "__main__":
    
    motion_detector = Motion(None)
    object_detector = Objects(None)

    # TODO - calculate the total motion before hand and identify the
    #        footage that is too shaky to be used. That way we can
    #        skip the stabilization step and save time.
    stabilize = Stabilize(None)

    capture = cv2.VideoCapture('../media/test_original.mp4')

    stabilize(capture)

    #capture.seek(0)

    #motion_detector(capture)

    #capture.set(cv2.CAP_PROP_FPS, 0.1)

    capture.release()