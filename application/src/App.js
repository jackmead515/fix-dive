import { PureComponent } from "react";

import Button from '@mui/material/Button';

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
            </div>
        )
    }
}