import mesa
import math
import logging as log

from protest_cascade.scheduler import RandomActivationByTypeFiltered
from .agent import Citizen

# setup logging for the model
log.basicConfig(
    filename="protest_cascade.log",
    filemode="w",
    format="%(message)s",
    level=log.DEBUG,
)


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
        network=False,
        network_discount=0.5,
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
        self.network = network
        self.network_discount = network_discount
        self.citizen_count = round(self.width * self.height * self.citizen_density)
        self.network_size = round(
            (((self.citizen_vision * 2 + 1) ** 2) - 1) * self.citizen_density
        )
        self.iteration = 0
        self.schedule = RandomActivationByTypeFiltered(self)
        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=True)

        # agent counts
        self.support = 0
        self.oppose = 0
        self.active_count = 0

        # Create agents
        for i in range(self.citizen_count):
            pos = None
            if not self.multiple_agents_per_cell and len(self.grid.empties) > 0:
                pos = self.random.choice(list(self.grid.empties))
            else:
                x = self.random.randrange(self.width)
                y = self.random.randrange(self.height)
                pos = (x, y)
            citizen = Citizen(self.next_id(), self, pos, self.citizen_vision)
            self.grid.place_agent(citizen, pos)
            self.schedule.add(citizen)

        # set up the data collector
        model_reporters = {
            "Seed": self.report_seed,
        }
        agent_reporters = {
            "pos": lambda a: getattr(a, "pos", None),
            "condition": lambda a: getattr(a, "condition", None),
        }
        self.datacollector = mesa.DataCollector(
            model_reporters=model_reporters, agent_reporters=agent_reporters
        )

        # log.DEBUG(self.schedule.agents_by_type[Citizen].values())

        # intializing the agent network
        if self.network:
            self.network_initialization()

        # The final step is to set the model running
        self.running = True
        self.datacollector.collect(self)

    def step(self):
        """
        Advance the model by one step and collect data.
        """
        self.schedule.step()

        # collect data
        self.datacollector.collect(self)

        # update iteration
        self.iteration += 1
        if self.iteration > self.max_iters:
            self.running = False

    def network_initialization(self):
        """
        Placeholder
        """
        for agent in self.schedule.agents_by_type[Citizen].values():

            # create a list of tuples of (agent, distance to agent) distances
            # from this agent to all other agents
            distances = []
            for other_agent in self.schedule.agents_by_type[Citizen].values():
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
                k=self.network_size,
            )

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

    # @staticmethod
    # def count_jailed(model):
    #     """
    #     Helper method to count jailed agents.
    #     """
    #     return len(
    #         [
    #             agent
    #             for agent in model.schedule.agents
    #             if agent.breed == "citizen" and agent.jail_sentence > 0
    #         ]
    #     )

    # @staticmethod
    # def speed_of_rebellion_calculation(model):
    #     """
    #     Calculates the speed of transmission of the rebellion.
    #     """
    #     if model.citizen_count == 0:
    #         return 0
    #     count = 0
    #     for agent in model.schedule.agents:
    #         if agent.breed == "citizen" and agent.flipped == True:
    #             count += 1
    #     return count / model.citizen_count
