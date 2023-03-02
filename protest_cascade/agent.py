import mesa
import math
import logging as log

# set up logging for the model
log.basicConfig(
    filename="./log/protest_cascade.log",
    filemode="w",
    format="%(message)s",
    level=log.DEBUG,
)


class RandomWalker(mesa.Agent):
    """
    Class implementing random walker methods in a generalized manner.

    Not intended to be used on its own, but to inherit its methods to multiple
    other agents.
    """

    grid = None
    x = None
    y = None
    moore = True

    def __init__(self, unique_id, model, pos, moore=True):
        """
        grid: The MultiGrid object in which the agent lives.
        x: The agent's current x coordinate
        y: The agent's current y coordinate
        moore: If True, may move in all 8 directions.
                Otherwise, only up, down, left, right.
        """
        super().__init__(unique_id, model)
        self.pos = pos
        self.moore = moore

    def update_neighbors(self):
        """
        Update the list of neighbors.
        """
        self.neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=True, radius=self.vision
        )
        self.neighbors = self.model.grid.get_cell_list_contents(self.neighborhood)

    def random_move(self):
        """
        Step one cell in any allowable direction.
        """
        # Pick the next cell from the adjacent cells.
        next_moves = self.model.grid.get_neighborhood(self.pos, self.moore, True)

        # move towards other protesters if object type is Citizen and condition
        # is Protest or if object type is Security
        if (isinstance(self, Citizen) and self.ever_flipped) or isinstance(
            self, Security
        ):
            next_moves = self.move_towards(next_moves)

        # reduce to valid next moves if we don't allow multiple agents per cell
        if not self.model.multiple_agents_per_cell:
            next_moves = [
                empty for empty in next_moves if self.model.grid.is_cell_empty(empty)
            ]

        # If there are no valid moves stay put
        if not next_moves:
            return

        # randomly choose valid move
        next_move = self.random.choice(next_moves)

        # Now move:
        self.model.grid.move_agent(self, next_move)

    def determine_avg_loc(self):
        """
        Looks at surrounding cells and determines the average location of the
        of active agents in vision.
        """
        # if no neighbors, return self.pos
        if not self.neighborhood:
            return None

        # pull out the positions of active agents in vision
        pos_ag_list = [
            agent.pos for agent in self.neighborhood if agent.condition == "Protest"
        ]

        # calculate the average location of active agents in vision
        if len(pos_ag_list) > 0:
            avg_pos = (
                round(sum([pos[0] for pos in pos_ag_list]) / len(pos_ag_list)),
                round(sum([pos[1] for pos in pos_ag_list]) / len(pos_ag_list)),
            )
        # if no active agents in vision, stay put
        else:
            avg_pos = None

        # update memory
        self.memory = avg_pos

    def move_towards(self, next_moves):
        """
        Whittles choices of next moves to only those that move the agent closer
        to the average location of active agents in vision.
        """
        if self.memory is None:
            return next_moves

        closer_moves = [
            move
            for move in next_moves
            if self.distance(move, self.memory) < self.distance(self.pos, self.memory)
        ]
        return closer_moves

    def sigmoid(self, x):
        """
        Sigmoid function
        """
        return 1 / (1 + math.exp(-x))

    def logit(self, x):
        """
        Logit function
        """
        return math.log(x / (1 - x))

    def distance(self, pos1, pos2):
        """
        Calculates the distance between two points
        """
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)


