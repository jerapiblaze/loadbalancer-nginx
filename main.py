import argparse
import time
from weightcalc import *
from logging import Logger
import logging
import yaml
import utilities
import os
import sys

logging.basicConfig(
    stream=sys.stdout, level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s | %(message)s'
)
logger = logging.getLogger('main')

argparser = argparse.ArgumentParser(description="Load balancer")

DEFAULT_CONFIG_FILE="./config/dummy.yaml"
argparser.add_argument("-f", "--file", type=str, default=DEFAULT_CONFIG_FILE)

args = argparser.parse_args()
config_file=args.file
try:
    config_dict = utilities.ConfigParser(config_file)[0]
    config = utilities.Dict2ObjParser(config_dict).parse()
except Exception:
    config_file = DEFAULT_CONFIG_FILE
    config_dict = utilities.ConfigParser(config_file)[0]
    config = utilities.Dict2ObjParser(config_dict).parse()
logger.info(f"Using config file: {config_file}")
# if args.verbose:
#     logger.setLevel(logging.DEBUG)

logger.info(f"==== Load balancer: Weight Calculator ====")
logger.info(f"k-cpu      : {config.Coeffs.cpu}")
logger.info(f"k-mem      : {config.Coeffs.mem}")
logger.info(f"k-sto      : {config.Coeffs.sto}")
logger.info(f"k-net      : {config.Coeffs.net}")
logger.info(f"intervals  : {config.CycleIntervals}")
logger.info(f"algorithm  : {config.Algorithm}")
logger.info(f"verbose    : {config.Verbose}")
logger.info(f"prometheus : {config.PrometheusQueryEndpoint}")
logger.info(f"output     : {config.OutputFile}")

match config.Algorithm:
    case "dynamicsmooth_weighted_roundrobin":
        from dynamicsmooth_weighted_roundrobin import DSWRR as Algo
    case "simple_sort":
        from simple_sort import SS as Algo
    case _:
        raise Exception("Not implemented!")

CALCULATOR = Algo(config)
prev_weight = None
try:
    while True:
        logger.info("Starting new config round.")
        metrics = Metrics(
            url=config.PrometheusQueryEndpoint,
            servers=config.Servers
        )
        weights = CALCULATOR.Calc(metrics)
        if prev_weight == weights:
            logger.info("No changes in weights.")
            time.sleep(config.CycleIntervals)
            continue
        WriteConfig(
            server_weights=weights,
            path=config.OutputFile
        )
        logger.info(f"Config written at: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
        if config.Verbose:
            logger.info(weights)
        cmd = "nginx -s reload"
        logger.info(f"Reloading NGINX config with command: {cmd}")
        prev_weight = weights
        os.system(cmd)
        time.sleep(config.CycleIntervals)
except KeyboardInterrupt:
    logger.info("Keyboard interrupt received! Exit.")
    
exit()
