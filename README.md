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

## Maintainance
We've found that some services require some degree of maintainance, depending on how they are deployed. This section collects maintainance tasks that you *might* want to include in your production-environment.

### Riesgos-WPS
Running the WPS now for a longer time, we occasionally ran into hard disk limitations due to all the files that the WPS created. This will depend on how much disk-space you make available to it and how often you re-create the container, of course.

You might want to add cronjobs to do some cleanup-work. The following jobs worked for us in production:
```bash
rm -rf /usr/local/tomcat/webapps/geoserver/data/workspaces/riesgos/*.zip /usr/local/tomcat/webapps/geoserver/data/workspaces/riesgos/*.tif /usr/local/tomcat/webapps/geoserver/data/data/riesgos/*.zip /usr/local/tomcat/webapps/geoserver/data/data/riesgos/*.tif
```
(removes the tiffs & zip files from the geoserver).

```bash
find /usr/local/tomcat/temp -type f -mtime +3 -execdir rm -- {} \;
```
(removes temp files from the tomcat).


## See also

- https://docs.docker.com/compose/compose-file/compose-file-v2/
