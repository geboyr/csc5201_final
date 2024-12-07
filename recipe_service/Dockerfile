# Use an official Python runtime as an image
FROM python:3.9

# Set the working directory within the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the working directory
COPY . /app

# Expose the port that Flask will run on (this should match the service definition in docker-compose.yml)
EXPOSE 5000

# Run the specific Flask app
CMD ["python", "recipe_service.py"]
#CMD ["gunicorn", "--bind", "0.0.0.0:5001", "recipe_service:app"]
