import cv2


class Objects():

    def __init__(self, config):
        self.config = config


    def __call__(self, frame):
        resize = self.config.get('resize')
        resized = cv2.resize(frame, (0,0), fx=resize, fy=resize, interpolation = cv2.INTER_AREA)      
        model = cv2.ximgproc.segmentation.createSelectiveSearchSegmentation()
        model.setBaseImage(resized)
        #ss.switchToSelectiveSearchFast()
        #ss.switchToSelectiveSearchFast(base_k=1000, inc_k=1000, sigma = 0.8)
        model.switchToSingleStrategy()
        rects = model.process()
        
        # cast to type float32
        rects = rects.astype('float32')
        
        # adjust bounding box to original image size
        rects[:, 0] /= resize
        
        return rects