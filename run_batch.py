import logging as log
import os

# set up logging to output to cwd /data
# log debug messages to file
# info message to console
cwd = os.getcwd()
log_path = os.path.join(cwd, "./log/")
if not os.path.exists(log_path):
    os.makedirs(log_path)

data_path = os.path.join(cwd, "./data/")
if not os.path.exists(data_path):
    os.makedirs(data_path)

from protest_cascade.model import ProtestCascade
from mesa.batchrunner import FixedBatchRunner
import pandas as pd
from itertools import product
from protest_cascade.agent import Citizen, Security

log.basicConfig(filename=f"{cwd}/log/batch.log", level=log.DEBUG)
log.info("Starting batch run")

# parameters that will remain constant
fixed_parameters = {
    "multiple_agents_per_cell": True,
}

# parameter sweep
# params = [
#     {
#         "seed": [287],
#         "private_preference_distribution_mean": [-1, -0.6, -0.2, 0, 0.2, 0.6, 1],
#         "security_density": [0.0, 0.02, 0.04, 0.06, 0.08],
#         "epsilon": [0, 0.2, 0.4, 0.6, 0.8, 1, 3],
#     },
#     {
#         "seed": [298],
#         "private_preference_distribution_mean": [-1, -0.6, -0.2, 0, 0.2, 0.6, 1],
#         "security_density": [0.0, 0.02, 0.04, 0.06, 0.08],
#         "epsilon": [0, 0.2, 0.4, 0.6, 0.8, 1, 3],
#     },
# ]

#If you need to test a single parameter set, uncomment this and comment out the above:
params = [
    {
        "seed": [21048712],
        "private_preference_distribution_mean": [-1],
        "security_density": [0.0],
        "epsilon": [0],
    }
]

def dict_product(dicts):  # could just use the below but it's cleaner this way
    """
    >>> list(dict_product(dict(number=[1,2], character='ab')))
    [{'character': 'a', 'number': 1},
     {'character': 'a', 'number': 2},
     {'character': 'b', 'number': 1},
     {'character': 'b', 'number': 2}]
    """
    return (dict(zip(dicts, x)) for x in product(*dicts.values()))


# set up the reporters
model_reporters = {
    "Seed": lambda m: m.report_seed(m),
    "Citizen Count": lambda m: m.count_citizen(m),
    "Protest Count": lambda m: m.count_protest(m),
    "Support Count": lambda m: m.count_support(m),
    "Speed of Spread": lambda m: m.speed_of_spread(m),
    "Security Density": lambda m: m.report_security_density(m),
    "Private Preference": lambda m: m.report_private_preference(m),
    "Epsilon": lambda m: m.report_epsilon(m),
    "Threshold": lambda m: m.report_threshold(m),
}

agent_reporters = {
    "pos": "pos",
    "condition": "condition",
    "opinion": "opinion",
    "activation": "activation",
    "private_preference": "private_preference",
    "epsilon": "epsilon",
    "threshold": "threshold",
    "jail_sentence": "jail_sentence",
    "flip": "flip",
    "ever_flipped": "ever_flipped",
    "model_security_density": "dc_security_density",
    "model_private_preference": "dc_private_preference",
    "model_epsilon": "dc_epsilon",
    "model_threshold": "dc_threshold",
    "model_seed": "dc_seed",
}

for i, p in enumerate(params):
    parameters_list = [*dict_product(p)]
    # what to run and what to collect
    # iterations is how many runs per parameter value
    # max_steps is how long to run the model
    max_steps = 200
    batch_run = FixedBatchRunner(
        ProtestCascade,
        parameters_list,
        fixed_parameters,
        model_reporters=model_reporters,
        agent_reporters=agent_reporters,
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
    batch_end_model.to_csv(f"{path}/model_batch_{i}.csv")

    if not os.path.exists(
        f"{path}/model/seed_{list(batch_step_model_raw.keys())[0][0]}"
    ):
        os.makedirs(f"{path}/model/seed_{list(batch_step_model_raw.keys())[0][0]}")
    for key, df in batch_step_model_raw.items():
        df.to_csv(
            f"{path}/model/seed_{key[0]}/model_seed_{key[0]}_pp_{key[1]}_sd{key[2]}_ep_{key[3]}.csv"
        )

    if not os.path.exists(
        f"{path}/agent/seed_{list(batch_step_agent_raw.keys())[0][0]}"
    ):
        os.makedirs(f"{path}/agent/seed_{list(batch_step_agent_raw.keys())[0][0]}")
    for key, df in batch_step_agent_raw.items():
        df.to_csv(
            f"{path}/agent/seed_{key[0]}/agent_seed_{key[0]}_pp_{key[1]}_sd{key[2]}_ep_{key[3]}.csv"
        )
