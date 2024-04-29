import argparse
import time
from weightcalc import *
from logging import Logger
import logging
import yaml
import utilities

# logging.basicConfig(filename="newfile.log",
#                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                     filemode='w')
# logger = logging.getLogger('main')

argparser = argparse.ArgumentParser(description="Load balancer")

argparser.add_argument("-f", "--file", type=str, default="./config/dummy.yaml")

args = argparser.parse_args()
print(f"Using config file: {args.file}")
config_dict = utilities.ConfigParser(args.file)[0]
config = utilities.Dict2ObjParser(config_dict).parse()

# if args.verbose:
#     logger.setLevel(logging.DEBUG)

print(f"==== Load balancer: Weight Calculator ====")
print(f"k-cpu      : {config.Coeffs.cpu}")
print(f"k-mem      : {config.Coeffs.mem}")
print(f"k-sto      : {config.Coeffs.sto}")
print(f"k-net      : {config.Coeffs.net}")
print(f"intervals  : {config.CycleIntervals}")
print(f"algorithm  : {config.Algorithm}")
print(f"verbose    : {config.Verbose}")
print(f"prometheus : {config.PrometheusQueryEndpoint}")
print(f"output     : {config.OutputFile}")

match config.Algorithm:
    case "dynamicsmooth_weighted_roundrobin":
        from dynamicsmooth_weighted_roundrobin import DSWRR as Algo
    case "simple_sort":
        from simple_sort import SS as Algo
    case _:
        raise Exception("Not implemented!")

CALCULATOR = Algo(config)
try:
    while True:
        metrics = Metrics(
        url=config.PrometheusQueryEndpoint,
        servers=config.Servers
        )
        weights = CALCULATOR.Calc(metrics)
        WriteConfig(
            server_weights=weights,
            path=config.OutputFile
        )
        # Worker(A.Calc, config)
        time.sleep(config.CycleIntervals)
except KeyboardInterrupt:
    print("Keyboard interrupt received! Exit.")
