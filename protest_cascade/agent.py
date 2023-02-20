from protest_cascade.random_walk import RandomWalker

import mesa


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

    def step(self):
        """
        Decide whether to activate, then move if applicable.
        """
        # random movement
        if self.model.multiple_agents_per_cell:
            self.random_move()
        else:
            self.random_move_to_empty()
        # update neighborhood
        self.neighborhood = self.update_neighbors()
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
            self.private_preference + self.epsilon + (0.01 * actives_in_vision)
        )
        if self.opinion > self.threshold:
            self.condition = "Protest"
        else:
            self.condition = "Support"


