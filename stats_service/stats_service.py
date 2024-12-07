from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, timedelta
import time
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

app = Flask(__name__)

# Database
DB_USERNAME = os.getenv('MYSQL_ROOT_USERNAME')
DB_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD')
DB_HOST = os.getenv('DATABASE_HOST', 'db')
DB_NAME = os.getenv('DATABASE_NAME', 'stats_db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# API
VALID_INCOMING_API_KEYS = os.getenv('VALID_INCOMING_API_KEYS', '').split(',')

class Stat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    response_time = db.Column(db.Float, nullable=False)

def check_api_key(request):
    api_key = request.headers.get('Authorization')
    if api_key and api_key.startswith('ApiKey '):
        provided_key = api_key.split(' ')[1]
        if provided_key in VALID_INCOMING_API_KEYS:
            return None  # Authorized
    return jsonify({'error': 'Unauthorized'}), 401

@app.route('/record_stat', methods=['POST'])
def record_stat():
    auth_response = check_api_key(request)
    if auth_response:
        return auth_response

    data = request.get_json()
    service_name = data.get('service_name')
    response_time = data.get('response_time')

    if not service_name or response_time is None:
        return jsonify({'error': 'Invalid data'}), 400

    new_stat = Stat(service_name=service_name, response_time=response_time)
    db.session.add(new_stat)
    db.session.commit()

    return jsonify({'message': 'Stat recorded successfully'}), 201

@app.route('/stats', methods=['GET'])
def view_stats():
    stats = Stat.query.order_by(Stat.timestamp.desc()).all()

    html = """
    <!doctype html>
    <html lang="en">
      <head>
        <title>Service Usage Statistics</title>
      </head>
      <body>
        <h1>Service Usage Statistics</h1>
        <table border="1">
          <tr>
            <th>ID</th>
            <th>Service Name</th>
            <th>Timestamp</th>
            <th>Response Time (s)</th>
          </tr>
          {% for stat in stats %}
          <tr>
            <td>{{ stat.id }}</td>
            <td>{{ stat.service_name }}</td>
            <td>{{ stat.timestamp }}</td>
            <td>{{ stat.response_time }}</td>
          </tr>
          {% endfor %}
        </table>
      </body>
    </html>
    """
    return render_template_string(html, stats=stats)

# Dash
dash_app = Dash(__name__, server=app, url_base_pathname='/dash/')

def get_data():
    query = db.session.query(Stat).all()
    df = pd.DataFrame([{
        'id': s.id,
        'service_name': s.service_name,
        'timestamp': s.timestamp,
        'response_time': s.response_time
    } for s in query])
    return df

dash_app.layout = html.Div([
    html.H1("Service Usage Dashboard", style={'text-align': 'center'}),

    html.Div([
        html.H2("Response Time"),
        dcc.Graph(id='response-time-graph')
    ]),

    html.Div([
        html.H2("Number of Service Calls"),
        dcc.Graph(id='counts-graph')
    ]),

    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # Update every minute
        n_intervals=0
    )
])

@dash_app.callback(
    [Output('counts-graph', 'figure'),
     Output('response-time-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n):
    df = get_data()

    if df.empty:
        fig_counts = px.bar(title='No data available')
        fig_response = px.line(title='No data available')
        return fig_counts, fig_response

    service_counts = df.groupby('service_name').size().reset_index(name='count')
    fig_counts = px.bar(service_counts, x='service_name', y='count', title='Number of Calls per Service')

    # Filter the data for last 6 hours
    cutoff = datetime.utcnow() - timedelta(hours=6)
    df_recent = df[df['timestamp'] >= cutoff]

    if df_recent.empty:
        fig_response = px.line(title='No data in the last 6 hours')
    else:
        fig_response = px.line(df_recent, x='timestamp', y='response_time', color='service_name',
                               title='Response Time Over Last 6 Hours')

    return fig_counts, fig_response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)
