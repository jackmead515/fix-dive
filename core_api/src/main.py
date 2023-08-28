# generate Flask boilerplate
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

import config

config.initialize()

from routes.project import get_project_data
from routes.project import upload_eye_tracking
from routes import upload

app.register_blueprint(upload.mod)
app.register_blueprint(get_project_data.mod)
app.register_blueprint(upload_eye_tracking.mod)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
