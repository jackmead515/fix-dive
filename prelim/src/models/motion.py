import cv2

from util.profile_time import profile_time

class Motion():

    def __init__(self, config):
        self.config = config
        self.prev_frame = None

    @profile_time('motion')
    def __call__(self, frame):
        if self.prev_frame is None:
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return None

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(self.prev_frame, gray_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        self.prev_frame = gray_frame

        # window_width = math.ceil(frame.shape[0] * 0.1)
        # window_height = math.ceil(frame.shape[1] * 0.1)
        # grid_id = 0
        # for x in range(0, frame.shape[0], window_width):
        #     for y in range(0, frame.shape[1], window_height):
        #         xx = x + window_width
        #         yy = y + window_height
        #         window = flow[x:xx, y:yy]
        #         median_motion = np.median(window)
        #         data.append([frame_count, grid_id, median_motion])
        #         grid_id += 1

        return flow