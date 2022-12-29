# Fix-Dive

Automatically fix dive footage that sucks.

## About

I love taking footage of my scuba diving or free diving. But I absolutely suck at it. It's easy to stabilize things and get the right white balance in the air. But that all changes when you go underwater. Red light almost disappears. Stabilization is nearly impossible without a complicated rig. You can buy a more expensive camera to get auto white-balance, proper filters, more resolution and higher clarity, a red light dive light, etc, ORRRR... you could just buy compute power in a GPU and run this codebase on your crappy dive footage like me :)

I have a $100 camera with a dumbass selfie stick and pretty beginner scuba dive gear. But, after training for a while and getting really precise with my buoyancy, I can capture enough raw footage to be useful.

## Filters

- Step 1 is to run object detection over my dive footage and compile a set of footage that only has nice pretty fishes and stuff in it. The threshold for objects detected can be tuned.

- Step 2 is to stabilize that footage. My buoyancy is pretty on point. I can suspend myself upside down with my mask only centimeters from a coral branch, but, still doesn't seem to matter as it's still shaky without some stabilizing hardware. https://github.com/AdamSpannbauer/python_video_stab

- Step 3 will then color correct the footage. This works by determining the red color frame by frame and working to restore the red color to a certain specifiable threshold.
https://github.com/jackmead515/dive-color-corrector

- Step 4 will then take the resulting video and run super resolution AI on it. This is the most demanding step, but a very important one. It uses a GAN network to deblur and clarify the imagery. This can quite literally turn a $100 cheapo Alibaba video into a $500 GoPro HERO 10 video. https://github.com/Lornatang/SRGAN-PyTorch

## Example Config

```
detect:
    type: selective_search
    config:
        max_objects: 100
        min_objects: 20
        overlap: 1s
        fps: 5
        base_k: 1000
        inc_k: 1000
        sigma: 0.8
        scale: 0.2
stabilize:
    tuneable: 4
    filter: extend
color:
    min_red_threshold: 60
enhance:

```

### Features And Stabilization

#### Basic Conversions

Convert from MOV to MP4
```
ffmpeg -i test_columbia.MOV -qscale 0 -vcodec copy test_columbia.mp4
```

Add checkpointing so that if the process stops, it can be restarted where
it left off.
```
checkpoint.json
{
    "step": "transform",
    "cache": "./cache.npy"
}
```

Stack two videos next to eachother
```
ffmpeg -i ../media/test2_original.mp4 -i stablized_video.mp4 -filter_complex hstack -c:v libx264 output.mp4
```


#### Object / Motion Detection

Using the LK method, are there points of interest that coorlate
to interesting footage?

If we use a Kalman Filter on the points of interest, is it possible that
we can detect the points of interest as a contiguous line of travel that
corolates to interesting footage? (maybe an animal or something)

Can we anaylze the motion detected at different quadrants of a footage (or the overall footage) to corolate interesting footage?

Can I detect the contours of the images to understand if the footage is interesting? Can I utilize color masking on the footage and then apply object detection?

#### Stabilization

How can we smooth out portions of the stabilized footage such that we don't "over stablize"?

If I tune the stabilization factor higher, I should expect more stable footage, but less footage to view. If I tune it lower, I should expect less stable footage but more in the view port.

If I tune the zoom factor higher, I should expect less in the view port but I can tune the stabilization factor higher. If I tune the zoom factor lower, then I can't increase the stabilization factor as much.

#### Cleaning Artifacts

How can I apply a background to the empty space that occurs after stabilization of the footage? Can I apply a median color profile? Can I use generative networks to fill in the rest of the footage?

How can I remove debre in the footage like marine snow and other oddies? Can a neural network auto detect and clear that? "noise" filter?

How can I remove longer sections of uninteresting footage while making the footage still viewable? Is there a threshold of duration that I can arguably remove? Should I apply scene transitions after removing those sections?

How can I remove the timestamp from the footage if I don't want it there?

#### Beautify

How can I enhance the resolution of the footage? Super Resolution AI?

Can I annotate the image with other metadata? Or hotspots?

How can I auto-correct the lack of red color in the footage?

### Links

https://www.analyticsvidhya.com/blog/2018/10/a-step-by-step-introduction-to-the-basic-object-detection-algorithms-part-1/?utm_source=blog&utm_medium=vehicle-detection-opencv-python

https://www.analyticsvidhya.com/blog/2020/04/vehicle-detection-opencv-python/

https://stackoverflow.com/questions/47483951/how-to-define-a-threshold-value-to-detect-only-green-colour-objects-in-an-image



