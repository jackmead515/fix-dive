import { PureComponent } from "react";

import Button from '@mui/material/Button';
import ReactPlayer from 'react-player'

export default class App extends PureComponent {
    render() {
        return (
            <div>
                <h1>App</h1>
                <Button variant="contained">
                  New Dive
                </Button>
                <Button variant="contained">
                  Old Dives
                </Button>
                <ReactPlayer
                  url='http://172.23.0.100:30140/fix-dive-storage/projects/1234567890/playlists/9a46be74ed065d8faf431f01c4ecc1a6-205/view/video.m3u8'
                  controls={true}
                  onStart={() => console.log('onStart')}
                  onPlay={() => console.log('onPlay')}
                  onPause={() => console.log('onPause')}
                  onBuffer={() => console.log('onBuffer')}
                  onBufferEnd={() => console.log('onBufferEnd')}
                  onEnded={() => console.log('onEnded')}
                  width='100%'
                  config={{
                    file: {
                      forceHLS: true
                    }
                  }}
                />
            </div>
        )
    }
}