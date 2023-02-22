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
    "max_iters": 5,
    "multiple_agents_per_cell": False,
}

# parameters you want to vary
# can also include combinations here
params = {"seed": [*range(0, 9, 1)]}


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
    },
    agent_reporters={
        "pos": "pos",
        "condition": "condition",
        "opinion": "opinion",
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
    df.to_csv(f"{path}/model/model_seed_{key[0]}.csv")

for key, df in batch_step_agent_raw.items():
    df.to_csv(f"{path}/agent/agent_seed_{key[0]}.csv")
