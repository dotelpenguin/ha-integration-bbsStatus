This is a home assistant intigration to monitor a WWIV BBS with a health status endpoint


We will define the IP/DNS and Port (default 8080), and refresh interval (deault 60s) within the home assistant config


Here is an example of the output

Url will be http://{IP/DNS}:{port}/status



curl http://10.0.2.134:8080/status
{
    "status": {
        "num_instances": 11,
        "used_instances": 0,
        "lines": [
            "BINKP Waiting for Call",
            "StarDoc 134 Node #2 Waiting For Call",
            "StarDoc 134 Node #3 Waiting for Call",
            "StarDoc 134 Node #4 Waiting for Call",
            "StarDoc 134 Node #5 Waiting for Call",
            "StarDoc 134 Node #6 Waiting for Call",
            "StarDoc 134 Node #7 Waiting for Call",
            "StarDoc 134 Node #8 Waiting for Call",
            "StarDoc 134 Node #9 Waiting for Call",
            "StarDoc 134 Node #10 Waiting for Call",
            "StarDoc 134 Node #11 Waiting for Call"
        ]
    }


We want to import this JSON treeWe will need:

