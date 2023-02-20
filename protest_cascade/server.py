import mesa

from .model import ProtestCascade
from .agent import Citizen
from mesa.visualization.UserParam import Slider, NumberInput, Checkbox
from mesa.visualization.modules import ChartModule, TextElement


AGENT_SUPPORT_COLOR = "#648FFF"
AGENT_OPPOSE_COLOR = "#FE6100"



# class QuiescentChart(TextElement):
#     """Display the current active population."""

#     def render(self, model):
#         return f"Quiescent Population: {model.quiescent_count}"


# quiescent_chart = QuiescentChart()

# chart = ChartModule(
#     [
#         {"Label": "Quiescent", "Color": "#648FFF"},
#         {"Label": "Active", "Color": "#FE6100"},
#         {"Label": "Jailed", "Color": "#808080"},
#     ],
#     data_collector_name="datacollector",
# )

# chart_spread_speed = ChartModule(
#     [
#         {"Label": "Speed of Rebellion Transmission", "Color": "#000000"},
#     ],
#     data_collector_name="datacollector",
# )


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


# default model params do not match netlogo defaults and model does not exhibit
# the same behavior as netlogo
# model_params = dict(
#     height=40,
#     width=40,
#     citizen_density=0.7,
#     cop_density=0.074,
#     citizen_vision=7,
#     cop_vision=7,
#     legitimacy=0.8,
#     max_jail_term=1000,
# )

# matching netlogo defaults
model_params = dict(
    height=40,
    width=40,
    citizen_density=Slider("Initial Agent Density", 0.1, 0.0, 0.9, 0.1),
    multiple_agents_per_cell=Checkbox("Multiple Agents Per Cell", value=False),
    citizen_vision=Slider("Citizen Vision", 7, 1, 10, 1),
    network=Checkbox("Network", value=False),
    network_discount=Slider("Network Discount Factor", 0.5, 0.0, 1.0, 0.1),
    seed=NumberInput("Random Seed", value=42),
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
