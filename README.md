# Protest Cascade Model

## Summary
This is a modular agent-based model of protest cascades based on the work of Kuran (1991) and Epstein (2002). The model is built using the Mesa framework for agent-based modeling in Python. The model is designed to be modular and extensible, allowing for the addition of new agents, behaviors, and schedules. 

## How to create a virtual environment using Ananconda and install dependencies
[Anaconda](https://www.anaconda.com/) is a free and open-source distribution of the Python and R programming languages for scientific computing, that aims to simplify package management and deployment. The following steps will create a virtual environment using Anaconda and install the dependencies.

replace `abm_protest_cascade` with the name of your choice
```
    $ conda create -n abm_protest_cascade --file requirements.txt
    $ conda activate abm_protest_cascade
```

## How to Run

To use the model interactively, from the model directory run:

```
    $ python run.py
```

The command line will print a URL

Then open your browser to [http://127.0.0.1:8521/](http://127.0.0.1:8521/) and press Reset, then Run.

## Files in protest_cascade/

* ``model.py``: Core model and agent code.
* ``server.py``: Sets up the interactive visualization.
* ``agent.py``: Defines the base agent RandomWalker and the inheriting agents Citizen and Security.
* ``schedule.py``: Defines the base schedule SimultaneousActivationByType and the inheriting schedule with added functions.

## Further Reading

This model uses inspiration from:

[Kuran, Timur. "Now Out of Never: The Element of Surprise in the East European Revolutions of 1989." World Politics, Vol. 44 No. 1, Oct. 1991: 7-48.](https://pdodds.w3.uvm.edu/files/papers/others/1991/kuran1991.pdf)

[Epstein, J. “Modeling civil violence: An agent-based computational approach”, Proceedings of the National Academy of Sciences, Vol. 99, Suppl. 3, May 14, 2002](http://www.pnas.org/content/99/suppl.3/7243.short)

[Wolf Sheep Predation model](https://github.com/projectmesa/mesa-examples/tree/main/examples/wolf_sheep)
