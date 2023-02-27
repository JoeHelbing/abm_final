import mesa
import math
import logging as log
import numpy as np
from protest_cascade.scheduler import RandomActivationByTypeFiltered
from .agent import Citizen, Security


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
        security_density=0.04,
        security_vision=7,
        max_jail_term=30,
        movement=True,
        multiple_agents_per_cell=False,
        network=False,
        network_discount=0.5,
        international_context=0.00,
        private_preference_distribution_mean=0,
        standard_deviation=1,
        epsilon=0.5,
        threshold=0.1,
        max_iters=1000,
        seed=None,
        random_seed=False,
    ):
        super().__init__()
        if random_seed:
            self.reset_randomizer(np.random.randint(0, 1000000))
        else:
            self.reset_randomizer(seed)
        print(f"Running ProtestCascade with seed {self._seed}")
        log.info(f"Running ProtestCascade with seed {self._seed}")
        self.width = width
        self.height = height
        self.citizen_density = citizen_density
        self.citizen_vision = citizen_vision
        self.security_density = security_density
        self.security_vision = security_vision
        self.movement = movement
        self.max_jail_term = max_jail_term
        self.max_iters = max_iters
        self.multiple_agents_per_cell = multiple_agents_per_cell
        self.network = network
        self.network_discount = network_discount
        self.citizen_count = round(self.width * self.height * self.citizen_density)
        self.security_count = round(self.width * self.height * self.security_density)
        self.network_size = round(
            (((self.citizen_vision * 2 + 1) ** 2) - 1) * self.citizen_density
        )
        self.epsilon = (epsilon / 2 * -1, epsilon / 2)
        self.threshold = 1 - threshold
        self.iteration = 0
        self.random_seed = random_seed
        self.schedule = RandomActivationByTypeFiltered(self)
        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=True)

        # theshold for protest agent level constants
        self.international_context = international_context

        # agent counts
        self.support_count = 0
        self.oppose_count = 0
        self.protest_count = 0

        # Create agents
        for i in range(self.citizen_count):
            pos = None
            if not self.multiple_agents_per_cell and len(self.grid.empties) > 0:
                pos = self.random.choice(list(self.grid.empties))
            else:
                x = self.random.randrange(self.width)
                y = self.random.randrange(self.height)
                pos = (x, y)
            # normal distribution of private regime preference
            private_preference = self.random.gauss(
                private_preference_distribution_mean, standard_deviation
            )
            # uniform distribution of error term on expectation of repression
            epsilon = self.random.uniform(self.epsilon[0], self.epsilon[1])
            # uniform distribution of threshold for protest
            threshold = self.random.uniform(self.threshold, 1)
            citizen = Citizen(
                self.next_id(),
                self,
                pos,
                self.citizen_vision,
                private_preference,
                epsilon,
                threshold,
            )
            self.grid.place_agent(citizen, pos)
            self.schedule.add(citizen)

        for i in range(self.security_count):
            pos = None
            if not self.multiple_agents_per_cell and len(self.grid.empties) > 0:
                pos = self.random.choice(list(self.grid.empties))
            else:
                x = self.random.randrange(self.width)
                y = self.random.randrange(self.height)
                pos = (x, y)
            security = Security(
                self.next_id(),
                self,
                pos,
                self.security_vision,
            )
            self.grid.place_agent(security, pos)
            self.schedule.add(security)

        # set up the data collector
        model_reporters = {
            "Seed": self.report_seed,
            "Citizen Count": self.count_citizen,
            "Protest Count": self.count_protest,
            "Support Count": self.count_support,
            "Jail Count": self.count_jail,
            "Speed of Spread": self.speed_of_spread,
        }
        agent_reporters = {
            "pos": lambda a: getattr(a, "pos", None),
            "condition": lambda a: getattr(a, "condition", None),
            "opinion": lambda a: getattr(a, "opinion", None),
            "activation": lambda a: getattr(a, "activation", None),
            "private_preference": lambda a: getattr(a, "private_preference", None),
            "epsilon": lambda a: getattr(a, "epsilon", None),
        }
        self.datacollector = mesa.DataCollector(
            model_reporters=model_reporters, agent_reporters=agent_reporters
        )

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
        log.debug("========================================")
        log.debug(f"Running step {self.iteration} of {self.max_iters}")
        self.schedule.step()

        # collect data
        self.datacollector.collect(self)

        # update agent counts
        self.protest_count = self.count_protest(self)

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

    """
    Section for model level helper methods used in ititialization and step.
    """

    def distance_calculation(self, agent1, agent2):
        """
        Helper method to calculate distance between two agents.
        """
        return math.sqrt(
            (agent1.pos[0] - agent2.pos[0]) ** 2 + (agent1.pos[1] - agent2.pos[1]) ** 2
        )

    """
    Section for helper methods used in data collection.
    """

    @staticmethod
    def report_seed(model):
        """
        Helper method to report the seed.
        """
        return model._seed

    @staticmethod
    def count_citizen(model):
        """
        Helper method to report the citizen count.
        """
        return model.citizen_count

    @staticmethod
    def speed_of_spread(model):
        """
        Calculates the speed of transmission of the rebellion.
        """
        return (
            len(
                [
                    agent
                    for agent in model.schedule.agents_by_type[Citizen].values()
                    if agent.flip is True
                ]
            )
            / model.citizen_count
        )

    @staticmethod
    def count_protest(model):
        """
        Helper method to count protesting agents.
        """
        return len(
            [
                agent
                for agent in model.schedule.agents_by_type[Citizen].values()
                if agent.condition == "Protest"
            ]
        )

    @staticmethod
    def count_support(model):
        """
        Helper method to count publicly supporting agents.
        """
        return len(
            [
                agent
                for agent in model.schedule.agents_by_type[Citizen].values()
                if agent.condition == "Support"
            ]
        )

    @staticmethod
    def count_jail(model):
        """
        Helper method to count jailed agents.
        """
        return len(
            [
                agent
                for agent in model.schedule.agents_by_type[Citizen].values()
                if agent.condition == "Jailed"
            ]
        )
