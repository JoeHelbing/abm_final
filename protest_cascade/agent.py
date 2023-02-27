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
        self.active_agent_in_vision = False
        self.gravity_vec = None

    def update_neighbors(self):
        """
        Placeholder
        """
        self.neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=True, radius=self.vision
        )
        self.neighbors = self.model.grid.get_cell_list_contents(self.neighborhood)

        # update active agent in vision boolean
        self.active_agent_in_vision = any(
            agent.condition == "Protest" for agent in self.neighbors
        )

    def random_move(self):
        """
        Step one cell in any allowable direction.
        """
        # Pick the next cell from the adjacent cells.
        next_moves = self.model.grid.get_neighborhood(self.pos, self.moore, True)

        # reduce to valid next moves aka empties if we don't allow multiple
        # agents per cell
        if not self.model.multiple_agents_per_cell:
            next_moves = [
                empty for empty in next_moves if self.model.grid.is_cell_empty(empty)
            ]

        # move towards other protesters if object type is Citizen and condition
        # is Protest or if object type is Security
        if (isinstance(self, Citizen) and self.condition == "Protest") or isinstance(
            self, Security
        ):
            if self.active_agent_in_vision:
                # find direction of greatest mass of active agents in vision
                self.gravity_vec = self.gravity()
                next_moves = self.move_towards(next_moves)

        if (
            isinstance(self, Citizen)
            and self.condition == "Protest"
            and self.active_agent_in_vision
        ):
            log.debug(f"next_moves: {next_moves}")

        # If there are no valid moves stay put
        if not next_moves:
            return

        # randomly choose valid move
        next_move = self.random.choice(next_moves)

        # Now move:
        self.model.grid.move_agent(self, next_move)

    def move_towards(self, next_moves):
        """
        Whittles choices of next moves to only those that move the agent closer
        to the location greatest mass of active agents in vision.
        """
        closer_move = []
        # # remove moves that don't move agent closer to gravity vector position
        # closer_moves = min(
        #     [(self.distance(move, self.gravity_vec), move) for move in next_moves]
        # )

        # closer_move.append(closer_moves[1])

        # log.debug(f"Self pos: {self.pos}")
        # log.debug(f"Agent {self.unique_id} closer_move: {closer_move}")
        log.debug(f"Agent {self.unique_id} self pos: {self.pos}")
        log.debug(f"Agent {self.unique_id} gravity_vec: {self.gravity_vec}")
        log.debug(f"Agent {self.unique_id} next_moves: {next_moves}")
        if self.gravity_vec in next_moves:
            closer_move.append(self.gravity_vec)
            log.debug(f"Agent {self.unique_id} is going {closer_move}")
            return closer_move
        else:
            return

    def gravity(self):
        """
        Uses a gravity function to determine agent movement based on the
        distance between agent and other active agents.
        """
        force_x = 0
        force_y = 0

        active_neighbors = 0

        for agent in self.neighbors:
            if isinstance(agent, Citizen) and agent.condition == "Protest":
                active_neighbors += 1
                distance = self.distance(self.pos, agent.pos)
                force_x += (self.pos[0] - agent.pos[0]) / distance**2
                force_y += (self.pos[1] - agent.pos[1]) / distance**2

        if force_x > 0:
            force_x_r = 1
        elif force_x < 0:
            force_x_r = -1
        else:
            force_x_r = 0

        if force_y > 0:
            force_y_r = 1
        elif force_y < 0:
            force_y_r = -1
        else:
            force_y_r = 0

        log.debug(f"Agent {self.unique_id} force_x: {force_x}, force_y: {force_y}")
        log.debug(
            f"Agent {self.unique_id} force_x_r: {force_x_r}, force_y_r: {force_y_r}"
        )
        return self.pos[0] + force_x_r, self.pos[1] + force_y_r

    def sigmoid(self, x):
        """
        Sigmoid function
        """
        return 1 / (1 + math.exp(-x))

    def distance(self, pos1, pos2):
        """
        Calculates the distance between two points
        """
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)


class Citizen(RandomWalker):
    """
    Placeholder
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
        Placeholder
        """
        super().__init__(unique_id, model, pos)
        self.pos = pos
        self.vision = vision
        self.network = None
        self.condition = "Support"
        self.private_preference = private_preference
        self.epsilon = epsilon
        self.threshold = threshold
        self.neighborhood = None
        self.neighbors = None
        self.opinion = None
        self.activation = None
        self.flip = None
        self.ever_flipped = False
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

        # update neighbors
        self.update_neighbors()
        # random movement
        self.random_move()
        # based on neighborhood determine if support, oppose, or protest
        self.determine_condidion()

    def determine_condidion(self):
        """
        Placeholder
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
    Placeholder
    """

    def __init__(self, unique_id, model, pos, vision):
        """
        Placeholder
        """
        super().__init__(unique_id, model, pos)
        self.pos = pos
        self.vision = vision
        self.condition = "Support"
        self.gravity_val = None
        self.neighborhood = None
        self.neighbors = None

    def step(self):
        """
        Placeholder
        """
        # random movement
        self.random_move()
        self.update_neighbors()
        self.arrest()

    def arrest(self):
        """
        Placeholder
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
