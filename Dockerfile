# Step 1: Use the official Python 3 image as a parent image
FROM python:3.8-slim

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Copy the dependencies file to the working directory
COPY requirements.txt ./

# Step 4: Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the content of the local src directory to the working directory
COPY . .

# Step 6: Make port 5000 available to the world outside this container
EXPOSE 5050

# Step 7: Define the command to run your app using Gunicorn with eventlet worker
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5050", "run_server:app"]

