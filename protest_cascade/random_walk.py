"""
Generalized behavior for random walking, one grid cell at a time.
"""

import mesa
import math


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

    def random_move(self):
        """
        Step one cell in any allowable direction.
        """
        # Pick the next cell from the adjacent cells.
        next_moves = self.model.grid.get_neighborhood(self.pos, self.moore, True)

        # reduce to valid next moves if we don't allow multiple agents per cell
        if not self.model.multiple_agents_per_cell:
            next_moves = [
                empty for empty in next_moves if self.model.grid.is_cell_empty(empty)
            ]
        # move towards other protesters if protesting
        if self.condition == "Protest":
            next_moves = self.move_towards(next_moves)

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
