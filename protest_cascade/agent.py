from protest_cascade.random_walk import RandomWalker

import mesa
import logging as log

# set up logging for the model
log.basicConfig(
    filename="./log/protest_cascade.log",
    filemode="w",
    format="%(message)s",
    level=log.DEBUG,
)


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
        self.opinion = None
        self.activation = None
        self.flip = None
        self.memory = None

    def step(self):
        """
        Decide whether to activate, then move if applicable.
        """
        # Set flip to False
        self.flip = False
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
        Placeholder
        """
        # Count total active agents in vision
        actives_in_vision = 1.0  # citizen counts herself
        for c in self.neighbors:
            if c.condition == "Protest":
                actives_in_vision += 1

        # Calculate opinion and determine condition
        self.opinion = (
            self.private_preference + self.epsilon + (0.1 * actives_in_vision)
        )
        self.activation = self.sigmoid(self.opinion)
        log.debug(
            f"Agent {self.unique_id} -- opinion: {self.opinion}, activation: {self.activation}"
        )

        if self.activation > self.threshold:
            if self.condition != "Protest":
                self.flip = True
                log.debug(f"====================================================")
                log.debug(f"Agent {self.unique_id} Threshold -- {self.threshold}")
                log.debug(f"Agent {self.unique_id} -- FLIPPED TO PROTEST")
            self.condition = "Protest"
        else:
            self.condition = "Support"
