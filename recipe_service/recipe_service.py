import os
from openai import OpenAI
import requests
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# OpenAI
open_ai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=open_ai_api_key)

# API Stuff
API_KEY = os.getenv('OUTGOING_API_KEY', '')
VALID_INCOMING_API_KEYS = os.getenv('VALID_INCOMING_API_KEYS', '').split(',')

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
        response = requests.post('http://stats-service:5002/record_stat', json=data, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f'Failed to record stat: {e}')

@app.route('/generate_recipe', methods=['POST'])
def generate_recipe():
    start_time = time.time()
    auth_response = check_api_key(request)
    if auth_response:
        return auth_response
    try:
        headers = {'Authorization' : f'ApiKey {API_KEY}'}
        response = requests.get('http://ingredients-service:5000/ingredients', headers=headers)
        response.raise_for_status()
        ingredients_data = response.json()
        ingredient_list = [item['name'] for item in ingredients_data['ingredients']]
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch ingredients: {str(e)}'}), 500

    prompt = f"Below you will find a list of ingredients I have available to me. Please suggest a recipe using these ingredients. You do not need to use all of the ingredients that I have on hand, but you can't use others not in my list. The ingredients I have are: {', '.join(ingredient_list)}."

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4o-mini",
            max_tokens=750,
            temperature=0.7
        )
        recipe = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({'error': f'Error calling OpenAI API: {str(e)}'}), 500

    response = jsonify({'recipe': recipe})
    response_time = time.time() - start_time
    record_stat('recipeService_generateRecipe', response_time)
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
