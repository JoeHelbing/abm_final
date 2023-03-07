import mesa

from .model import ProtestCascade
from .agent import Citizen, Security
from mesa.visualization.UserParam import Slider, NumberInput, Checkbox
from mesa.visualization.modules import ChartModule, TextElement


AGENT_SUPPORT_COLOR = "#648FFF"
AGENT_OPPOSE_COLOR = "#FE6100"


class CitizenChart(TextElement):
    """Display the current citizen population."""

    def render(self, model):
        return f"Total Citizen Population: {model.citizen_count}"


class ProtestChart(TextElement):
    """Display the current protesting population."""

    def render(self, model):
        return f"Protesting Population: {model.protest_count}"


class SupportChart(TextElement):
    """Display the current publicly (regime) supporting population."""

    def render(self, model):
        return f"Supporting Population: {model.support_count}"


class JailChart(TextElement):
    """Display the current publicly (regime) supporting population."""

    def render(self, model):
        return f"Supporting Population: {model.jail_count}"


citizen_chart = CitizenChart()
protest_chart = ProtestChart()
support_chart = SupportChart()
jail_chat = JailChart()

count_chart = ChartModule(
    [
        {"Label": "Support Count", "Color": "#648FFF"},
        {"Label": "Protest Count", "Color": "#FE6100"},
        {"Label": "Jail Count", "Color": "#000000"},
    ],
    data_collector_name="datacollector",
)

chart_spread_speed = ChartModule(
    [
        {"Label": "Speed of Spread", "Color": "#000000"},
    ],
    data_collector_name="datacollector",
)


def portrayal(agent):
    if agent is None:
        return

    if type(agent) is Security and agent.defected:
        return

    if type(agent) is Citizen and agent.condition == "Jail":
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
        radius = 0.5 if agent.condition == "Support" else 0.7
        portrayal["Color"] = color
        portrayal["r"] = radius
        portrayal["Filled"] = "false"
        portrayal["Layer"] = 0

    if type(agent) is Security:
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8
        portrayal["Color"] = "#000000"
        portrayal["Layer"] = 1
    return portrayal


model_params = dict(
    height=40,
    width=40,
    citizen_density=Slider("Initial Agent Density", 0.7, 0.0, 0.9, 0.1),
    # citizen_vision=Slider("Citizen Vision", 7, 1, 10, 1),
    # security_vision=Slider("Security Vision", 7, 1, 10, 1),
    security_density=Slider("Security Density", 0.00, 0.0, 0.09, 0.01),
    # max_jail_term=Slider("Maximum Jail Term", 30, 1, 50, 5),
    private_preference_distribution_mean=Slider(
        "Mean of Regime Preference", 0, -1, 1, 0.1
    ),
    # standard_deviation=Slider("Standard Deviation of Regime Preference", 1, 0, 2, 0.1),
    epsilon=Slider("Epsilon", 1, 0, 1.5, 0.1),
    # network=Checkbox("Network", value=False),
    random_seed=Checkbox("Flip to Using Random Seeds", value=False),
    multiple_agents_per_cell=Checkbox("Multiple Agents Per Cell", value=False),
    seed=NumberInput("User Chosen Fixed Seed", value=42),
)
canvas_element = mesa.visualization.CanvasGrid(portrayal, 40, 40, 480, 480)
server = mesa.visualization.ModularServer(
    ProtestCascade,
    [
        canvas_element,
        citizen_chart,
        protest_chart,
        support_chart,
        count_chart,
        chart_spread_speed,
    ],
    "Protest Cascade",
    model_params,
)