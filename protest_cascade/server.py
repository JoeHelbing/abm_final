import mesa

from .model import ProtestCascade
from .agent import Citizen
from mesa.visualization.UserParam import Slider, NumberInput, Checkbox
from mesa.visualization.modules import ChartModule, TextElement


AGENT_SUPPORT_COLOR = "#648FFF"
AGENT_OPPOSE_COLOR = "#FE6100"


def portrayal(agent):
    if agent is None:
        return

    portrayal = {
        "Shape": "circle",
        "x": agent.pos[0],
        "y": agent.pos[1],
        "Filled": "true",
    }

    if type(agent) is Citizen:
        color = (
            AGENT_SUPPORT_COLOR if agent.condition == "Support" else AGENT_OPPOSE_COLOR
        )
        portrayal["Color"] = color
        portrayal["r"] = 0.5
        portrayal["Filled"] = "false"
        portrayal["Layer"] = 0

    return portrayal


model_params = dict(
    height=40,
    width=40,
    citizen_density=Slider("Initial Agent Density", 0.7, 0.0, 0.9, 0.1),
    multiple_agents_per_cell=Checkbox("Multiple Agents Per Cell", value=False),
    citizen_vision=Slider("Citizen Vision", 7, 1, 10, 1),
    network=Checkbox("Network", value=False),
    seed=NumberInput("Fixed Seed", value=42),
    random_seed=Checkbox("Random Seed", value=False),
)
canvas_element = mesa.visualization.CanvasGrid(portrayal, 40, 40, 480, 480)
server = mesa.visualization.ModularServer(
    ProtestCascade,
    [
        canvas_element,
    ],
    "Protest Cascade",
    model_params,
)
