import requests
import datetime

def GetMetrics(url) -> dict:
    print(url)
    pass

def WriteConfig(server_weights:dict, path:str) -> None:
    with open(path, "w") as f:
        f.write(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
        
def generate_nginx_conf(servers, weights):
#     conf = """
# http {
#     upstream backend {
#         # least_conn;
# """ 
#     for server, weight in zip(servers, weights):
#         conf += f"        server {server} weight={weight};\n"
        
#     conf += """
#     }

#     server {
        
#         location / {
#             proxy_pass http://appservers;
#             health_check;
#         }
#         location /api {
#             limit_except GET {
#                 auth_basic "NGINX Plus API";
#                 auth_basic_user_file /path/to/passwd/file;
#             }
#             api write=on;
#             allow 127.0.0.1;
#             deny  all;
#         }
#     }
# }
# """
    conf = """
    http {
        upstream backend {
            # least_conn;
    """ 
    for server, weight in zip(servers, weights):
        conf += f"        server {server} weight={weight};\n"
        
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

