import mesa
import math

from protest_cascade.scheduler import RandomActivationByTypeFiltered
from .agent import Citizen


class ProtestCascade(mesa.Model):
    """
    Placeholder
    """

    def __init__(
        self,
        width=40,
        height=40,
        citizen_vision=7,
        citizen_density=0.7,
        movement=True,
        multiple_agents_per_cell=False,
        max_iters=100,
        seed=None,
    ):
        super().__init__()
        self.reset_randomizer(seed)
        print(f"Running ProtestCascade with seed {self._seed}")
        self.width = width
        self.height = height
        self.citizen_density = citizen_density
        self.citizen_vision = citizen_vision
        self.movement = movement
        self.max_iters = max_iters
        self.multiple_agents_per_cell = multiple_agents_per_cell
        self.iteration = 0
        self.schedule = RandomActivationByTypeFiltered(self)
        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=True)

        # agent counts
        self.citizen_count = round(self.width * self.height * self.citizen_density)
        self.support = 0
        self.oppose = 0
        self.active_count = 0

        self.running = True

        # Create agents
        for i in range(self.citizen_count):
            pos = None
            if not self.multiple_agents_per_cell and self.grid.empties > 0:
                pos = self.random.choice(self.grid.empties)
            else:
                x = self.random.randrange(self.width)
                y = self.random.randrange(self.height)
                pos = (x, y)
            citizen = Citizen(self.next_id(), pos, self, True)
            self.grid.place_agent(citizen, (x, y))
            self.schedule.add(citizen)


        self.citizen_count = self.count_citizens(self)
        self.active_count = self.count_active(self)
        self.quiescent_count = self.count_quiescent(self)

        model_reporters = {
            "Quiescent": self.count_quiescent,
            "Active": self.count_active,
            "Jailed": self.count_jailed,
            "Speed of Rebellion Transmission": self.speed_of_rebellion_calculation,
            "Seed": self.report_seed,
        }
        agent_reporters = {
            "pos": lambda a: getattr(a, "pos", None),
            "breed": lambda a: getattr(a, "breed", None),
            "hardship": lambda a: getattr(a, "hardship", None),
            "risk aversion": lambda a: getattr(a, "risk_aversion", None),
            "threshold": lambda a: getattr(a, "threshold", None),
            "jail sentence": lambda a: getattr(a, "jail_sentence", None),
            "condition": lambda a: getattr(a, "condition", None),
            "grievance": lambda a: getattr(a, "grievance", None),
            "arrest probability": lambda a: getattr(a, "arrest_probability", None),
        }
        self.datacollector = mesa.DataCollector(
            model_reporters=model_reporters, agent_reporters=agent_reporters
        )

        self.datacollector.collect(self)

        # intializing the agent network
        for agent in self.schedule.agents:
            # create a list of tuples of (agent, distance to agent) distances
            # from this agent to all other agents
            if agent.breed == "citizen":
                distances = []
                for other_agent in self.schedule.agents:
                    if agent is not other_agent:
                        distances.append(
                            (other_agent, self.distance_calculation(agent, other_agent))
                        )
                # assign max distance
                max_distance = max(distances, key=lambda x: x[1])[1]
                # normalise all distances to be between 0 and 1 and replace
                # the distance with the normalised distance
                distances = [
                    (agent, distance / max_distance) for agent, distance in distances
                ]
                # assign network as a list to agent.network as a random
                # distribution of up to citizen_network_size agents preferring but not
                # limited to agents that are closer
                agent.network = self.random.choices(
                    [agent for agent, distance in distances],
                    weights=[distance for agent, distance in distances],
                    k=self.citizen_network_size,
                )

    def step(self):
        """
        Advance the model by one step and collect data.
        """
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)
        # update agent counts
        self.active_count = self.count_active(self)
        self.quiescent_count = self.count_quiescent(self)
        self.jail_count = self.count_jailed(self)

        # update iteration
        self.iteration += 1
        if self.iteration > self.max_iters:
            self.running = False

    @staticmethod
    def count_quiescent(model):
        """
        Helper method to count quiescent agents.
        """
        return len(
            [
                agent
                for agent in model.schedule.agents
                if agent.breed == "citizen" and agent.condition == "Quiescent"
            ]
        )

    @staticmethod
    def count_active(model):
        """
        Helper method to count active agents.
        """
        return len(
            [
                agent
                for agent in model.schedule.agents
                if agent.breed == "citizen" and agent.condition == "Active"
            ]
        )

    @staticmethod
    def count_jailed(model):
        """
        Helper method to count jailed agents.
        """
        return len(
            [
                agent
                for agent in model.schedule.agents
                if agent.breed == "citizen" and agent.jail_sentence > 0
            ]
        )

    @staticmethod
    def count_citizens(model):
        """
        Helper method to count citizens.
        """
        return len(
            [agent for agent in model.schedule.agents if agent.breed == "citizen"]
        )

    @staticmethod
    def count_cops(model):
        """
        Helper method to count cops.
        """
        return len([agent for agent in model.schedule.agents if agent.breed == "cop"])

    # combine all agent counts into one method
    @staticmethod
    def count_agents(model):
        """
        combines the various count methods into one
        """
        return (
            model.count_quiescent(model)
            + model.count_active(model)
            + model.count_jailed(model)
        )

    @staticmethod
    def speed_of_rebellion_calculation(model):
        """
        Calculates the speed of transmission of the rebellion.
        """
        if model.citizen_count == 0:
            return 0
        count = 0
        for agent in model.schedule.agents:
            if agent.breed == "citizen" and agent.flipped == True:
                count += 1
        return count / model.citizen_count

    @staticmethod
    def report_seed(model):
        """
        Helper method to report the seed.
        """
        return model._seed

    def distance_calculation(self, agent1, agent2):
        """
        Helper method to calculate distance between two agents.
        """
        return math.sqrt(
            (agent1.pos[0] - agent2.pos[0]) ** 2 + (agent1.pos[1] - agent2.pos[1]) ** 2
        )
