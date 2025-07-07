import random
import heapq
import collections
from typing import List, Tuple, Dict, Optional

import pyxel

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------
CELL = 32               # tile size in pixels (sprites are 16×16)
MAZE_W, MAZE_H = 31, 31 # keep odd numbers (perfect maze)
VIEW_TILES_X = 17       # width of camera window in tiles (odd)
VIEW_TILES_Y = 13       # height of camera window in tiles (odd)
SCREEN_W = VIEW_TILES_X * CELL
SCREEN_H = VIEW_TILES_Y * CELL
FPS = 60

FOOTPRINT_TTL = 10 * FPS   # frames footprints persist
TRACK_INTERVAL = 12        # Jack replans every n frames
SIGHT_RANGE = 5            # tiles – how far Jack can spot prints / Danny
PLAYER_SPEED = 4           # pixels per frame (4 → one tile in 4 frames)
ENEMY_SPEED = 2
BRAID_PROB = 0.18          # probability to remove a wall when braiding
MAX_FOOTPRINTS = 300

# bank‑0 coordinates for tiles
TILE_SNOW   = (0, 0)
TILE_BUSH   = (CELL, 0)
TILE_FOOT   = (CELL * 2, 0)

# Direction helpers ----------------------------------------------------------
DIRS = {
    "UP":    (0, -1),
    "DOWN":  (0, 1),
    "LEFT":  (-1, 0),
    "RIGHT": (1, 0),
}

# ---------------------------------------------------------------------------
# Maze generation
# ---------------------------------------------------------------------------

def generate_maze(w: int, h: int) -> List[List[int]]:
    """Binary DFS maze (perfect). Passages are 1, walls are 0."""
    grid = [[0] * w for _ in range(h)]
    def carve(cx: int, cy: int):
        dirs = list(DIRS.values())
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = cx + dx * 2, cy + dy * 2
            if 0 < nx < w and 0 < ny < h and grid[ny][nx] == 0:
                grid[cy + dy][cx + dx] = 1
                grid[ny][nx] = 1
                carve(nx, ny)
    grid[1][1] = 1
    carve(1, 1)
    return grid


def braid_maze(grid: List[List[int]], p: float = BRAID_PROB) -> None:
    """Remove a fraction *p* of walls that separate adjacent passages to
    create loops, turning the perfect maze into a braided one.  Works in‑place."""
    h, w = len(grid), len(grid[0])
    for y in range(1, h - 1, 2):
        for x in range(1, w - 1, 2):
            if random.random() < p:
                choices = []
                for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and grid[ny][nx]:
                        choices.append((dx // 2, dy // 2))
                if choices:
                    dx, dy = random.choice(choices)
                    grid[y + dy][x + dx] = 1


def farthest_point(grid: List[List[int]], start: Tuple[int, int]):
    h, w = len(grid), len(grid[0])
    sx, sy = start
    dist = [[-1] * w for _ in range(h)]
    dist[sy][sx] = 0
    q = collections.deque([(sx, sy)])
    far, farpos = 0, start
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS.values():
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] == 1 and dist[ny][nx] == -1:
                dist[ny][nx] = dist[y][x] + 1
                q.append((nx, ny))
                if dist[ny][nx] > far:
                    far, farpos = dist[ny][nx], (nx, ny)
    return farpos

# ---------------------------------------------------------------------------
# A* path‑finding (Jack)
# ---------------------------------------------------------------------------

def astar(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]):
    if start == goal:
        return []
    h, w = len(grid), len(grid[0])
    sx, sy = start
    gx, gy = goal
    def hdist(x, y):
        return abs(x - gx) + abs(y - gy)
    open_set = [(hdist(sx, sy), 0, sx, sy)]
    came: Dict[Tuple[int, int], Tuple[int, int]] = {}
    g_cost = {start: 0}
    while open_set:
        _, cost, x, y = heapq.heappop(open_set)
        if (x, y) == goal:
            path = []
            while (x, y) != start:
                path.append((x, y))
                x, y = came[(x, y)]
            return path[::-1]
        for dx, dy in DIRS.values():
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] == 1:
                nc = cost + 1
                if nc < g_cost.get((nx, ny), 1e9):
                    g_cost[(nx, ny)] = nc
                    came[(nx, ny)] = (x, y)
                    heapq.heappush(open_set, (nc + hdist(nx, ny), nc, nx, ny))
    return []

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
class Footprint:
    def __init__(self, x: int, y: int):
        self.x, self.y = x, y
        self.ttl = FOOTPRINT_TTL

    @property
    def tile(self) -> Tuple[int, int]:
        return self.x, self.y

    def update(self) -> bool:
        self.ttl -= 1
        return self.ttl <= 0

    def draw(self, camx: int, camy: int):
        px, py = self.x * CELL - camx, self.y * CELL - camy
        if -CELL < px < SCREEN_W and -CELL < py < SCREEN_H:
            u, v = TILE_FOOT
            pyxel.blt(px, py, 0, u, v, CELL, CELL, 0)


