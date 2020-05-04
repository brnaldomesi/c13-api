# Podcast API


## Getting Started
### Software Requirements

You will need to have [Docker](https://www.docker.com/community-edition#/download) installed in order to run the stack.

### Setting SSH Tunneling
If you're trying to access the development DB in AWS, you will need to tunnel into it.
There is a docker-compose file that adds a proxy container for this purpose, but before
you can use it, you need to modify your own SSH config appropriately.

1. Create an SSH private/public key and make sure you can access `bastion-unpriv.cadence13.io` with it.
2. Create `~/.ssh/config` if it doesn't already exist.
3. Add the following to `~/.ssh/config`:
```
Host postgres-dev-tunnel
    HostName bastion-unpriv.cadence13.io
    IdentityFile ~/.ssh/yourprivatekey
    User yourusername
    ForwardAgent yes
    TCPKeepAlive yes
    ConnectTimeout 5
    ServerAliveCountMax 10
    ServerAliveInterval 15
```
In the above config, `yourprivatekey` should be the name of the private key you created in step 1
and `yourusername` should be the username created for you to connect to `bastion-unpriv.cadence13.io`.

#### For Linux
If you are accessing Docker on Linux, you might be performing these commands using `sudo` or directly from root.
In that case, your `.ssh` directory would need to be in `/root`.


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

You can run docker-compose using an alternate docker-compose file. Make sure all of
your commands specify that config file, however, or else docker could get confused:
```
docker-compose -f docker-compose-localdb.yml up
docker-compose -f docker-compose-localdb.yml stop
```

### Accessing the Dashboard API

After spinning up the docker containers, the Dashboard API can be reached at http://localhost:8080.
The OpenAPI schema can be accessed at http://localhost:8080/ui/.