from flask import render_template
from flask import Blueprint
import os

html_api = Blueprint('html_api', __name__)


@html_api.route('/')
def index():
    return render_template('recommender.html', maps_api_key=os.environ['maps_api_key'])
