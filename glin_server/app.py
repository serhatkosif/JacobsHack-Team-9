import os

from flask import Flask, render_template
import pandas as pd
import json
import plotly
import plotly.express as px

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    @app.route('/')
    def notdash():
        df = pd.DataFrame({
            'Fruit': ['Apples', 'Oranges', 'Bananas', 'Apples', 'Oranges', 
            'Bananas'],
            'Amount': [4, 1, 2, 2, 4, 5],
            'City': ['SF', 'SF', 'SF', 'Montreal', 'Montreal', 'Montreal']
        })
        fig = px.bar(df, x='Fruit', y='Amount', color='City', 
            barmode='group')
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        
        return render_template('notdash.html', graphJSON=graphJSON)

    return app

    