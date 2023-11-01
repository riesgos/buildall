# General

- sudo docker compose down -v (also cleans volumes)
- Browser: new tab, clear cookies, clear memory (especially cache headers).
- Browser: In dev-tab, make sure that HTTP-cache is deactivated.


# Routing issues
- If you have a domain-name, you might have to register it with  `reverse_proxy/default.conf` under `server_name`.
- 

# Docker issues
- Some older versions of docker will not accept boolean values. We found that for the variable `RECREATE_DATADIR` the string value `"false"` - as opposed to the boolean `false` - did work.


# Fetch failed


## Symptoms:
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
Commonly occurs after containers have been (re-)started and riesgos-wps-init is not yet completed.

## Solution:
Wait a few seconds and try again.
Potentially restart backend, riesgos-wps, and wps-init.



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


# 
