from time import sleep
import numpy as np
import random
import pygame
import keyboard
import math
import matplotlib.colors as colors
import matplotlib.pyplot as plt

from pygame import Color

# tile ids
DIRT = 0
GRASS = 1

# entity ids
EMPTY = 0
RABBIT = 1
FOX = 2

# tile update settings
GRASS_GROW_CHANCE = 0.005

# world settings
GRASS_TILE_PCT = 1
DIRT_TILE_PCT = 1 - GRASS_TILE_PCT

class World:
    def __init__(self, size, num_rabbits=10, num_foxes=2, tile_size=30):
        self.size = size
        self.tiles = np.zeros((size, size))
        self.tile_size = tile_size
        self.entities = np.zeros_like(self.tiles)

        self.init_grid()
        self.spawn_entities(num_rabbits, num_foxes)

        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.size * self.tile_size, self.size * self.tile_size))
        pygame.display.set_caption('World')


    def init_grid(self):
        self.tiles = np.random.choice([GRASS, DIRT], size=(self.size, self.size), p=[GRASS_TILE_PCT, DIRT_TILE_PCT])
    

    def spawn_entities(self, num_rabbits, num_foxes):
        # spawn rabbits
        for _ in range(num_rabbits):
            self.try_spawn_entity(RABBIT)

        # spawn foxes
        for _ in range(num_foxes):
            self.try_spawn_entity(FOX)


    def try_spawn_entity(self, entity_id):
        pos = self.get_spawnable_patch()
        if pos is None:
            print(f"No spawnable patch found - unable to spawn entity (id={entity_id})")
            return
        
        self.entities[pos] = entity_id


    # TODO update this to use a more efficient algorithm - get a list of empty patches and choose one at random
    def get_spawnable_patch(self, max_tries=20):
        patch_x = random.randint(0, self.size-1)
        patch_y = random.randint(0, self.size-1)

        i = 0
        while self.entities[patch_x, patch_y] != EMPTY:
            patch_x = random.randint(0, self.size-1)
            patch_y = random.randint(0, self.size-1)

            i += 1
            if i >= max_tries:
                return None

        return patch_x, patch_y


    def step(self):
        # move the foxes
        for x in range(self.size):
            for y in range(self.size):
                if self.entities[x, y] == FOX:
                    self.move_fox(x, y)
        
        # move the rabbits
        for x in range(self.size):
            for y in range(self.size):
                if self.entities[x, y] == RABBIT:
                    self.move_rabbit(x, y)
        
        # grow the grass
        for x in range(self.size):
            for y in range(self.size):
                if self.tiles[x, y] == DIRT:
                    self.grow_grass(x, y)


    def move_fox(self, x, y):
        # get the fox's neighbors
        neighbors = self.get_neighboring_entites(x, y)


        for n in neighbors:
            if self.entities[n] == RABBIT:
                self.entities[n] = FOX
                self.entities[x, y] = EMPTY
                return
        
        # otherwise, move to a random empty patch within 1 tile
        new_x = random.randint(max(0, x-1), min(self.size-1, x+1))
        new_y = random.randint(max(0, y-1), min(self.size-1, y+1))
        
        if self.entities[new_x, new_y] == EMPTY:
            self.entities[x, y] = EMPTY
            self.entities[new_x, new_y] = FOX

    
    def move_rabbit(self, x, y):
        # get the rabbit's neighbors
        neighbors = self.get_neighboring_entites(x, y, distance=2)

        # if there is a fox, run away from it
        for n in neighbors:
            if self.entities[n] == FOX:
                # move away from the fox
                new_x = x + (x - n[0])
                new_y = y + (y - n[1])

                # if the new position is out of bounds, don't move
                if new_x < 0 or new_x >= self.size or new_y < 0 or new_y >= self.size:
                    break
                
                # if the new position is empty, move there
                if self.entities[new_x, new_y] == EMPTY:
                    self.entities[x, y] = EMPTY
                    self.entities[new_x, new_y] = RABBIT
                    return

        # if there is grass on our tile, eat it with a small chance
        if self.tiles[x, y] == GRASS and random.random() < 0.05:
            self.tiles[x, y] = DIRT

        # otherwise, move to a square with grass 1 tile away
        new_x = random.randint(max(0, x-1), min(self.size-1, x+1))
        new_y = random.randint(max(0, y-1), min(self.size-1, y+1))

        if self.tiles[new_x, new_y] == GRASS and self.entities[new_x, new_y] == EMPTY:
            self.entities[x, y] = EMPTY
            self.entities[new_x, new_y] = RABBIT


    def get_neighboring_entites(self, x, y, distance=1):
        neighbors = []

        # get the neighbors (no edge wrapping, 8-connected, up to distance tiles away)
        for i in range(-distance, distance + 1):
            for j in range(-distance, distance + 1):
                if (i == 0 and j == 0) or x + i < 0 or x + i >= self.size or y + j < 0 or y + j >= self.size:
                    continue

                neighbors.append((x + i, y + j))
            
        return neighbors
        

    def grow_grass(self, x, y):
        if random.random() < GRASS_GROW_CHANCE and self.entities[x, y] == EMPTY:
            self.tiles[x, y] = GRASS
    

    def render(self):
       # Map colors to RGB values for the grid
        grid_color_map = {
            DIRT: Color(139, 69, 19),       # Brown
            GRASS: Color(0, 255, 0)         # Green
        }

        # Map colors to RGB values for the entities
        entity_color_map = {
            EMPTY: Color(0, 0, 0),          # Black
            RABBIT: Color(230, 230, 230),   # White
            FOX: Color(255, 0, 0)           # Red
        }

        # Tile size
        tile_size = self.tile_size
        entity_size = tile_size / 2

        # Clear the screen
        self.screen.fill((0, 0, 0))

        # Draw the grid
        for x in range(self.size):
            for y in range(self.size):
                pygame.draw.rect(self.screen, grid_color_map[self.tiles[x, y]], (x * tile_size, y * tile_size, tile_size, tile_size))

                # Draw the entities
                if self.entities[x, y] != EMPTY:
                    pygame.draw.rect(self.screen, entity_color_map[self.entities[x, y]], (x * tile_size + tile_size / 4, y * tile_size + tile_size / 4, entity_size, entity_size))


        # Update the display
        pygame.display.flip()


    def loop(self, interactive=False, ticks_per_second=5):

        while True:
            pygame.event.pump()  # Process events

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

                if interactive:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        self.step()
                        self.print_info(grid=False)
                        self.render()
            
            self.step()
            self.render()
            pygame.time.wait(int(1000 / ticks_per_second))


    def print_info(self, grid=True):
       
        if grid:
            print(self.entities)

        # get the number of each type of cell
        dirt_count = np.sum(self.entities == DIRT)
        grass_count = np.sum(self.entities == GRASS)
        rabbit_count = np.sum(self.entities == RABBIT)
        fox_count = np.sum(self.entities == FOX)

        print("Dirt: %d, Grass: %d, Rabbit: %d, Fox: %d" % (dirt_count, grass_count, rabbit_count, fox_count))


if __name__ == "__main__":
    world = World(100, num_rabbits=40, num_foxes=2, tile_size=10)
    world.loop(interactive=False, ticks_per_second=50)

    # world.print_info()
