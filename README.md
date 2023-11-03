# buildall
Repository for building and running all of riesgos' services


## Preconditions

The script is intended to run on a linux system with the following tools installed:
- bash
- git
- docker
- curl
- tar
- sed

For docker it is best if docker version 2 is installed that includes `docker compose`
as a [subcommand](https://docs.docker.com/compose/compose-file/compose-file-v2/).
If you have docker in version 1, you need to install `docker-compose` too.

## How to get started

1. Adjust the `.env` file; replace the `<host-ip-address>` with your server's ip address.

2. You can build & run all needed docker images running:

```bash
# Make sure the build.sh can be executed
chmod +x build.sh
# Build all needed docker images
./build.sh all
# Start running all the services
./build.sh run
```

3. You can then open the browser on [http://localhost:8000](http://localhost:8000).

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




## Architecture overview

Shows 
- containers (boxes)
- which containers try to connect to other containers (arrows)
- which settings they use (content of boxes)
        - mostly refers to their .env variables
        - but for proxy lists the proxy-passes


```txt
frontend                                                  compare-frontend
┌────────────────┐                                   ┌────────────────────────────────┐
|frontendSubPath |                                   │         compareFrontendSubPath │
│                ├───────────────┐  ┌────────────────┤                                │
└────────────────┘               │  │                └────────────────────────────────┘
        |                        │  │                        |   
        |                        │  │                        |   
        |            backend     ▼  ▼                        |   
        |           ┌───────────────────────────────┐        |                   
        |           │     backendUrl                │        |                   
        |           │     backendPort               │        |                   
        |           │     maxStorageLifeTimeMinutes │        |               monitor   
        |           │     sendMailTo                │        |               ┌─────────────────────────┐ 
        |           │     sourceEmail               │◄───────|───────────────| testServiceEveryMinutes |
        |           │                               │        |               └─────────────────────────┘
        |           │                               │        |                   
        |           └─────────────┼─────────────────┘        |                   
        |                         │                          |   
        |                         │                          |   
        └───────────────────────┐ │ ┌────────────────────────┘   
                                │ │ |
                                │ │ |
                                ▼ │ ▼                                         Why use a proxy?
                   reverse-proxy  ▼                                           1. So that backend doesn't need to know all containers' addresses
                   ┌───────────────────────────────────┐                      2. So that backend may be deployed outside of docker
                   │   /reverse-proxy/default.conf     │                      3. So that containers can be moved outside of docker,
                   │       /geoserver ─────────────────┼────────────────┐        with proxy then pointing to new, outside server instead of towards
                   │       /wps ───────────────────────┼─────────────┐  │        container in local docker network.
                   │       /sysrelwps ─────────┐       │             │  │    4. The reverse proxy centralizes all CORS settings ... which can be complicated.                          
           ┌───────┼───────/tsunawps           │       │             │  │    5. It's also useful if you only have a limited amount of ports available (80, 443, ...)
           │  ┌────┼───────/tsunaoutputs       │       │             │  │                                                                    
           │  │    │┌──────/tsunageoserver     │       │             │  │                                                                    
           │  │    └┼──────────────────────────┼───────┘             │  │                                                                    
           │  │     │                          │                     │  │                                                                    
           │  │     │                          │                     │  │                                                                    
           │  │     │                          │                     │  │   ..... all containers up to here should be available from outside ......
           │  │     │                          │                     │  │
           ▼  ▼     │                          │                     ▼  ▼
   tsunawps         │        ades              │    riesgos-wps                      
   ┌──────────────┐ │        ┌──────────────┐ ◄┘    ┌────────────────────────────────────────────────────────────────┐
   └──────────────┘ │        └──────────────┘       │  riesgosWpsCatalinaOpts                                        │
                    │                               │  riesgosWpsMaxcacheSizeMb                                      │
                    │                               │  riesgosWpsGeoserverAccessBaseUrl                              │
                    │                               │  riesgosWpsGeoserverSendBaseUrl                                │
                    │                               │  riesgosWpsGeoserverUsername                                   │
                    │                               │  riesgosWpsGeoserverPassword                                   │
                    ▼                               │  riesgosWpsAccessServerHost  ───────┐                          │
   tsunageoserver                                   │  riesgosWpsAccessServerPort         │                          │
   ┌────────────────┐                               │  riesgosWpsAccessServerProtocol     │how to access riesgos-wps │
   └────────────────┘                               │  riesgosWpsAccessServerPath  ───────┘from outside of docker    │
                                                    │  riesgosWpsTomcatUsername                                      │
                                                    │  riesgosWpsTomcatPassword                                      │
                                                    │  riesgosWpsPassword                                            │
                                                    │  riesgosWpsSendBaseUrl                                         │
                                                    │                                                                │
                                                    └────────────────────────────────────────────────────────────────┘
                                                                ^
                                                                |
                                                     wps-init   |
                                                      ┌────────────────┐ 
                                                      └────────────────┘


```


## Idiosyncrasies

- Many containers have a `containerInit.sh` script, which is the `CMD` entrypoint to the container. 
        - This init script is there for updating the containers configuration based on the `environment`  values from the docker-compose file. 
        - This way, you can change a containers configuration without having to rebuild it.
- The architecture has all traffic between the user-facing containers (`frontend`, `compare-frontend` and `backend`) and the business-logic containers routed through a `reverse-proxy`.
        - So that backend doesn't need to know all containers' addresses
        - So that backend may be deployed outside of docker
        - So that containers can be moved outside of docker, with proxy then pointing to new, outside server instead of towards container in local docker network.




# Issues encountered
- frontend: cannot stat ../.env
