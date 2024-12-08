from flask import Flask, request, redirect, url_for, render_template_string, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import time
import os

app = Flask(__name__)

# Database
DB_USERNAME = os.getenv('MYSQL_ROOT_USERNAME')
DB_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@db/ingredients_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# API / Auth
API_KEY = os.getenv('OUTGOING_API_KEY', '')
VALID_INCOMING_API_KEYS = os.getenv('VALID_INCOMING_API_KEYS', '').split(',')
RECIPE_API_URL = "http://recipe-service:5001/generate_recipe"
STATS_API_URL = "http://stats-service:5002/record_stat"

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

def check_api_key(request):
    api_key = request.headers.get('Authorization')
    if api_key and api_key.startswith('ApiKey '):
        provided_key = api_key.split(' ')[1]
        if provided_key in VALID_INCOMING_API_KEYS:
            return None  # Authorized
    return jsonify({'error': 'Unauthorized'}), 401

def record_stat(service_name, response_time):
    headers = {'Authorization': f'ApiKey {API_KEY}', 'Content-Type': 'application/json'}
    data = {'service_name': service_name, 'response_time': response_time}
    try:
        response = requests.post(STATS_API_URL, json=data, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f'Failed to record stat: {e}')

form_html = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>AI Recipe Generator</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  </head>

  <body class="bg-light">
    <div class="container py-4">
      <h1 class="mb-4">AI Recipe Generator</h1>

      <!-- Form to add a new ingredient -->
      <div class="card mb-4">
        <div class="card-header">Add a New Ingredient</div>
        <div class="card-body">
          <form action="/ui" method="POST" class="form-inline">
            <label for="name" class="sr-only">Ingredient Name:</label>
            <input type="text" id="name" name="name" class="form-control mr-2" placeholder="Enter ingredient name" required>
            <button type="submit" class="btn btn-primary">Add Ingredient</button>
          </form>
        </div>
      </div>

      <!-- Display existing ingredients -->
      <div class="card mb-4">
        <div class="card-header">Existing Ingredients</div>
        <div class="card-body" style="overflow-y: auto; resize: vertical; height: 200px; min-height: 100px; border: 1px solid #ccc; padding: 10px;">
          <ul class="list-group">
            {% for ingredient in ingredients %}
              <li class="list-group-item d-flex justify-content-between align-items-center">
                {{ ingredient.name }}
                <form action="/ingredients/{{ ingredient.id }}" method="POST" style="display:inline;">
                  <input type="hidden" name="_method" value="DELETE">
                  <button type="submit" class="btn btn-sm btn-danger">Delete</button>
                </form>
              </li>
            {% endfor %}
          </ul>
        </div>
      </div>

      <!-- Button to generate a recipe -->
      <div class="mb-4">
        <h2>Generate Recipe</h2>
        <button class="btn btn-success" onclick="generateRecipe()">Generate Recipe</button>
      </div>

      <!-- Spinner (hidden by default) -->
      <div id="spinner" class="text-center mb-4" style="display:none;">
        <div class="spinner-border text-primary" role="status">
          <span class="sr-only">Loading...</span>
        </div>
        <p>Generating your recipe, please wait...</p>
      </div>

      <!-- Area to display the generated recipe -->
      <div id="recipeOutput"></div>

      <!-- Area for links to stats and dashboard -->
      <div class="card mb-4">
        <div class="card-header">Admin Links</div>
        <div class="card-body">
          <ul>
            <li><a id="stats-link" href="#">View Stats</a></li>
            <li><a id="dash-link" href="#">View Dashboard</a></li>
          </ul>
        </div>
      </div>
      
    </div>

    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
      function generateRecipe() {
        document.getElementById('spinner').style.display = 'block';
        document.getElementById('recipeOutput').innerHTML = "";

        fetch('/recipe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
        })
        .then(response => response.json())
        .then(data => {
          document.getElementById('spinner').style.display = 'none';
          if (data.recipe) {
            document.getElementById('recipeOutput').innerHTML = `
              <div class="card">
                <div class="card-header">Generated Recipe</div>
                <div class="card-body">
                  <pre>${data.recipe}</pre>
                </div>
              </div>
            `;
          } else if (data.error) {
            document.getElementById('recipeOutput').innerHTML = "<div class='alert alert-danger'>Error: " + data.error + "</div>";
          }
        })
        .catch(error => {
          document.getElementById('spinner').style.display = 'none';
          document.getElementById('recipeOutput').innerHTML = "<div class='alert alert-danger'>Error generating recipe: " + error + "</div>";
        });
      }
    </script>
    <script>
        // Get the current host (IP or domain)
        const host = window.location.hostname;

        // Construct the URLs with the same hostname, different port, and specific routes
        document.getElementById('stats-link').href = `http://${host}:5002/stats`;
        document.getElementById('dash-link').href = `http://${host}:5002/dash`;
    </script>
  </body>
