# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Expose port 8000 for Gunicorn
EXPOSE 8000

# Define environment variables
ENV FLASK_APP=app.py

# Run the command to start Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers", "3", "app:app"]