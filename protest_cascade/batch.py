from model import EpsteinCivilViolence
from mesa.batchrunner import FixedBatchRunner
import json
import logging as log

import os

import numpy as np
import pandas as pd

from itertools import product

# set up logging to output to cwd /data
# log debug messages to file
# info message to console
cwd = os.getcwd()
path = os.path.join(cwd, "data/")
log.basicConfig(filename=f"{path}/log/batch.log", level=log.DEBUG)
log.info("Starting batch run")


# parameters that will remain constant
fixed_parameters = {
    "width": 40,
    "height": 40,
    "citizen_density": 0.7,
    "cop_density": 0.04,
    "citizen_vision": 7,
    "cop_vision": 7,
    "legitimacy": 0.82,
    'citizen_network_size':157,
    "max_jail_term": 30,
    "active_threshold": 0.1,
    "arrest_prob_constant": 2.3,
    'network_discount_factor':0.5,
    "movement": True,
    "max_iters": 500,
    # 'seed':None
}


# parameters you want to vary
# can also include combinations here
params = {
    "seed": [*range(100, 300 + 1, 1)]
}


def dict_product(dicts):  # could just use the below but it's cleaner this way
    """
    >>> list(dict_product(dict(number=[1,2], character='ab')))
    [{'character': 'a', 'number': 1},
     {'character': 'a', 'number': 2},
     {'character': 'b', 'number': 1},
     {'character': 'b', 'number': 2}]
    """
    return (dict(zip(dicts, x)) for x in product(*dicts.values()))


parameters_list = [*dict_product(params)]

# log the parameters
log.debug(parameters_list)

# what to run and what to collect
# iterations is how many runs per parameter value
# max_steps is how long to run the model
max_steps = 500
batch_run = FixedBatchRunner(
    EpsteinCivilViolence,
    parameters_list,
    fixed_parameters,
    model_reporters={
        "Quiescent": lambda m: m.count_quiescent(m),
        "Active": lambda m: m.count_active(m),
        "Jailed": lambda m: m.count_jailed(m),
        "Speed of Rebellion Transmission": lambda m: m.speed_of_rebellion_calculation(
            m
        ),
        "Seed": lambda m: m.report_seed(m),
    },
    agent_reporters={
        "pos": "pos",
        "breed": "breed",
        "hardship": "hardship" if "breed" == "citizen" else "breed",
        "risk aversion": "risk_aversion" if "breed" == "citizen" else "breed",
        "threshold": "threshold" if "breed" == "citizen" else "breed",
        "jail term": "jail_term" if "breed" == "citizen" else "breed",
        "condition": "condition" if "breed" == "citizen" else "breed",
        "greivance": "greivance" if "breed" == "citizen" else "breed",
        "arrest probability": "arrest_probability" if "breed" == "citizen" else "breed",
    },
    max_steps=max_steps,
)

# run the batches of your model with the specified variations
batch_run.run_all()


## NOTE: to do data collection, you need to be sure your pathway is correct to save this!
# Data collection
# extract data as a pandas Data Frame
batch_end_model = batch_run.get_model_vars_dataframe()
batch_end_agent = batch_run.get_agent_vars_dataframe()
batch_step_model_raw = batch_run.get_collector_model()
batch_step_agent_raw = batch_run.get_collector_agents()

# export the data to a csv file for graphing/analysis
cwd = os.getcwd()
path = os.path.join(cwd, "data/")
batch_end_model.to_csv(f"{path}\model_batch.csv")

print(batch_step_model_raw.keys())

for key, df in batch_step_model_raw.items():
    df.to_csv(f"{path}/seed_run/model_seed_{key[0]}.csv")

for key, df in batch_step_agent_raw.items():
    df.to_csv(f"{path}/seed_run/agent_seed_{key[0]}.csv")


# batch_save = {f'{key[0]}_{key[1]}':list(value['Cooperating_Agents']) for key,value in batch_dict.items()}
# json.dump(batch_save, open("C:\\Users\\grace\\Desktop\\macs_abm\\5_Sheduling\\PD_Grid\\pd_grid\\data\\batch_list.json", 'w'), indent = 4)
# batch_df_a.to_csv("../data/agent_batch.csv")
