# Podcast API


## Getting Started
### Software Requirements

You will need to have [Docker](https://www.docker.com/community-edition#/download) installed in order to run the stack.


### Docker Compose

To build the containers:
```
docker-compose build
```

To start the containers in blocking mode:
```
docker-compose up
```

To start the containers in daemon mode (-d):
```
docker-compose up -d
```

To tail the logs:
```
docker-compose logs -f [optional name of container]
```

To restart one or all of the containers:
```
docker-compose restart [optional name of container]
```

### Accessing the Dashboard API

After spinning up the docker containers, the Dashboard API can be reached at http://localhost:8080.
The OpenAPI schema can be accessed at http://localhost:8080/ui/.