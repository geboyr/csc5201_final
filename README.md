# csc5201_final

## Description of Application:
AI Recipe Generator allows you add (and remove) ingredients you have on hand, and ask ChatGPT for a recipe that uses some or all of those ingredients.

## Digital Ocean Installation Instructions
1. Sign up for a Digital Ocean account. https://cloud.digitalocean.com/ 

2. Create a new droplet with Docker. (Click the blue “Create Docker Droplet” button). https://marketplace.digitalocean.com/apps/docker

3. Down under the Size section, you can pick the most basic (shared CPU), regular SSD, cheapest CPU option (currently $6 / month).

4. Scroll down and type in a password you’ll remember.

5. And click Create Droplet!

6. Wait a minute for the droplet to be created, then copy its IP address and open your terminal.

7. In your terminal Type: ssh root@IP_ADDRESS_YOU_COPIED

8. Then enter your password.

9. Now, let’s get the project’s code: git clone https://github.com/geboyr/csc5201_final

10. Go into the folder using the command: cd csc5201_final

10. Create a .env file (I like to use nano) and fill in the API keys you have. You’ll copy the contents of env-example.txt and fill it in with the appropriate API keys & passwords. Default user/pw is root/root for mysql root username & password, and my_user and user for mysql user and password. (I would recommend changing those when you have a moment). But you'll also need to get an OpenAI API key, and create your own longer API keys for the various services.

12. Then, you can run: docker compose up --build (You might need to retype the dash's manually if you are copying/pasting into terminal).

13. Wait a few minutes for everything to start, and for the load test to run.

14. Once the logs have died down (and you see the load test results), you can access the app at the following URLs:
- http://<your-droplet-ip-address>:5000/ (To manage your ingredients and generate recipes)
- http://<your-droplet-ip-address>:5002/stats (To view the raw stats of service calls and response times)
- http://<your-droplet-ip-address>:5002/dash (To view a nice dashboard of service calls and response times)

## API Overview
### Ingredients Service / API
This API allows you to manage ingredients and generate recipes based on available ingredients. It provides endpoints to list, add, delete ingredients, and to generate recipes (by calling a separate service).

#### 1. List Ingredients
GET /ingredients

Returns a list of all ingredients.

Request
Headers:
{
  "Authorization": "ApiKey <your_api_key>"
}

Response
Status 200
{
  "ingredients": [
    { "id": 1, "name": "Tomato" },
    { "id": 2, "name": "Onion" }
  ]
}


#### 2. Add Ingredient
POST /ingredients

Adds a new ingredient to the database.

Request
Headers:
{
  "Authorization": "ApiKey <your_api_key>",
  "Content-Type": "application/json"
}

Body:
{
  "name": "Garlic"
}

Response
Status 201
{
  "message": "Ingredient added",
  "id": 3
}


#### 3. Delete Ingredient
DELETE /ingredients/<id>

Deletes an ingredient by its ID.

Request
Replace <id> in the URL with the ingredient's ID.

Example URL:
http://localhost:5000/ingredients/3
Headers:
{
  "Authorization": "ApiKey <your_api_key>"
}

Response
Status 204: No content on success.
Status 404: Ingredient not found.

### Recipe Service / API
This API generates recipes based on available ingredients by querying an OpenAI model. It integrates with other services, such as the ingredient service and a stats service, to provide functionality and log performance metrics.

#### 1. Generate Recipe
POST /generate_recipe

Generates a recipe based on available ingredients fetched from the ingredient service.

Request
Headers:
{
  "Authorization": "ApiKey <your_api_key>"
}

Response
Status 200
{
  "recipe": "Tomato soup: Use Tomato and Onion."
}

Status 401: Unauthorized if the API key is invalid or missing.
{
  "error": "Unauthorized"
}

Status 500: If there’s an error fetching ingredients or calling the OpenAI API.
{
  "error": "Failed to fetch ingredients: <error_message>"
}

### Stats Service / API
The Stats Service API records, displays, and visualizes service performance metrics, such as response times and service call counts. It provides a simple HTML-based stats view and an interactive dashboard powered by Dash.

#### 1. Record Stat
POST /record_stat

Records a service's response time and associates it with a timestamp.

Request
Headers:
{
  "Authorization": "ApiKey <your_api_key>",
  "Content-Type": "application/json"
}

Body:
{
  "service_name": "ingredient_service",
  "response_time": 0.123
}

Response
Status 201: Stat successfully recorded.
{
  "message": "Stat recorded successfully"
}

Status 400: Invalid request data.
{
  "error": "Invalid data"
}

Status 401: Unauthorized if the API key is invalid or missing.
{
  "error": "Unauthorized"
}


#### 2. View Stats
GET /stats
Displays a simple HTML table of all recorded stats.
Response
Renders an HTML page with columns:
ID: Unique stat ID.
Service Name: Name of the service.
Timestamp: Time the stat was recorded.
Response Time (s): Recorded response time.

#### 3. Dashboard
GET /dash
Displays an interactive dashboard with visualizations of service usage and response times.
Visualizations
Response Time Over Last 6 Hours: A line graph showing response times by service.
Number of Service Calls: A bar chart showing the count of calls per service.

### API Authentication
All API endpoints require an Authorization header with an API key:
{
  "Authorization": "ApiKey <your_api_key>"
}
