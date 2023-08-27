import { PureComponent } from "react";

import ReactPlayer from 'react-player'
import * as d3 from 'd3';

import './App.css';

function convertProgressToFrameNumber(playedSeconds, fps) {
  return Math.floor(playedSeconds * fps);
}

export default class App extends PureComponent {

  constructor(props) {
    super(props);
    
    this.state = {
      duration: undefined,
      progress: undefined,
      frameNumber: undefined,
      videoDetails: undefined
    }
  }

  componentDidUpdate() {
    const { duration, progress, videoDetails } = this.state;

    if (duration && progress && videoDetails) {
      const frameRate = parseInt(videoDetails.streams[0].r_frame_rate.split('/')[0]);
      const frameNumber = convertProgressToFrameNumber(progress.playedSeconds, frameRate);
      this.setState({ frameNumber: frameNumber });
    }
  }

  componentDidMount() {
    this.renderSeekBox();

    const url = 'http://172.23.0.100:30140/fix-dive-storage/projects/1234567890/playlists/low_details.json'

    fetch(url)
      .then(response => response.json())
      .then(data => {
        this.setState({ videoDetails: data });
      });
  }

  renderSeekBox() {
    const bbox = d3.select("#seekbox").node().getBoundingClientRect();
    const width = bbox.width;
    const height = bbox.height;
  }

  render() {
    return (
      <div>
        <div>
          <p>{this.state?.frameNumber} frame</p>
          <p>{this.state?.progress?.playedSeconds} / {this.state?.duration} seconds</p>
        </div>
        <div className="player__container">
          <ReactPlayer
            url='http://172.23.0.100:30140/fix-dive-storage/projects/1234567890/playlists/low.m3u8'
            controls={true}
            pip={false}
            onStart={() => console.log('onStart')}
            onPlay={() => console.log('onPlay')}
            onPause={() => console.log('onPause')}
            onBuffer={() => console.log('onBuffer')}
            onBufferEnd={() => console.log('onBufferEnd')}
            onEnded={() => console.log('onEnded')}
            onProgress={(e) => this.setState({ progress: e })}
            onDuration={(e) => this.setState({ duration: e })}
            width='100%'
            height='100%'
            config={{
              file: {
                forceHLS: true
              }
            }}
          />
        </div>
        <div className="seek__container">
          <div className="seek__box" id="seekbox">

          </div>
        </div>
      </div>
    )
  }
}