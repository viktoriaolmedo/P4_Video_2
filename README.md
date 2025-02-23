We use an API we created las trimester.
We make sure it's running using this command: fastapi dev main.py

Then we need to put it inside a docker. For that, we create a Dockerfile with all the dependencies and run the Docker container using the image. 
We build the container with this command: docker build -t myfastapi_container .
We run the container, for example, like this: docker run -d -p 80:8000 --name myfastapi_container myfastapi_container
We can enter from here http://localhost:80 or to see it visually here: http://127.0.0.1:8000/docs
