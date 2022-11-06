# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

# Flask modules
from flask   import render_template, request
from jinja2  import TemplateNotFound

import pickle
import requests as req

import random

# App modules
from apps import app

import pandas as pd
import json
import plotly
import plotly.express as px

# App main route + generic routing
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path>')
def index(path):

    try:

        # Detect the current page
        segment = get_segment( request )

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template( 'home/' + path, segment=segment, graphJSON=make_plot(get_info()) )
    
    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

@app.route('/address', methods=["GET", "POST"])
def cb_address():

    config = get_info()
    config["Address"] = request.args.get('data')

    update_address(config)

    commit_info(config)

    return make_plot(config)

@app.route('/radius', methods=["GET", "POST"])
def cb_radius():

    config = get_info()
    update_address(config)

    config["Radius"] = float(request.args.get('data'))

    commit_info(config)

    return make_plot(config)

@app.route('/size', methods=["GET", "POST"])
def cb_size():

    config = get_info()
    update_address(config)

    config["Size"] = float(request.args.get('data'))

    commit_info(config)

    return make_plot(config)

def make_plot(config):

    print("Making plot")
    df = pd.DataFrame({
        'Fruit': ['Apples', 'Oranges', 'Bananas', 'Apples', 'Oranges', 
        'Bananas'],
        'Amount': [4, 1, 2, 2, 4, random.random()],
        'City': ['SF', 'SF', 'SF', 'Montreal', 'Montreal', 'Montreal']
    })
    fig = px.bar(df, x='Fruit', y='Amount', color='City', 
        barmode='group')

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def get_segment( request ): 

    try:
        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment    

    except:
        return None  

def get_info():

    try:
        config = pickle.load(open("glin_config.pickle",'rb'))
    except:
        config = {"Address":"Jacobs University", "Radius": 5, "Size":0.5}

    return config

def commit_info(config):

    pickle.dump(config, open("glin_config.pickle",'wb'))

def update_address(config):
    
    resp = req.get("https://nominatim.openstreetmap.org/search", params={"q":config["Address"],"format":"json"})
    resp = resp.json()

    if len(resp) == 0:
        print("There is no address found")
        return
    
    info = resp[0]

    config["Center"] = {"lat": float(info["lat"]), "lon": float(info["lon"])}
