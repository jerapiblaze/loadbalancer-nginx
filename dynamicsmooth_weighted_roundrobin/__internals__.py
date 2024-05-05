from collections import namedtuple

class DSWRR:
    def __init__(self, config):
        self.config = config
    def Calc(self, metrics:object) -> dict:
        config = self.config
        server_metrics = metrics.Sample()

        # STEP 1
        I_performance_value = dict()
        for metric in ["cpu","mem","sto","net"]:
            maxMetric = max([float(k[f"{metric}Total"]) for k in list(server_metrics.values())])
            performance_values = dict()
            for server_name in list(server_metrics.keys()):
                capacity = server_metrics[server_name][f"{metric}Total"]
                if maxMetric == 0:
                    performance_value = 0
                else:
                    performance_value = float(capacity)/maxMetric
                performance_values[server_name] = performance_value
            I_performance_value[metric] = performance_values    

        SW_static_weight = dict()
        for server_name in list(server_metrics.keys()):
            static_weight = \
                I_performance_value["cpu"][server_name] * config.Coeffs.cpu + \
                I_performance_value["mem"][server_name] * config.Coeffs.mem + \
                I_performance_value["sto"][server_name] * config.Coeffs.sto + \
                I_performance_value["net"][server_name] * config.Coeffs.net
            SW_static_weight[server_name] = static_weight

        # STEP 2
        L_idle_rate = dict()
        for server_name in list(server_metrics.keys()):
            metrics = server_metrics[server_name]
            K_idle_ratios = dict()
            for metric in ["cpu","mem","sto","net"]:
                for i in ["cpu", "mem", "sto", "net"]:
                    iTotal, iFree = metrics[f"{i}Total"], metrics[f"{i}Free"]
                    if iTotal == 0:
                        K_idle_ratios[i] = 0
                    else:
                        K_idle_ratios[i] = float(iFree)/float(iTotal)
            l_idle_rate = \
                K_idle_ratios["cpu"] * config.Coeffs.cpu + \
                K_idle_ratios["mem"] * config.Coeffs.mem + \
                K_idle_ratios["sto"] * config.Coeffs.sto + \
                K_idle_ratios["net"] * config.Coeffs.net
            L_idle_rate[server_name] = l_idle_rate

        DW_dynamic_weight = dict()
        for server_name in config.Servers:
            i = config.Servers.index(server_name)
            # STEP 3
            TW_dynamic_weight = config.C * config.LimitCoeffs[i] * L_idle_rate[server_name] * SW_static_weight[server_name]
            minWeight = config.MinWeights[i]
            maxWeight = config.MaxWeights[i]
            dw = TW_dynamic_weight
            # STEP 4
            # STATIC AND PRE-CALCULATED
            # STEP 5
            if dw < minWeight:
                dw = minWeight
            if dw > maxWeight:
                dw = maxWeight
            DW_dynamic_weight[server_name] = dw
        return DW_dynamic_weight