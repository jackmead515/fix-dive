import React from 'react';
import { Button } from '@mui/material';
import ReactPlayer from 'react-player'
import * as d3 from 'd3';

import './App.css';

function convertProgressToFrameNumber(playedSeconds, fps) {
  return Math.floor(playedSeconds * fps);
}

const contains = (x, y, w, h, point) => {
  return x <= point[0] && point[0] <= x + w && y <= point[1] && point[1] <= y + h;
}

function movingAverage(array, window) {
  const result = [];
  let sum = 0;

  for (let i = 0; i < window; i++) {
    sum += array[i];
  }
  result.push(sum / window);

  for (let i = window; i < array.length; i++) {
    sum = sum - array[i - window] + array[i];
    result.push(sum / window);
  }

  return result;
}

async function fetchVideoDetails(projectId) {
  const url = `http://172.23.0.100:30140/fix-dive-storage/projects/${projectId}/playlists/low_details.json`

  return await fetch(url).then(response => response.json());
}

async function fetchHotSpotData(projectId) {
  const url = `http://127.0.0.1:8000/api/projects/${projectId}/data/preprocess?columns=frame_index,median_motion,blur,total_objects`;

  return await fetch(url).then(response => response.json());
}

export default class App extends React.PureComponent {

  constructor(props) {
    super(props);
    
    this.state = {
      videoDetails: undefined,
      hotSpotData: undefined,
      projectId: undefined,
      videoReady: false
    };

    this.videoRef = React.createRef();
    this.videoProgress = 0;
    this.seekMarker = undefined;
    this.seekXScale = undefined;
    this.eyeTrackingData = "frame_index,progress,eye_x,eye_y\n";
    this.onGazerUpdated = this.onGazerUpdated.bind(this);
  }

  componentDidMount() {
    // get project id from url query params
    const projectId = new URLSearchParams(window.location.search).get('projectId');

    if (!projectId) {
      console.error('Project ID is missing');
      return;
    }

    this.setState({ projectId: projectId }, async () => {
      const videoDetails = await fetchVideoDetails(projectId);
      const hotSpotData = await fetchHotSpotData(projectId);
      this.setState({ videoDetails, hotSpotData }, () => {
        this.initGazer();
        this.renderSeekBox();
        this.setState({ videoReady: true });
      });
    });
  }

  initGazer() {
    const webgazer = window.webgazer;

    console.log('webgazer compatability', webgazer.detectCompatibility());

    webgazer
      .showVideo(false)
      .showFaceOverlay(false)
      .showFaceFeedbackBox(false)
      .showPredictionPoints(false)
      //.applyKalmanFilter(true)
      .setRegression('ridge')
      .setGazeListener(this.onGazerUpdated)
      .begin();
  }

  uploadEyeTrackingData() {
    const { projectId } = this.state;
    const url = `http://127.0.0.1:8000/api/projects/${projectId}/upload/eye_tracking`;

    fetch(url, {
      method: 'POST',
      body: this.eyeTrackingData
    }).then(response => {
      console.log(response);
    }).catch(error => {
      console.error(error);
    });
  }

  onGazerUpdated(data, elapsedTime) {
    if (!data) {
      return;
    }

    const isFocused = document.hasFocus();
    
    const progress = this.videoRef.current.getCurrentTime();

    // browser tab is focused and video is playing
    if (isFocused && progress !== this.videoProgress) {
      const element = document.getElementById('playerbox');
      const bbox = element.getBoundingClientRect();
      const eyePos = [data.x, data.y];
      
      //const frameRate = parseInt(this.state.videoDetails.streams[0].r_frame_rate.split('/')[0]);
      //const frameNumber = convertProgressToFrameNumber(progress, frameRate);

      const duration = this.videoRef.current.getDuration();
      const progressPrecentage = progress / duration;

      if (this.seekMarker) {
        //let hlsPlayer = this.videoRef.current.getInternalPlayer('hls');
        //console.log(hlsPlayer);

        this.seekMarker
          .attr('x', this.seekXScale(progressPrecentage))
          .attr('visibility', 'visible');
      }

      // check if eye position is inside the video player
      if (contains(bbox.x, bbox.y, bbox.width, bbox.height, eyePos)) {

        // convert eye position to relative position inside the video player
        eyePos[0] = (eyePos[0] - bbox.x) / bbox.width;
        eyePos[1] = (eyePos[1] - bbox.y) / bbox.height;

        this.eyeTrackingData += `${progressPrecentage},${eyePos[0]},${eyePos[1]}\n`;
      }
    }

    this.videoProgress = progress;
  }

