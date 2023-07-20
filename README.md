# buildall
Repository for building and running all of riesgos' services


## Preconditions

The script is intended to run on a linux system with the following tools installed:
- bash
- git
- docker

For docker it is best if docker version 2 is installed that includes `docker compose`
as a [subcommand](https://docs.docker.com/compose/compose-file/compose-file-v2/).
If you have docker in version 1, you need to install `docker-compose` too.

## How to get started

You can build & run all needed docker images running:

```bash
# Make sure the build.sh can be executed
chmod +x build.sh
# Build all needed docker images
./build.sh all
# Start running all the services
./build.sh run
```

You can then open the browser on [http://localhost:8000](http://localhost:8000).

## Troubleshooting

See [here](./TROUBLESHOOTING.md).

## See also

- https://docs.docker.com/compose/compose-file/compose-file-v2/