class Citizen(RandomWalker):
    """
    Citizen agent class that inherits from RandomWalker class. This class
    looks at it's neighbors and decides whether to activate or not based on
    number of active neighbors and it's own activation level.
    """

    def __init__(
        self,
        unique_id,
        model,
        pos,
        vision,
        private_preference,
        epsilon,
        threshold,
    ):
        """
        Attributes and methods inherited from RandomWalker class:
        grid, x, y, moore, update_neighbors, random_move, determine_avg_loc,
        move_towards, sigmoid, logit, distance
        """
        super().__init__(unique_id, model, pos)
        # core agent attributes
        # self.pos = pos
        self.vision = vision

        # agent personality attributes
        self.private_preference = private_preference
        self.epsilon = epsilon
        self.threshold = threshold
        self.opinion = None
        self.activation = None
        self.risk_aversion = None

        # agent memory attributes
        self.network = None
        self.flip = None
        self.ever_flipped = False
        self.memory = None
        self.condition = "Support"

        # agent jail attributes
        self.jail_sentence = 0

    def step(self):
        """
        Decide whether to activate, then move if applicable.
        """
        # Set flip to False
        self.flip = False
        # jail sentence
        if self.jail_sentence > 0:
            self.jail_sentence -= 1
            return
        elif self.jail_sentence <= 0 and self.condition == "Jailed":
            self.pos = self.random.choice(list(self.model.grid.empties))
            log.debug(f"Citizen {self.unique_id}  was given {self.pos} after jail.")
            self.model.grid.place_agent(self, self.pos)
            log.debug(
                f"Grid position is confirmed to be {self.model.grid.get_cell_list_contents(self.pos)}"
            )

        # random movement
        self.random_move()
        # update neighborhood
        self.neighborhood = self.update_neighbors()
        # memorize avg location of acitve agents
        self.memory = self.determine_avg_loc()
        # based on neighborhood determine if support, oppose, or protest
        self.determine_condidion()

    def update_neighbors(self):
        """
        Look around and see who my neighbors are
        """
        self.neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=True, radius=self.vision
        )

        self.neighbors = self.model.grid.get_cell_list_contents(self.neighborhood)

    def determine_condidion(self):
        """
        activation function that determines whether citizen will support
        or protest.
        """
        # Count total active agents in vision
        actives_in_vision = 1.0  # citizen counts themself
        actives_in_vision += sum(
            [
                True
                for active in self.neighbors
                if isinstance(active, Citizen) and active.condition == "Protest"
            ]
        )
        security_in_vision = 1
        security_in_vision += sum(
            [True for active in self.neighbors if isinstance(active, Security)]
        )

        # Calculate opinion and determine condition
        self.opinion = (
            self.private_preference
            + self.epsilon
            + ((0.1 * actives_in_vision) / security_in_vision)
        )

        self.activation = self.sigmoid(self.opinion)

        # record previous condition
        prev_condition = self.condition

        if self.activation > self.threshold:
            if self.condition != "Protest":
                self.flip = True
                self.ever_flipped = True
            self.condition = "Protest"
        else:
            self.condition = "Support"

        if prev_condition != self.condition:
            log.debug(f"Agent {self.unique_id} -- {prev_condition} -> {self.condition}")


class Security(RandomWalker):
    """
    Security agent class that inherits from RandomWalker class. This class
    looks at it's neighbors and arrests active neighbor

    Attributes and methods inherited from RandomWalker class:
    grid, x, y, moore, update_neighbors, random_move, determine_avg_loc,
    move_towards, sigmoid, logit, distance
    """

    def __init__(self, unique_id, model, pos, vision):
        super().__init__(unique_id, model, pos)
        self.pos = pos
        self.vision = vision
        self.condition = "Support"
        self.memory = None

    def step(self):
        """
        Steps for security class to determine behavior
        """
        # random movement
        self.random_move()
        self.update_neighbors()
        self.arrest()

    def arrest(self):
        """
        Arrests active neighbor
        """
        neighbor_cells = self.model.grid.get_neighborhood(self.pos, moore=True)

        active_neighbors = [
            agent
            for agent in self.model.grid.get_cell_list_contents(neighbor_cells)
            if (isinstance(agent, Citizen) and agent.condition == "Protest")
        ]

        if active_neighbors:
            arrestee = self.random.choice(active_neighbors)
            sentence = self.random.randint(0, self.model.max_jail_term)
            arrestee.jail_sentence = sentence
            arrestee.condition = "Jailed"
            self.model.grid.remove_agent(arrestee)
            log.debug(f"====================================================")
            log.debug(f"Agent {arrestee.unique_id} -- ARRESTED")
            log.debug(f"Agent {arrestee.unique_id} -- SENTENCED TO {sentence} TURNS")
