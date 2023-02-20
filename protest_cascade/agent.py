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
        ):
        """
        Placeholder
        """
        super().__init__(unique_id, model, pos)
        self.pos = pos
        self.vision = vision
        self.network = None
        self.condition = "Support"

    def step(self):
        """
        Decide whether to activate, then move if applicable.
        """
        # 
        self.update_neighbors()
        if self.model.multiple_agents_per_cell:
            self.random_move()
        else:
            self.random_move_to_empty()
        

    def update_neighbors(self):
        """
        Look around and see who my neighbors are
        """
        self.neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=True, radius=self.vision
        )

        self.neighbors = self.model.grid.get_cell_list_contents(self.neighborhood)
        self.empty_neighbors = [
            c for c in self.neighborhood if self.model.grid.is_cell_empty(c)
        ]



# class Cop(mesa.Agent):
#     """
#     A cop for life.  No defection.
#     Summary of rule: Inspect local vision and arrest a random active agent.

#     Attributes:
#         unique_id: unique int
#         x, y: Grid coordinates
#         vision: number of cells in each direction (N, S, E and W) that cop is
#             able to inspect
#     """

#     def __init__(self, unique_id, model, pos, vision):
#         """
#         Create a new Cop.
#         Args:
#             unique_id: unique int
#             x, y: Grid coordinates
#             vision: number of cells in each direction (N, S, E and W) that
#                 agent can inspect. Exogenous.
#             model: model instance
#         """
#         super().__init__(unique_id, model)
#         self.breed = "cop"
#         self.pos = pos
#         self.vision = vision

#     def step(self):
#         """
#         Inspect local vision and arrest a random active agent. Move if
#         applicable.
#         """
#         self.update_neighbors()
#         active_neighbors = []
#         for agent in self.neighbors:
#             if (
#                 agent.breed == "citizen"
#                 and agent.condition == "Active"
#                 and agent.jail_sentence == 0
#             ):
#                 active_neighbors.append(agent)
#         if active_neighbors:
#             arrestee = self.random.choice(active_neighbors)
#             sentence = self.random.randint(0, self.model.max_jail_term)
#             arrestee.jail_sentence = sentence
#             arrestee.condition = "Jailed"
#         if self.model.movement and self.empty_neighbors:
#             new_pos = self.random.choice(self.empty_neighbors)
#             self.model.grid.move_agent(self, new_pos)

#     def update_neighbors(self):
#         """
#         Look around and see who my neighbors are.
#         """
#         self.neighborhood = self.model.grid.get_neighborhood(
#             self.pos, moore=True, radius=self.vision
#         )
#         self.neighbors = self.model.grid.get_cell_list_contents(self.neighborhood)
#         self.empty_neighbors = [
#             c for c in self.neighborhood if self.model.grid.is_cell_empty(c)
#         ]
