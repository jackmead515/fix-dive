import cv2

class Motion():

    def __init__(self, config):
        self.config = config
        self.prev_frame = None

    def __call__(self, frame):
        if self.prev_frame is None:
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return None

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(self.prev_frame, gray_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        self.prev_frame = gray_frame

        return flow