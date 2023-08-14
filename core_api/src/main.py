# generate Flask boilerplate

from flask import Flask

app = Flask(__name__)

import config

config.initialize()

from routes import upload

app.register_blueprint(upload.mod)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
