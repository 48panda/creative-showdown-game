from program_renderer import renderer
from tiles import tile_key
import pygame
import random
from win_conditions import win_conditions
import copy

player = pygame.image.load("assets/player_tile.png")
player_pickup = pygame.image.load("assets/player_pickup.png")
goal = pygame.image.load("assets/goal.png")

class grid_renderer(renderer):
    def runner_fail_check(self):
        if not self.world[self.player_y][self.player_x].player_stand:
            return True
        return False
    def init_runner(self, data, **kwargs):
        self.hasTeleported = False
        self.programCounter = 0
        self.prevProgramCounter = -1
        self.timesRunCurrent = 0
        self.ticks_passed = 0
        self.time_since_last_run = 1000
        grid = data["grid"]
        key = data["grid_key"]
        world = []
        for y,row in enumerate(grid):
            new_row = []
            for x,cell in enumerate(row):
                new_row.append(tile_key[key[cell]])
            world.append(new_row)
        self.world = world
        self.player_x = data["player_x"]
        self.player_y = data["player_y"]
        self.goal_x = data["goal_x"]
        self.goal_y = data["goal_y"]
        self.win_conditions = data["win_conditions"]
        self.items = copy.deepcopy(data["items"])
        for item in self.items:
            item["num"] = random.randint(item["value"]["min"], item["value"]["max"])
        self.player_pickup = False
        self.last_move = None
        self.won = False
    def render_game(self,w,h):
        if not self.playing:
            for item in self.items:
                item["num"] = random.randint(item["value"]["min"], item["value"]["max"])
        game = pygame.Surface((w,h))
        game.fill((255,0,255))
        grid_w = w - 100
        grid_h = h - 100
        grid_w_per_cell = grid_w // len(self.world[0])
        grid_h_per_cell = grid_h // len(self.world)
        grid_cell_size = min(grid_w_per_cell, grid_h_per_cell)
        grid_w = grid_cell_size * len(self.world[0])
        grid_h = grid_cell_size * len(self.world)
        grid_x = (w - grid_w) // 2
        grid_y = (h - grid_h) // 2
        old_x = self.player_x
        old_y = self.player_y
        if self.last_move == "up":
            old_y += 1
        elif self.last_move == "down":
            old_y -= 1
        elif self.last_move == "left":
            old_x += 1
        elif self.last_move == "right":
            old_x -= 1
        if self.time_since_last_run < 500 and self.last_move != None:
            frac = self.time_since_last_run / 500
            render_x = old_x * (1-frac) + self.player_x * frac
            render_y = old_y * (1-frac) + self.player_y * frac
        else:
            if self.last_move != None and not self.world[self.player_y][self.player_x].player_stand:
                frac = (self.time_since_last_run - 500) / 500
                render_x = self.player_x
                render_y = self.player_y * (1-frac) + (self.player_y + 2) * frac
            else:  
                render_x = self.player_x
                render_y = self.player_y
        box_size = grid_cell_size // 2
        box_font = pygame.font.SysFont("Calibri bold", box_size - 5)
        for y,row in enumerate(self.world):
            for x,cell in enumerate(row):
                game.blit(pygame.transform.scale(cell.texture, (grid_cell_size, grid_cell_size)), (grid_x + x * grid_cell_size, grid_y + y * grid_cell_size))
                if max(self.player_x,old_x) == x and max(self.player_y,old_y) == y:
                    if self.player_pickup:
                        box_x = grid_x + render_x * grid_cell_size + box_size // 4
                        box_y = grid_y + render_y * grid_cell_size - box_size // 4 * 3
                        item = self.player_pickup
                        game.blit(pygame.transform.scale(player_pickup, (grid_cell_size, grid_cell_size)), (grid_x + render_x * grid_cell_size, grid_y + render_y * grid_cell_size))
                        pygame.draw.rect(game, (0,255,0), (box_x, box_y, box_size, box_size))
                        text = box_font.render(str(item["num"]).zfill(2), True, (0,0,0))
                        game.blit(text, (box_x + box_size // 2 - text.get_width() // 2, box_y + box_size // 2 - text.get_height() // 2))
                    else:
                        game.blit(pygame.transform.scale(player, (grid_cell_size, grid_cell_size)), (grid_x + render_x * grid_cell_size, grid_y + render_y * grid_cell_size))
        if {"type":"goal"} in self.win_conditions:
            game.blit(pygame.transform.scale(goal, (grid_cell_size, grid_cell_size)), (grid_x + self.goal_x * grid_cell_size, grid_y + self.goal_y * grid_cell_size))
        for item in self.items:
            if item["type"] == "box":
                render_x = grid_x + item["x"] * grid_cell_size
                render_y = grid_y + item["y"] * grid_cell_size
                box_x = render_x + grid_cell_size // 2 - box_size // 2
                box_y = render_y + grid_cell_size // 2 - box_size // 2
                pygame.draw.rect(game, (0,255,0), (box_x, box_y, box_size, box_size))
                text = box_font.render(str(item["num"]).zfill(2), True, (0,0,0))
                game.blit(text, (box_x + box_size // 2 - text.get_width() // 2, box_y + box_size // 2 - text.get_height() // 2))
        return game
    def value_getter(self, valueToGet):
        if valueToGet == "player x":
            return self.player_x
        elif valueToGet == "player y":
            return self.player_y
        elif valueToGet == "up":
            return self.world[self.player_y - 1][self.player_x]
    def validate_value_getter(self, valueToTest):
        return valueToTest in self.get_valid_values()
    def get_valid_values(self):
        return ["player x", "player y", "up", "down", "left", "right"]
    def pickup(self):
        if self.player_pickup:
            return
        index = None
        for i,item in enumerate(self.items):
            if item["x"] == self.player_x and item["y"] == self.player_y:
                index = i
        self.player_pickup = self.items.pop(index)
    def drop(self):
        if not self.player_pickup:
            return
        self.player_pickup["x"] = self.player_x
        self.player_pickup["y"] = self.player_y
        self.items.append(self.player_pickup)
        self.player_pickup = None
    def start_of_tick(self):
        self.world[self.player_y][self.player_x].stand(self)
    def move(self,direction):
        self.hasTeleported = False
        if direction == "up":
            self.player_y -= 1
        elif direction == "down":
            self.player_y += 1
        elif direction == "left":
            self.player_x -= 1
        elif direction == "right":
            self.player_x += 1
        if self.player_x < 0:
            self.player_x = 0
        if self.player_y < 0:
            self.player_y = 0
        if self.player_x >= len(self.world[0]):
            self.player_x = len(self.world[0]) - 1
        if self.player_y >= len(self.world):
            self.player_y = len(self.world) - 1
        if self.world[self.player_y][self.player_x].player_collide:
            if direction == "up":
                self.player_y += 1
            elif direction == "down":
                self.player_y -= 1
            elif direction == "left":
                self.player_x += 1
            elif direction == "right":
                self.player_x -= 1
        else:
            self.last_move = direction
    def check_win(self):
        won = True
        for win_condition in self.win_conditions:
            if not win_conditions[win_condition["type"]](self,win_condition):
                won = False
        return won