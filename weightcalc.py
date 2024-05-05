import datetime
import requests
from collections import namedtuple
import logging

logger = logging.getLogger("weightcalc")

def Worker(calculator, config:namedtuple):
    metrics = Metrics(
        url=config.PrometheusQueryEndpoint,
        servers=config.Servers
    )
    weights = calculator(metrics, config)
    WriteConfig(
        server_weights=weights,
        path=config.OutputFile
    )
    
class Metrics:
    def __init__(self, url, servers):
        self.url = url
        self.servers = servers
    
    # def Sample(self, server_name:str=None) -> dict:
    #     servers_metrics = dict()
    #     servers_list = self.servers if server_name is None else [server_name]
    #     for server in servers_list:
    #         metrics = dict()
    #         for metric in list(METRICS_QUERY_LIST.keys()):
    #             query = METRICS_QUERY_LIST[metric]
    #             params = {"query": query}
    #             response = requests.get(self.url, params).json()
    #             value = 0
    #             if not response["status"] == 'success':
    #                 value = 0
    #             else:
    #                 value = response['data']['result'][0]['value'][1]
    #             metrics[metric] = value
    #         servers_metrics[server] = metrics
    #     return servers_metrics
    def Sample(self, server_name:str=None) -> dict:
        # servers_metrics = dict()
        servers_list = self.servers if server_name is None else [server_name]
        # initialize server metrics
        servers_metrics = {server:dict() for server in servers_list}
        for metric in list(METRICS_QUERY_LIST.keys()):
            query = METRICS_QUERY_LIST[metric]
            params = {"query": query}
            logger.debug(f"Query params: {params}")
            response = requests.get(self.url, params).json()
            logger.debug(f"Query result: {response}")
            # Initialize sheet
            for server in servers_list:
                servers_metrics[server][metric] = 0
            if not response["status"] == 'success': # failed, return 0
                continue
            if response["data"]["resultType"] == "scalar": # One value for all       
                for server in servers_list:
                    value = float(response["data"]["result"][1])
                    servers_metrics[server][metric] = value
                continue
            for r in response["data"]["result"]: # Find and replace
                server = r["metric"]["instance"].replace("9126","8888")
                if server in servers_list:
                    value = float(r["value"][1])
                    servers_metrics[server][metric] = value
        logger.debug(f"Servers metrics: {servers_metrics}")
        return servers_metrics
    
    def CustomQuery(self, query):
        params = {"query": query}
        response = requests.get(self.url, params).json()
        value = 0
        if not response["status"] == 'success':
            value = 0
        else:
            value = response['data']['result'][0]['value'][1]
        return value

def WriteConfig(server_weights:dict, path:str) -> None:
    filecontent = GenerateNginxConf(server_weights)
    logger.debug(f"Config file content: \n{filecontent}\n")
    with open(path, "w") as f:
        f.write(filecontent)

def GenerateNginxConf(weights:dict):
    servers = "\n".join([f"server {server} weight={round(weights[server])};\t\t" for server in list(weights.keys())])
    conf = CONFIG_FILE.replace("${SERVERS}", servers)
    return conf

METRICS_QUERY_LIST = {
    "cpuTotal": "1",
    "cpuFree": "cpu_usage_idle{cpu='cpu-total'}",
    "memTotal": "1",
    "memFree": "mem_available_percent/100",
    "stoTotal": "1",
    "stoFree": "1",
    "netTotal": "1",
    "netFree": "1"
}

CONFIG_FILE = """
    upstream backend {
        # least_conn;
        ${SERVERS}
    }

    server {
        listen 80;
        location / {
            proxy_pass http://backend;
            # health_check;
            proxy_read_timeout 1800;
            proxy_connect_timeout 1800;
            proxy_send_timeout 1800;
            send_timeout 1800;
        }
    }
"""