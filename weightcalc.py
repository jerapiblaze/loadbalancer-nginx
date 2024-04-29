import datetime
import requests
from collections import namedtuple

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
    
    def Sample(self, server_name:str=None) -> dict:
        servers_metrics = dict()
        servers_list = self.servers if server_name is None else [server_name]
        for server in servers_list:
            metrics = dict()
            for metric in list(METRICS_QUERY_LIST.keys()):
                query = METRICS_QUERY_LIST[metric]
                params = {"query": query}
                response = requests.get(self.url, params).json()
                value = 0
                if not response["status"] == 'success':
                    value = 0
                else:
                    value = response['data']['result'][0]['value'][1]
                metrics[metric] = value
            servers_metrics[server] = metrics
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
    with open(path, "w") as f:
        f.write(filecontent)
    print(f"Config written at: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")

def GenerateNginxConf(weights:dict):
    conf = """
http {
    upstream backend {
        least_conn;
""" 
    for server in list(weights.keys()):
        conf += f"        server {server} weight={weights[server]};\n"
        
    conf += """
    }

    server {
        
        location / {
            proxy_pass http://appservers;
            health_check;
        }
        location /api {
            limit_except GET {
                auth_basic "NGINX Plus API";
                auth_basic_user_file /path/to/passwd/file;
            }
            api write=on;
            allow 127.0.0.1;
            deny  all;
        }
    }
}
"""
    return conf

METRICS_QUERY_LIST = {
    "cpuTotal": "",
    "cpuFree": "",
    "memTotal": "node_memory_MemTotal_bytes",
    "memFree": "node_memory_MemAvailable_bytes",
    "stoTotal": "",
    "stoFree": "",
    "netTotal": "",
    "netFree": ""
}