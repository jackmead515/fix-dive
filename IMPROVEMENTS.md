# Detect Chunk Size

From the raw video, asset the size (resolution, fps, etc) of the video and
determine the optimal size to reduce it down to in order to get the best
playback and processing performance.

# Provide Loading Progress

Determine the progress of the chunking and processing of the video and provide
that to the user.

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