</html>
"""

# UI ROUTE
@app.route('/ui', methods=['GET', 'POST'])
def ui_home():
    start_time = time.time()

    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            headers = {
                'Authorization': f'ApiKey {API_KEY}',
                'Content-Type': 'application/json'
            }
            response = requests.post(
                "http://localhost:5000/ingredients",
                headers=headers,
                json={'name': name}
            )
        response_time = time.time() - start_time
        record_stat('ingredient_service.ui_home', response_time)
        return redirect(url_for('ui_home'))

    ingredients = Ingredient.query.all()
    response_time = time.time() - start_time
    record_stat('ingredient_service.ui_home', response_time)
    return render_template_string(
        form_html,
        ingredients=ingredients
    )


# API ROUTES
@app.route('/ingredients', methods=['GET'])
def list_ingredients():
    start_time = time.time()
    auth_response = check_api_key(request)
    if auth_response:
        response_time = time.time() - start_time
        record_stat('ingredient_service.list_unauthorized', response_time)
        return auth_response

    ingredients = Ingredient.query.all()
    output = [{'id': i.id, 'name': i.name} for i in ingredients]
    response_time = time.time() - start_time
    record_stat('ingredient_service.list', response_time)
    return jsonify({'ingredients': output}), 200

@app.route('/ingredients', methods=['POST'])
def add_ingredient():
    start_time = time.time()
    auth_response = check_api_key(request)
    if auth_response:
        response_time = time.time() - start_time
        record_stat('ingredient_service.add_unauthorized', response_time)
        return auth_response

    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Name not provided'}), 400

    new_ingredient = Ingredient(name=data['name'])
    db.session.add(new_ingredient)
    db.session.commit()

    response_time = time.time() - start_time
    record_stat('ingredient_service.add', response_time)

    return jsonify({
        'message': 'Ingredient added',
        'id': new_ingredient.id
    }), 201

@app.route('/ingredients/<int:id>', methods=['DELETE', 'POST'])
def delete_ingredient(id):
    start_time = time.time()
    auth_response = check_api_key(request)
    if auth_response and request.method == 'DELETE':
        response_time = time.time() - start_time
        record_stat('ingredient_service.delete_unauthorized', response_time)
        return auth_response

    ingredient = Ingredient.query.get(id)
    if ingredient:
        db.session.delete(ingredient)
        db.session.commit()
        response_time = time.time() - start_time
        record_stat('ingredient_service.delete', response_time)
        if request.method == 'DELETE':
            return '', 204
        else:
            return redirect(url_for('ui_home'))
    else:
        return jsonify({'error': 'Not found'}), 404

@app.route('/recipe', methods=['POST'])
def generate_recipe_endpoint():
    start_time = time.time()
    headers = {'Authorization': f'ApiKey {API_KEY}'}
    try:
        response = requests.post(RECIPE_API_URL, headers=headers)
        response.raise_for_status()
        recipe = response.json().get('recipe', 'No recipe generated.')
    except requests.exceptions.RequestException as e:
        recipe = f'Error generating recipe: {e}'
    response_time = time.time() - start_time
    record_stat('ingredient_service.generate_recipe', response_time)
    return jsonify({'recipe': recipe})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
