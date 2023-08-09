
- Upload raw video files

The data will have to be uploaded to remote server. (S3 would be best).
Should probably be a server that uploads data and then moves it over to S3.
Feedback should be given to show the user how long it's going to take to upload it.

- Concatenate videos into video segment chunks

For the convenience of the algorithm, the videos should be split up into equal sized chunks
and labeled chronologically so the time can be calculated. This will improve multiprocessing
capabilities and make it easier to work with the data.

- Run preliminary algorithms

Object detection to identify hot spots, running kmeans to identify different
environments or features in the footage to help with scene detection, anaylzing motion
in order to suggest stabilization parameters, Segment anything model might be useful
to identify different animals in the video. Perhaps a classification model exists that can
identify if an instance is an animal or not.

- Prompt user for parameters 

At this point, the user might want to be prompted to adjust parameters. Segments of the
video could be shown from the kmeans, object detection, and motion analysis to help trim
down the video into the most interesting parts. A timeline could be shown that helps the user
to scan to the video segments. They could also highlight certain frames or segment lengths of
footage that they find interesting or want to be included in the final video.
 
- Run main algorithms

Using the data from the preliminary algorithms, the parameter adjustments, and the user annotations,
the main algorithms can run to stabilize, color correct, enhance, and condense the video. Feature detection can be used on the user annotations to find similar features in the video to keep, stabilization can be used to stabilize the most unstable footage, color correction can be applied if desired, and super resolution may be used if the user wants to enhance the video. More segmentation can be done in order to generate an anaylsis of the video to show the user what the video contains.

- Notify user

During the process, the user should be notified of the progress but also
able to view past videos that have been generated. The user should have a very
easy to read dialog that will assist them in understanding what is happening and
why it is happening.

