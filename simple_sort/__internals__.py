from collections import namedtuple

class SS:
    def __init__(self, config):
        self.config = config
    def Calc(self, metrics:object) -> dict:
        config = self.config
        # print(server_metrics)
        server_metrics = metrics.Sample()
        weights = dict()
        for server_name in list(server_metrics.keys()):
            metrics = server_metrics[server_name]
            usedRatios = dict()
            for i in ["cpu", "mem", "sto", "net"]:
                iTotal, iFree = metrics[f"{i}Total"], metrics[f"{i}Free"]
                if iTotal == 0:
                    usedRatios[i] = 0
                else:
                    usedRatios[i] = 1 - float(iFree)/float(iTotal)
            weight = \
                usedRatios["cpu"] * config.Coeffs.cpu + \
                usedRatios["mem"] * config.Coeffs.mem + \
                usedRatios["sto"] * config.Coeffs.sto + \
                usedRatios["net"] * config.Coeffs.net
            weights[server_name] = weight
        # print(weights)
        return weights