class CharacterBase:
    ORIENT_U = {  # u‑offsets in bank image
        "DOWN": 0,
        "UP": CELL,
        "RIGHT": CELL * 2,
        "LEFT": CELL * 2,  # mirror for left
    }

    def __init__(self, x: int, y: int, bank: int):
        self.x, self.y = x, y
        self.px, self.py = x * CELL, y * CELL
        self.dir = "DOWN"
        self.bank = bank

    @property
    def tile(self) -> Tuple[int, int]:
        return self.x, self.y

    def draw(self, camx: int, camy: int):
        dx = self.px - camx
        dy = self.py - camy
        if -CELL < dx < SCREEN_W and -CELL < dy < SCREEN_H:
            u = self.ORIENT_U[self.dir]
            if self.dir == "LEFT":
                pyxel.blt(dx, dy, self.bank, u, 0, -CELL, CELL, 0)
            else:
                pyxel.blt(dx, dy, self.bank, u, 0, CELL, CELL, 0)


class Player(CharacterBase):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, bank=1)
        self.moving = False
        self.vx = self.vy = 0

    def handle_input(self, grid: List[List[int]]):
        if self.moving:
            return
        keymap = {
            pyxel.KEY_LEFT: "LEFT",
            pyxel.KEY_RIGHT: "RIGHT",
            pyxel.KEY_UP: "UP",
            pyxel.KEY_DOWN: "DOWN",
        }
        for key, d in keymap.items():
            if pyxel.btnp(key):
                dx, dy = DIRS[d]
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < MAZE_W and 0 <= ny < MAZE_H and grid[ny][nx] == 1:
                    self.dir = d
                    self.moving = True
                    self.vx, self.vy = dx * PLAYER_SPEED, dy * PLAYER_SPEED
                break

    def update(self):
        if self.moving:
            self.px += self.vx
            self.py += self.vy
            if self.px % CELL == 0 and self.py % CELL == 0:
                self.x, self.y = self.px // CELL, self.py // CELL
                self.moving = False


class Enemy(CharacterBase):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, bank=2)
        self.path: List[Tuple[int, int]] = []
        self.frame = 0

    # ------------------------------------------------------------------
    # Hunting logic
    # ------------------------------------------------------------------
    def _see_player(self, player_pos: Tuple[int, int]) -> bool:
        px, py = player_pos
        return abs(px - self.x) + abs(py - self.y) <= SIGHT_RANGE

    def _see_print(self, fp: Footprint) -> bool:
        return abs(fp.x - self.x) + abs(fp.y - self.y) <= SIGHT_RANGE

    def _nearest_visible_print(self, footprints: List[Footprint]) -> Optional[Tuple[int, int]]:
        for fp in reversed(footprints):  # newest first
            if self._see_print(fp):
                return fp.tile
        return None

    def _wander(self, grid: List[List[int]]) -> List[Tuple[int, int]]:
        """Pick a random target tile and return a path. Tries a few times."""
        for _ in range(30):
            tx = random.randrange(1, MAZE_W, 2)
            ty = random.randrange(1, MAZE_H, 2)
            if grid[ty][tx]:
                p = astar(grid, self.tile, (tx, ty))
                if p:
                    return p
        return []

    # ------------------------------------------------------------------
    def update(self, grid: List[List[int]], player_pos: Tuple[int, int], footprints: List[Footprint]):
        # re‑plan path periodically or when there is none
        if self.frame % TRACK_INTERVAL == 0 or not self.path:
            target = self._nearest_visible_print(footprints)
            if target is None and self._see_player(player_pos):
                target = player_pos
            if target is not None:
                self.path = astar(grid, self.tile, target)
            else:
                # wander if we have no clue
                if not self.path:
                    self.path = self._wander(grid)

        self.frame += 1

        # follow current path -----------------------------------------
        if self.path:
            tx, ty = self.path[0]
            # move pixel‑wise towards tx,ty
            if self.px < tx * CELL:
                self.px += ENEMY_SPEED; self.dir = "RIGHT"
            elif self.px > tx * CELL:
                self.px -= ENEMY_SPEED; self.dir = "LEFT"
            elif self.py < ty * CELL:
                self.py += ENEMY_SPEED; self.dir = "DOWN"
            elif self.py > ty * CELL:
                self.py -= ENEMY_SPEED; self.dir = "UP"
            # reached next step ?
            if self.px // CELL == tx and self.py // CELL == ty and self.px % CELL == 0 and self.py % CELL == 0:
                self.x, self.y = tx, ty
                self.path.pop(0)

