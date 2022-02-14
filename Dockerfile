FROM python:3.7

# Run commands from /app directory inside container
WORKDIR /app

# add the current directory to the container as /app
ADD . /app

# Copy requirements from local to docker image
COPY requirements.txt /app

# Install the dependencies in the docker image
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

# unblock port 80 for the Flask app to run on
EXPOSE 80

# Copy everything from the current dir to the image
COPY . .