# Fix the Progress / Frame Count Issue

Since the framerate is not constant and changes just a little
bit between frames, the react-player (since it only gives back progress in time)
will not be able to calculate the correct frame number. Find out how to change
this by either utilizing a progress column in the feature datasets or by getting
the frame number from react-player (somehow)

What I should do is add a 'progress' column from 0-1 in the feature datasets
that uses the frame_number / total_frames to calculate the progress. Then in
the frontend I do the same thing but with the duration and current time.

# Detect Chunk Size

From the raw video, asset the size (resolution, fps, etc) of the video and
determine the optimal size to reduce it down to in order to get the best
playback and processing performance.

# Provide Loading Progress

Determine the progress of the chunking and processing of the video and provide
that to the user.

With processing, I can report back the progress of each Dask task via counting
the amount of frames processed and then using the total amount of Dask tasks
to determine overall progress.

With ffmpeg, I may be able to calculate how long the chunking is taking by reading
from the ffmpeg standard output.

# Sample Video Stream to Different 5-10 Second Clips

We want to sample the video stream to display to the user a 5-10 second clip of
different hot spots in the video. Using preliminary analysis, we can determine
the most interesting parts of the video and display those to the user. From there
we can then further process the video to get more detailed information.

# FAST-SAM for instance segmentation from user input

The user could provide a bounding box or point to an
animal in the video that they like or want to track.

# Generate ML reports with juypter notebook

We could render a juypter notebook into HTML that shows a
report on the dive footage statistics that it has discovered.
Using pretty-juypter or mercury would also help to make it
more interactive or pretty.

# Interactive feedback on the UI

Using eye tracking movement, we could find the most common points where a user
is looking and feed that into the SAM segmentation model. This will create a
much more hands free experience.
