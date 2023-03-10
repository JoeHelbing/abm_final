import mesa
import math
import logging as log
import numpy as np
from protest_cascade.scheduler import SimultaneousActivationByTypeFiltered
from .agent import Citizen, Security


class ProtestCascade(mesa.Model):
    """
    Create ProtestCascade model with the following parameters:

    width: width of the grid
    height: height of the grid
    citizen_vision: vision of the citizen agents [some integer]
    citizen_density: density of the citizen agents [float between 0 and 1]
    security_density: density of the security agents [float between 0 and 1]
    security_vision: vision of the security agents [some integer]
    max_jail_term: maximum jail term for security agents [some integer]
    movement: whether or not agents can move [boolean]
    multiple_agents_per_cell: whether or not multiple agents can occupy the same cell [boolean]
    network: whether or not agents are connected in a network with fixed settings [boolean]
    network_discount: discount factor for network connections [float between 0 and 1]
    international_context: unused parameter currently
    private_preference_distribution_mean: the mean or center point of a normal distribution for private preference
    standard_deviation: the standard deviation of a normal distribution for private preference
    epsilon: the operationalization of authoritarianism representing error rate of agent understanding of "red line" and repression consequences
    threshold: value between 0 and 1 for threshold of (1 - threshold) for agent to protest
    max_iters: maximum number of iterations to run the model
    seed: seed for random number generator
    random_seed: whether or not to use a random seed for the random number generator
    """

    def __init__(
        self,
        width=40,
        height=40,
        citizen_vision=7,
        citizen_density=0.7,
        security_density=0.00,
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

        # model boolean constants
        self.movement = movement
        self.multiple_agents_per_cell = multiple_agents_per_cell
        self.network = network
        self.network_discount = network_discount

        # agent level constants
        self.international_context = international_context

        # model boolean constants
        self.movement = movement
        self.multiple_agents_per_cell = multiple_agents_per_cell
        self.network = network
        self.network_discount = network_discount

        # agent level constants
        self.international_context = international_context
        self.citizen_density = citizen_density
        self.citizen_vision = citizen_vision
        self.private_preference_distribution_mean = private_preference_distribution_mean
        self.standard_deviation = standard_deviation
        self.epsilon = epsilon
        self.threshold = 3.595
        self.security_density = security_density
        self.security_vision = security_vision

        # model level constants

        # model level constants
        self.max_jail_term = max_jail_term
        self.citizen_count = round(self.width * self.height * self.citizen_density)
        self.security_count = round(self.width * self.height * self.security_density)
        self.network_size = round(
            (((self.citizen_vision * 2 + 1) ** 2) - 1) * self.citizen_density
        )

        # model setup
        self.max_iters = max_iters

        # model setup
        self.max_iters = max_iters
        self.iteration = 0
        self.random_seed = random_seed
        self.schedule = SimultaneousActivationByTypeFiltered(self)
        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=True)

        # agent counts
        self.support_count = 0
        self.protest_count = 0

        # Create agents
        # create Citizens
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
                self.private_preference_distribution_mean, self.standard_deviation
            )
            # uniform distribution of error term on expectation of repression
            epsilon = self.random.gauss(0, self.epsilon)
            # uniform distribution of threshold for protest
            threshold = self.sigmoid(self.threshold + epsilon)
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

        # create Security
        for i in range(self.security_count):
            pos = None
            if not self.multiple_agents_per_cell and len(self.grid.empties) > 0:
                pos = self.random.choice(list(self.grid.empties))
            else:
                x = self.random.randrange(self.width)
                y = self.random.randrange(self.height)
                pos = (x, y)

            # normal distribution of private regime preference
            private_preference = self.random.gauss(
                self.private_preference_distribution_mean, self.standard_deviation
            )

            security = Security(
                self.next_id(),
                self,
                pos,
                self.security_vision,
                private_preference,
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
            "Security Density": self.report_security_density,
            "Private Preference": self.report_private_preference,
            "Episilon": self.report_epsilon,
            "Threshold": self.report_threshold,
        }
        agent_reporters = {
            "pos": lambda a: getattr(a, "pos", None),
            "condition": lambda a: getattr(a, "condition", None),
            "opinion": lambda a: getattr(a, "opinion", None),
            "activation": lambda a: getattr(a, "activation", None),
            "private_preference": lambda a: getattr(a, "private_preference", None),
            "epsilon": lambda a: getattr(a, "epsilon", None),
            "threshold": lambda a: getattr(a, "threshold", None),
            "jail_sentence": lambda a: getattr(a, "jail_sentence", None),
            "flip": lambda a: getattr(a, "flip", None),
            "ever_flipped": lambda a: getattr(a, "ever_flipped", None),
            "model_seed": lambda a: getattr(a, "dc_seed", None),
            "model_security_density": lambda a: getattr(a, "dc_security_density", None),
            "model_private_preference": lambda a: getattr(a, "dc_private_preference", None),
            "model_epsilon": lambda a: getattr(a, "dc_epsilon", None),
            "model_threshold": lambda a: getattr(a, "dc_threshold", None),
            }
        self.datacollector = mesa.DataCollector(
            model_reporters=model_reporters, agent_reporters=agent_reporters
        )

        # intializing the agent network
        if self.network:
            self.network_initialization()

        # set citizen states prior to first step
        for agent in self.schedule.agents_by_type[Citizen].values():
            agent.neighborhood = agent.update_neighbors()
            agent.determine_condition()

        # The final step is to set the model running
        self.running = True
        self.datacollector.collect(self)

    def step(self):
        """
        Advance the model by one step and collect data.
        """
        self.schedule.step()

        # defecting security outside of step function to avoid errors
        for agent in self.schedule.agents_by_type[Security].values():
            if agent.condition == "defect":
                agent.remove_thyself()
                del agent

        # collect data
        self.datacollector.collect(self)

        # update agent counts
        self.protest_count = self.count_protest(self)
        self.support_count = self.count_support(self)

        # update iteration
        self.iteration += 1
        if self.iteration > self.max_iters:
            self.running = False

    def network_initialization(self):
        """
        Initialize the network of agents for each agent in the model.

        preferences agents that are closer to them and normalizes the distances
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

    ############################################################################
    ############################################################################
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

    def sigmoid(self, x):
        """
        Sigmoid function
        """
        return 1 / (1 + math.exp(-x))

    ############################################################################
    ############################################################################
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
    
    @staticmethod
    def report_security_density(model):
        """
        Helper method to count security density.
        """
        return model.security_density
    
    @staticmethod
    def report_private_preference(model):
        """
        Helper method to count private preference distribution mean.
        """
        return model.private_preference_distribution_mean
    
    @staticmethod
    def report_epsilon(model):
        """
        Helper method to count epsilon.
        """
        return model.epsilon
    
    @staticmethod
    def report_threshold(model):
        """
        Helper method to count threshold.
        """
        return model.threshold
    