  renderSeekBox() {
    const { hotSpotData } = this.state;

    const x = hotSpotData.columns.find(column => column.name === 'frame_index').values;
    const by = hotSpotData.columns.find(column => column.name === 'blur').values;
    const my = hotSpotData.columns.find(column => column.name === 'median_motion').values;
    const oy = hotSpotData.columns.find(column => column.name === 'total_objects').values;

    const bbox = d3.select("#seekbox").node().getBoundingClientRect();
    const width = bbox.width;
    const height = bbox.height;
    const padding = 10;

    // const duration = this.state.videoDetails.format.duration;
    this.seekXScale = d3.scaleLinear()
      .domain([0, 1])
      .range([padding, width-padding]);

    const xScale = d3.scaleLinear()
      .domain([0, d3.max(x)])
      .range([padding, width-padding]);

    const plotLine = (x, y, color) => {
      const yScale = d3.scaleLinear()
        .domain([d3.min(y), d3.max(y)])
        .range([height-padding, padding]);

      const smoothY = movingAverage(y, 5);
      const data = x.map((d, i) => [d, smoothY[i] ? smoothY[i] : 0]);

      svg
        .append("path")
        .datum(data)  
        .attr("d", d3.line()
          .x(d => xScale(d[0]))
          .y(d => yScale(d[1]))
          .curve(d3.curveNatural)
        )
        .attr('stroke', color)
        .attr('stroke-width', '1')
        .attr('fill', 'none');
    };

    const svg = d3.select("#seekbox")
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    plotLine(x, by, '#0099ff'); // blue
    plotLine(x, my, '#ff9900'); // orange
    plotLine(x, oy, '#00ff00'); // green

    this.seekMarker = svg.append('rect')
      .attr('width', 1)
      .attr('height', height)
      .attr('fill', '#e3e3e3')
      .attr('visibility', 'hidden');
  }

  renderVideoPlayer() {
    const { projectId, videoReady } = this.state;

    if (!projectId || !videoReady) {
      return (
        <div id="playerbox" className="player__container">
        </div>
      )
    }

    const videoUrl = `http://172.23.0.100:30140/fix-dive-storage/projects/${projectId}/playlists/low.m3u8`

    return (
      <div id="playerbox" className="player__container">
        <ReactPlayer
          ref={this.videoRef}
          url={videoUrl}
          controls={true}
          pip={false}
          // onStart={() => this.setState({ playing: true })}
          // onPlay={() => this.setState({ playing: true })}
          // onPause={() => this.setState({ playing: false })}
          // onBuffer={() => this.setState({ playing: false })}
          // onEnded={() => this.setState({ playing: false })}
          // onProgress={(e) => this.setState({ progress: e })}
          // onDuration={(e) => this.setState({ duration: e })}
          progressInterval={1000}
          width='100%'
          height='100%'
          config={{
            file: {
              forceHLS: true
            }
          }}
        />
      </div>
    )
  }

  render() {
    
    return (
      <div className="app__container">
        <div className="header__container">
          <Button variant="contained" color="primary" onClick={() => this.uploadEyeTrackingData()}>
            Upload
          </Button>
          <Button variant="contained" color="primary">
            Track Your Face
          </Button>
        </div>
        {this.renderVideoPlayer()}
        <div className="seek__container">
          <div className="seek__box" id="seekbox">
          </div>
        </div>
      </div>
    )
  }
}