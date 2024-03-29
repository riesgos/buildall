# General

- sudo docker compose down -v (also cleans volumes)
- Browser: new tab, clear cookies, clear memory (especially cache headers).
- Browser: In dev-tab, make sure that HTTP-cache is deactivated.

# Routing issues

- If you have a domain-name, you might have to register it with `reverse_proxy/default.conf` under `server_name`.
-

# Docker issues

- Some older versions of docker will not accept boolean values. We found that for the variable `RECREATE_DATADIR` the string value `"false"` - as opposed to the boolean `false` - did work.
- This setup has _not_ been tested with `podman`. Some containers require the ability to run docker within docker, and we don't know if podman does support this.
- Take care that you don't have multiple versions of docker and docker-compose installed.

# Env file issues:

- frontend: cannot stat ../.env
- Verify that there is a `.env` file at the root of this repository (that is, in the same directory as this `TROUBLESHOOTING.md` file) and that you have replaced all occurrences of `<your-ip-address>`.

# Upon executing service: Fetch failed / 404 / Connection refused

## Symptoms:

Executing a service via the frontend results in an error message:

```
Error: connect ECONNREFUSED 127.0.0.1:8080
TypeError: fetch failed
    at Object.fetch (node:internal/deps/undici/undici:11457:11)
    at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
    at async WpsClient.getRaw (/backend/dist/utils/wps/lib/wpsclient.js:192:31)
    at async WpsClient.getNextState (/backend/dist/utils/wps/lib/wpsclient.js:99:29)
    at async WpsClient.executeAsync (/backend/dist/utils/wps/lib/wpsclient.js:58:28)
    at async getAvailableEqs (/backend/dist/usr/wpsServices.js:84:21)
    at async Object.loadEqs [as function] (/backend/dist/usr/peru/1_eqs/eqs.js:16:20)
    at async Scenario.execute (/backend/dist/scenarios/scenarios.js:55:25)
    at async /backend/dist/scenarios/scenario.interface.js:55:44
```

Could also be `404 Connection refused`

## Reason:

Sometimes when starting `riesgos-wps` you'll get a log like this:
`riesgos-wps-1  | 2024-02-27 13:16:45,496 [main] INFO  org.n52.wps.server.database.FlatFileDatabase: Using "http://localhost:8080/wps/RetrieveResultServlet?id=" as base URL for results`
This might be because `wps-init` didn't correctly send the wps'es external url to `riesgos-wps`.

If after that you manually do a `docker compose down riesgos-wps && docker compose up -d`, you'll get:
`riesgos-wps-1  | 2024-02-27 13:16:45,496 [main] INFO  org.n52.wps.server.database.FlatFileDatabase: Using "http://10.104.136.68:80/wps/RetrieveResultServlet?id=" as base URL for results`

With that, the WPS should be properly configured.

# html could not be unmarshalled

## Symptoms:

```
Element [html] could not be unmarshalled as is not known in this context and the property does not allow DOM content.
```

- Backend: jsonix cannot unmarshal input data that it got
  - That's because the data is not xml, but html
  - That's likely because it didn't get a WPS'es response, but instead an error-message from nginx in html
- Nginx/RiesgosWPS: didn't respond with WPS-response, but with error message in html

- Backend gets this error message just before [html] error:

```
"type":"POST-response",
"url":"http://10.104.136.68:80/wps/WebProcessingService?service=WPS&request=Execute&version=1.0.0&identifier=org.n52.gfz.riesgos.algorithm.impl.AssetmasterProcess",
"result":"<!doctype html><html lang=\"en\"><head><title>HTTP Status 404 – Not Found</title><style type=\"text/css\">body {font-family:Tahoma,Arial,sans-serif;} h1, h2, h3, b {color:white;background-color:#525D76;} h1 {font-size:22px;} h2 {font-size:16px;} h3 {font-size:14px;} p {font-size:12px;} a {color:black;} .line {height:1px;background-color:#525D76;border:none;}</style></head><body><h1>HTTP Status 404 – Not Found</h1><hr class=\"line\" /><p><b>Type</b> Status Report</p><p><b>Description</b> The origin server did not find a current representation for the target resource or is not willing to disclose that one exists.</p><hr class=\"line\" /><h3>Apache Tomcat/9.0.65</h3></body></html>"
```

- Looking into the riesgos-wps-logs:

