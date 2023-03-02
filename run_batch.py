from protest_cascade.model import ProtestCascade
from mesa.batchrunner import FixedBatchRunner
import logging as log
import os
import pandas as pd
from itertools import product

# set up logging to output to cwd /data
# log debug messages to file
# info message to console
cwd = os.getcwd()
path = os.path.join(cwd, "./data/")
log.basicConfig(filename=f"{path}/log/batch.log", level=log.DEBUG)
log.info("Starting batch run")

# parameters that will remain constant
fixed_parameters = {
    "width": 40,
    "height": 40,
    "citizen_density": 0.7,
    "citizen_vision": 7,
    "movement": True,
    "multiple_agents_per_cell": False,
}

# parameter sweep
params = {
    "seed": [*range(0, 9, 1)],
    "private_preference_distribution_mean": [
        -1,
        -0.5,
        0,
        0.5,
        1,
    ],
    "epsilon": [0, 0.2, 0.4, 0.6, 0.8, 1],
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
max_steps = 100
batch_run = FixedBatchRunner(
    ProtestCascade,
    parameters_list,
    fixed_parameters,
    model_reporters={
        "Seed": lambda m: m.report_seed(m),
        "Citizen Count": lambda m: m.count_citizen(m),
        "Protest Count": lambda m: m.count_protest(m),
        "Support Count": lambda m: m.count_support(m),
        "Speed of Spread": lambda m: m.speed_of_spread(m),
    },
    agent_reporters={
        "pos": "pos",
        "condition": "condition",
        "opinion": "opinion",
        "activation": "activation",
        "private_preference": "private_preference",
        "epsilon": "epsilon",
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
batch_end_model.to_csv(f"{path}/model_batch.csv")

if not os.path.exists(f"{path}/model"):
    os.makedirs(f"{path}/model")
for key, df in batch_step_model_raw.items():
    df.to_csv(f"{path}/model/model_seed_{key[0]}_pp_{key[1]}_ep_{key[2]}.csv")

if not os.path.exists(f"{path}/agent"):
    os.makedirs(f"{path}/agent")
for key, df in batch_step_agent_raw.items():
    df.to_csv(f"{path}/agent/agent_seed_{key[0]}_pp_{key[1]}_ep_{key[2]}.csv")