# ---------------------------------------------------------------------------
# Game class
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        random.seed()
        self.grid = generate_maze(MAZE_W, MAZE_H)
        braid_maze(self.grid, BRAID_PROB)           # <‑‑ extra loops
        self.start = (1, 1)
        self.exit = farthest_point(self.grid, self.start)
        self.player = Player(*self.start)
        self.enemy = Enemy(*self.exit)
        self.footprints: List[Footprint] = []
        self.state = "RUN"
        pyxel.init(SCREEN_W, SCREEN_H, title="Shining Labyrinth", fps=FPS, quit_key=pyxel.KEY_ESCAPE)
        self._load_images()
        pyxel.run(self.update, self.draw)

    # ------------------------------------------------------------------
    def _load_images(self):
        # tiles (bank 0)
        pyxel.images[0].load(0, 0, "src/sprites/labyrinth/snow.png")
        pyxel.images[0].load(CELL, 0, "src/sprites/labyrinth/bush.png")
        pyxel.images[0].load(CELL*2, 0, "src/sprites/labyrinth/snow-footstep.png")
        # Danny (bank 1) – 3 orientations packed horizontally
        pyxel.images[1].load(0, 0, "src/sprites/danny/danny-front.png")
        pyxel.images[1].load(CELL, 0, "src/sprites/danny/danny-back.png")
        pyxel.images[1].load(CELL*2, 0, "src/sprites/danny/danny-side.png")
        # Jack (bank 2)
        pyxel.images[2].load(0, 0, "src/sprites/jack/jack-front.png")
        pyxel.images[2].load(CELL, 0, "src/sprites/jack/jack-back.png")
        pyxel.images[2].load(CELL*2, 0, "src/sprites/jack/jack-side.png")

    # ------------------------------------------------------------------
    def update(self):
        if self.state != "RUN":
            if pyxel.btnp(pyxel.KEY_R):
                self.__init__()
            return

        # -- Player -----------------------------------------------------
        old_tile = self.player.tile
        self.player.handle_input(self.grid)
        self.player.update()

        # leave footprint on the tile Danny *just vacated*
        if self.player.tile != old_tile:
            if not self.footprints or self.footprints[-1].tile != old_tile:
                self.footprints.append(Footprint(*old_tile))
                if len(self.footprints) > MAX_FOOTPRINTS:
                    self.footprints.pop(0)

        # -- Enemy ------------------------------------------------------
        self.enemy.update(self.grid, self.player.tile, self.footprints)

        # -- Time on footprints ----------------------------------------
        self.footprints[:] = [fp for fp in self.footprints if not fp.update()]

        # -- Win / lose -------------------------------------------------
        if self.player.tile == self.enemy.tile:
            self.state = "LOSE"
        elif self.player.tile == self.exit:
            self.state = "WIN"

    # ------------------------------------------------------------------
    def _camera(self) -> Tuple[int, int]:
        camx = self.player.px - SCREEN_W // 2 + CELL // 2
        camy = self.player.py - SCREEN_H // 2 + CELL // 2
        camx = max(0, min(camx, MAZE_W * CELL - SCREEN_W))
        camy = max(0, min(camy, MAZE_H * CELL - SCREEN_H))
        return camx, camy

    def draw(self):
        camx, camy = self._camera()
        pyxel.cls(0)
        # Draw visible slice ------------------------------------------
        minx = camx // CELL
        miny = camy // CELL
        maxx = minx + VIEW_TILES_X + 1
        maxy = miny + VIEW_TILES_Y + 1
        for y in range(miny, maxy):
            for x in range(minx, maxx):
                if 0 <= x < MAZE_W and 0 <= y < MAZE_H:
                    u, v = TILE_SNOW if self.grid[y][x] == 1 else TILE_BUSH
                    dx = x * CELL - camx
                    dy = y * CELL - camy
                    pyxel.blt(dx, dy, 0, u, v, CELL, CELL, 0)
        # footprints & actors ----------------------------------------
        for fp in self.footprints:
            fp.draw(camx, camy)
        self.player.draw(camx, camy)
        self.enemy.draw(camx, camy)
        # highlight exit if on screen ---------------------------------
        ex, ey = self.exit
        dx = ex * CELL - camx
        dy = ey * CELL - camy
        if -CELL < dx < SCREEN_W and -CELL < dy < SCREEN_H:
            pyxel.rectb(dx+1, dy+1, CELL-2, CELL-2, 11)
        # overlay ------------------------------------------------------
        if self.state == "WIN":
            pyxel.text(SCREEN_W//2-20, SCREEN_H//2, "YOU ESCAPED!", 10)
            pyxel.text(SCREEN_W//2-40, SCREEN_H//2+8, "Press R to restart", 7)
        elif self.state == "LOSE":
            pyxel.text(SCREEN_W//2-24, SCREEN_H//2, "HERE'S JOHNNY!", 8)
            pyxel.text(SCREEN_W//2-40, SCREEN_H//2+8, "Press R to restart", 7)


if __name__ == "__main__":
    Game()