```
30-Jun-2023 09:17:32.501 INFO [Catalina-utility-1] se.jiderhamn.classloader.leak.prevention.JULLogger.info Releasing web app classloader from Apache Commons Logging
2023-06-30 09:17:32,514 [Catalina-utility-1] INFO  hsqldb.db.HSQLDB890B976FC7.ENGINE: Database closed
30-Jun-2023 09:17:32.625 INFO [Catalina-utility-1] org.apache.catalina.core.StandardContext.reload Reloading Context with name [/wps] is completed
30-Jun-2023 09:26:58.054 INFO [GuavaAuthCache-0-1] org.apache.catalina.loader.WebappClassLoaderBase.checkStateForResourceLoading Illegal access: this web application instance has been stopped already. Could not load [com.google.common.cache.RemovalCause]. The following stack trace is thrown for debugging purposes as well as to attempt to terminate the thread which caused the illegal access.
        java.lang.IllegalStateException: Illegal access: this web application instance has been stopped already. Could not load [com.google.common.cache.RemovalCause]. The following stack trace is thrown for debugging purposes as well as to attempt to terminate the thread which caused the illegal access.
                at org.apache.catalina.loader.WebappClassLoaderBase.checkStateForResourceLoading(WebappClassLoaderBase.java:1432)
                at org.apache.catalina.loader.WebappClassLoaderBase.checkStateForClassLoading(WebappClassLoaderBase.java:1420)
                at org.apache.catalina.loader.WebappClassLoaderBase.loadClass(WebappClassLoaderBase.java:1259)
                at org.apache.catalina.loader.WebappClassLoaderBase.loadClass(WebappClassLoaderBase.java:1220)
                at com.google.common.cache.LocalCache$Segment.expireEntries(LocalCache.java:2622)
                at com.google.common.cache.LocalCache$Segment.runLockedCleanup(LocalCache.java:3446)
                at com.google.common.cache.LocalCache$Segment.cleanUp(LocalCache.java:3438)
                at com.google.common.cache.LocalCache.cleanUp(LocalCache.java:3858)
                at com.google.common.cache.LocalCache$LocalManualCache.cleanUp(LocalCache.java:4797)
                at org.geoserver.security.auth.GuavaAuthenticationCacheImpl$1.run(GuavaAuthenticationCacheImpl.java:65)
                at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)
                at java.util.concurrent.FutureTask.runAndReset(FutureTask.java:308)
                at java.util.concurrent.ScheduledThreadPoolExecutor$ScheduledFutureTask.access$301(ScheduledThreadPoolExecutor.java:180)
                at java.util.concurrent.ScheduledThreadPoolExecutor$ScheduledFutureTask.run(ScheduledThreadPoolExecutor.java:294)
                at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
                at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
                at java.lang.Thread.run(Thread.java:750)
```

## Reason:

## Solution:

Restart buildall-riesgos-wps-1
Potentially also restart buildall-wps-init-1

# Port in use

## Symptoms

```bash
Error response from daemon: driver failed programming external connectivity on endpoint buildall-reverse_proxy-1 (c8c37c727da3eb11e756abc84d6004b18fdd6d017408b23add7ebdd4888007b1): Error starting userland proxy: listen tcp4 0.0.0.0:80: bind: address already in use
```

## Solution

This is self-explanatory: something on your machine is already blocking port 80. Do you have an apache or nginx running? Stop them.

# Syntax error / Error trying to load config.prod.json

## Symptoms

SyntaxError: JSON.parse: unexpected character at line 1 column 1 of the JSON data

## Diagnosis

Somewhere, a json file cannot be delivered. Instead what the request returns is a html-page which describes a 403 error. The actual error therefore is a 403 permission problem.

- Check where the error occurs:
  - in the `frontend` container? Then go into the container and fix the file's permissions
  - in the `reverse_proxy` container? Then change the configuration of the proxy to allow your file through
  - neither: is there a server somewhere between you and the reverse-proxy? Maybe your institution has its own proxy that your traffic needs to go through. This proxy could block certain file-request. Talk to you admin.

# Out of memory error

## Symptoms

One or more containers immediately stop with an OOM error:

```txt
library initialization failed - unable to allocate file descriptor table - out of memory
```

## Possible fix

Often times, this is due to the container trying to use more file-resources than your server allows it to.
We have encountered that error with the service `ades`.
If the number of files (`nofiles`) is indeed the source of the problem, then you can tell your server explicitly to allow more files for a docker container inside the `docker-compose.yml` file like so:

```yml
ades:
  image: 52north/ades:latest
  environment:
    SERVICE_SERVICE_URL: ${SysrelUrl}
    SERVICE_PROVIDER_INDIVIDUAL_NAME: Jane Doe
    SERVICE_PROVIDER_POSITION_NAME: First Line Supporter
    DOCKER_ENVPREFIX: TEST_
    TEST_MY_PROPERTY: custom-value
  # This service needs a lot of resources.
  # Your server might not per default allow such a high nofiles,
  # so we're setting it explicitly here.
  ulimits:
    nofile:
      soft: 65536
      hard: 65536
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
```
