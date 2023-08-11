import psycopg2
from flask import Blueprint, request, Response
from werkzeug.utils import secure_filename
import s3fs

import config
import util.database as database

mod = Blueprint('create_project', __name__)


def project_exists(cursor, project_name: str, username: str) -> bool:
    cursor.execute("""
        SELECT id FROM projects WHERE name = %s AND username = %s
    """, (project_name, username))
    
    project = cursor.fetchone()

    return project is not None


def create_project(cursor, project_name: str, username: str):
    cursor.execute("""
        INSERT INTO projects (name, username) VALUES (%s, %s)
    """, (project_name, username))


@mod.route('/api/project', methods=['POST'])
def upload():

    headers = request.headers

    if 'x-forwarded-email' not in headers:
        return Response('unauthorized', status=401)

    email = headers['x-forwarded-email']

    # get request json
    content = request.get_json()

    # connect to database
    connection = database.get_connection('projects')
    cursor = connection.cursor()

    if project_exists(cursor, content['name'], email):
        return Response('project already exists', status=400)
    
    create_project(cursor, content['name'], email)

    return 'OK', 200
    