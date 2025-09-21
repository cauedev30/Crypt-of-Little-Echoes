# main.py
#
# Jogo simples de roguelike com visão de cima escrito para PgZero,
# seguindo as restrições do projeto:
# - Apenas PgZero, math, random e Rect do pygame são usados.
# - Nenhuma imagem externa é necessária (a animação dos sprites é desenhada proceduralmente).
# - Músicas e sons devem ser fornecidos pelo usuário nas pastas /music e /sounds.
#
# Como executar:
# 1) Coloque bg_loop.ogg em music/, hit.wav, pickup.wav, menu_click.wav em sounds/
# 2) Execute com: pgzrun main.py
#
# Autor: Cursor (assistente), escrito para ser único e pedagógico.
# Nome do jogo: "Crypt of Little Echoes"

import math
import random
from pygame import Rect

# ----------------------------
# PREFERÊNCIAS E CONSTANTES
# ----------------------------
TITLE = "Crypt of Little Echoes"
WIDTH = 900
HEIGHT = 600

# Constantes de jogabilidade
TILE_SIZE = 40
MAP_COLS = WIDTH // TILE_SIZE
MAP_ROWS = HEIGHT // TILE_SIZE

PLAYER_SPEED = 130  # pixels por segundo
ENEMY_SPEED = 70
PLAYER_MAX_HEALTH = 5
INVULNERABILITY_TIME = 1.0  # segundos após ser atingido

# Configuração do inimigo
ENEMY_COUNT = 6
ENEMY_MIN_PATROL = 60
ENEMY_MAX_PATROL = 220

# UI / Menu
MENU_BG_COLOR = (18, 18, 24)

# Cores (RGB)
COLOR_BG = (20, 20, 30)
COLOR_WALL = (40, 40, 60)
COLOR_FLOOR = (28, 28, 38)
COLOR_TEXT = (230, 230, 230)
COLOR_HIGHLIGHT = (100, 160, 255)
COLOR_PLAYER = (200, 200, 70)

# Nomes dos arquivos de áudio (coloque seus arquivos nos locais corretos)
BGM_FILENAME = "bg_loop"  # nome do arquivo sem extensão na pasta music/
SOUND_HIT = "hit"
SOUND_PICKUP = "pickup"
SOUND_CLICK = "menu_click"

# ----------------------------
# ESTADO DO JOGO
# ----------------------------
# modo: "menu", "playing" (jogando), "gameover" (fim de jogo), "quit" (sair)
mode = "menu"
music_enabled = True

# Pontuação e nível
player_score = 0
level_time = 0.0

# ----------------------------
# UTILITÁRIOS AUXILIARES
# ----------------------------
def clamp(value, a, b):
    """Limita o valor ao intervalo [a, b]."""
    return max(a, min(b, value))


def rect_collide(r1: Rect, r2: Rect) -> bool:
    """Função auxiliar para colisão de retângulos."""
    return r1.colliderect(r2)


def distance(a, b):
    """Distância euclidiana entre dois pontos (x, y)."""
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.hypot(dx, dy)


# ----------------------------
# CLASSE BOTÃO DA UI
# ----------------------------
class Button:
    """Botão clicável usado nos menus."""

    def __init__(self, text, x, y, w, h):
        self.text = text
        self.rect = Rect(x, y, w, h)
        self.hovered = False

    def draw(self):
        screen.draw.filled_rect(self.rect, (40, 44, 52) if not self.hovered else (60, 90, 140))
        screen.draw.rect(self.rect, (180, 180, 180))
        # Calcula a posição do texto para centralização
        text_x = self.rect.x + self.rect.width // 2
        text_y = self.rect.y + self.rect.height // 2
        screen.draw.text(
            self.text,
            (text_x, text_y),
            color=COLOR_TEXT,
            fontsize=28,
            align="center",
        )

    def update_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


# ----------------------------
# CLASSE DO JOGADOR
# ----------------------------
class Player:
    """Jogador com visão de cima. Animação controlada pelo índice do frame e desenho procedural."""

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.width = 22
        self.height = 28
        self.health = PLAYER_MAX_HEALTH
        self.score = 0
        self.speed = PLAYER_SPEED
        self.direction = (0, -1)  # vetor normalizado para onde o jogador se moveu pela última vez
        self.frame_timer = 0.0
        self.frame = 0
        self.idle_timer = 0.0
        self.invulnerable_until = 0.0

    def rect(self):
        return Rect(int(self.x - self.width / 2), int(self.y - self.height / 2), self.width, self.height)

    def take_damage(self, amount, now):
        if now < self.invulnerable_until:
            return False  # ainda invulnerável
        self.health -= amount
        self.invulnerable_until = now + INVULNERABILITY_TIME
        safe_play_sound(SOUND_HIT)
        return True

    def update(self, dt):
        # Entrada de movimento
        dx = 0
        dy = 0
        if keyboard.left or keyboard.a:
            dx -= 1
        if keyboard.right or keyboard.d:
            dx += 1
        if keyboard.up or keyboard.w:
            dy -= 1
        if keyboard.down or keyboard.s:
            dy += 1

        moving = dx != 0 or dy != 0
        if moving:
            # Normaliza para evitar movimento diagonal mais rápido
            length = math.hypot(dx, dy)
            if length != 0:
                nx = dx / length
                ny = dy / length
            else:
                nx = 0
                ny = 0
            # Aplica o movimento
            self.x += nx * self.speed * dt
            self.y += ny * self.speed * dt
            self.direction = (nx, ny)
            self.frame_timer += dt
            self.idle_timer = 0.0
        else:
            self.idle_timer += dt
            self.frame_timer += dt * 0.5  # animação de ocioso mais lenta

        # Reinicia o índice do frame a cada 0.12 segundos (andando) ou mais devagar se estiver ocioso
        frame_speed = 0.12 if moving else 0.28
        if self.frame_timer >= frame_speed:
            self.frame_timer = 0.0
            self.frame = (self.frame + 1) % 4

        # Mantém o jogador dentro dos limites da tela (simples)
        self.x = clamp(self.x, self.width / 2 + 2, WIDTH - self.width / 2 - 2)
        self.y = clamp(self.y, self.height / 2 + 2, HEIGHT - self.height / 2 - 2)

    def draw(self, now):
        # Desenha o jogador como um corpo pequeno + "pés/cabeça" animados dependendo do frame
        center = (int(self.x), int(self.y))

        # Corpo
        body_w = 18
        body_h = 20
        body_rect = Rect(center[0] - body_w // 2, center[1] - body_h // 2, body_w, body_h)

        # Pisca durante a invulnerabilidade
        flash = False
        if now < self.invulnerable_until:
            # Pisca a cada 0.12s
            flash = int(now * 8) % 2 == 0

        body_color = COLOR_PLAYER if not flash else (255, 255, 255)
        screen.draw.filled_rect(body_rect, body_color)

        # Cabeça (círculo pequeno)
        head_pos = (center[0], center[1] - body_h // 2 - 6)
        screen.draw.filled_circle(head_pos, 7, (220, 160, 100) if not flash else (255, 255, 255))

        # Animação simples de "pernas" do sprite: desenha dois retângulos que se deslocam
        leg_offset = (self.frame % 2) * 4 - 2  # -2 ou 2
        # Desenha perna esquerda
        l_leg = Rect(center[0] - 6 + leg_offset, center[1] + 10, 6, 10)
        # Desenha perna direita
        r_leg = Rect(center[0] + 0 - leg_offset, center[1] + 10, 6, 10)
        screen.draw.filled_rect(l_leg, (150, 90, 40))
        screen.draw.filled_rect(r_leg, (150, 90, 40))

        # Olho direcional para indicar para onde está virado
        dx, dy = self.direction
        eye_x = center[0] + int(dx * 6)
        eye_y = center[1] - body_h // 2 - 6 + int(dy * 6)
        screen.draw.filled_circle((eye_x, eye_y), 2, (10, 10, 10))


# ----------------------------
# CLASSE DO INIMIGO
# ----------------------------
class Enemy:
    """Inimigo simples que patrulha em um retângulo de território. Animado proceduralmente."""

    def __init__(self, center_x, center_y, territory_radius):
        self.x = float(center_x)
        self.y = float(center_y)
        self.territory_center = (center_x, center_y)
        self.territory_radius = territory_radius
        self.speed = ENEMY_SPEED * (0.85 + random.random() * 0.4)
        self.width = 20
        self.height = 26
        self.frame = random.randint(0, 3)
        self.frame_timer = random.random() * 0.5
        # Escolhe um alvo de patrulha aleatório dentro do território
        self.target = self.random_point_in_territory()
        # Pequenos temporizadores de pausa para ociosidade/patrulha
        self.pause_until = 0.0
        self.is_alert = False  # quando está perseguindo o jogador
        self.chase_timeout = 0.0

    def rect(self):
        return Rect(int(self.x - self.width / 2), int(self.y - self.height / 2), self.width, self.height)

    def random_point_in_territory(self):
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(10, self.territory_radius)
        tx = self.territory_center[0] + math.cos(angle) * r
        ty = self.territory_center[1] + math.sin(angle) * r
        return (tx, ty)

    def update(self, dt, player: Player, now):
        # Se viu o jogador recentemente (is_alert), persegue por um tempo
        px, py = player.x, player.y
        dist_to_player = distance((self.x, self.y), (px, py))

        # Raio de percepção (inimigo percebe o jogador dentro de um certo alcance)
        perception = 100
        if dist_to_player < perception:
            self.is_alert = True
            self.chase_timeout = now + 2.0  # persegue por 2 segundos após perder de vista

        if self.is_alert and now < self.chase_timeout:
            # Move em direção ao jogador
            dx = px - self.x
            dy = py - self.y
            length = math.hypot(dx, dy) or 1
            nx = dx / length
            ny = dy / length
            self.x += nx * self.speed * dt * 1.2  # um pouco mais rápido ao perseguir
            self.y += ny * self.speed * dt * 1.2
        else:
            self.is_alert = False
            # Comportamento de patrulha: vai até o alvo, pausa, escolhe um novo
            if now < self.pause_until:
                # pausado
                pass
            else:
                tx, ty = self.target
                dx = tx - self.x
                dy = ty - self.y
                dist = math.hypot(dx, dy)
                if dist < 6:
                    # alcançou o alvo: pausa e escolhe outro
                    self.pause_until = now + random.uniform(0.6, 1.6)
                    self.target = self.random_point_in_territory()
                else:
                    nx = dx / dist
                    ny = dy / dist
                    self.x += nx * self.speed * dt
                    self.y += ny * self.speed * dt

        # Animação do frame
        self.frame_timer += dt
        if self.frame_timer >= 0.16:
            self.frame_timer = 0
            self.frame = (self.frame + 1) % 4

        # Mantém os inimigos dentro de seu território (limitação suave)
        cx, cy = self.territory_center
        angle = math.atan2(self.y - cy, self.x - cx)
        r = math.hypot(self.x - cx, self.y - cy)
        if r > self.territory_radius + 10:
            # empurra de volta para dentro
            self.x = cx + math.cos(angle) * (self.territory_radius - 6)
            self.y = cy + math.sin(angle) * (self.territory_radius - 6)

    def draw(self, now):
        # Desenha o inimigo como um corpo colorido com "barbatanas" ou pernas que se animam
        center = (int(self.x), int(self.y))
        # A cor do corpo muda se estiver em alerta
        base_color = (200, 100, 100) if not self.is_alert else (240, 80, 60)
        body = Rect(center[0] - 10, center[1] - 12, 20, 22)
        screen.draw.filled_rect(body, base_color)

        # Olho que olha em direção ao jogador se estiver em alerta
        screen.draw.filled_circle((center[0] + (self.frame - 1) * 1, center[1] - 6), 3, (20, 20, 20))

        # Animação simples de barbatana/perna
        fin_offset = (self.frame % 2) * 3 - 1
        f1 = Rect(center[0] - 12, center[1] + 6 + fin_offset, 6, 8)
        f2 = Rect(center[0] + 6, center[1] + 6 - fin_offset, 6, 8)
        screen.draw.filled_rect(f1, (120, 70, 40))
        screen.draw.filled_rect(f2, (120, 70, 40))

        # Dica de território (círculo pequeno e semitransparente) quando pausado ou no menu para ajudar a depurar
        # (não obstrutivo na jogabilidade)
        if mode == "menu":
            pass  # não desenhar territórios no menu
        # depuração opcional: screen.draw.circle(self.territory_center, self.territory_radius, (80,80,80))


# ----------------------------
# MAPA E ITENS
# ----------------------------
class Item:
    """Itens coletáveis simples colocados no chão. Animados como círculos pulsantes."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.pulse_timer = random.random() * 2

    def rect(self):
        return Rect(int(self.x - 8), int(self.y - 8), 16, 16)

    def update(self, dt):
        self.pulse_timer += dt

    def draw(self):
        # Raio pulsante
        r = 6 + math.sin(self.pulse_timer * 4) * 2
        screen.draw.filled_circle((int(self.x), int(self.y)), int(abs(r)), (120, 220, 160))


def generate_items(count=8):
    items_list = []
    margin = 40
    for _ in range(count):
        x = random.randint(margin, WIDTH - margin)
        y = random.randint(margin, HEIGHT - margin)
        items_list.append(Item(x, y))
    return items_list


# ----------------------------
# CONFIGURAÇÃO DO JOGO
# ----------------------------
# Ponto de surgimento do jogador
player = Player(WIDTH // 2, HEIGHT // 2)

# Lista de inimigos
enemies = []

def spawn_enemies(count):
    """Gera inimigos espalhados pelo mapa, cada um com seu próprio território."""
    result = []
    for i in range(count):
        # Escolhe um ponto central, evitando sobreposição direta com o jogador
        while True:
            cx = random.randint(80, WIDTH - 80)
            cy = random.randint(80, HEIGHT - 80)
            if distance((cx, cy), (player.x, player.y)) > 120:
                break
        territory_radius = random.randint(ENEMY_MIN_PATROL, ENEMY_MAX_PATROL)
        e = Enemy(cx, cy, territory_radius)
        # varia a posição inicial do inimigo dentro do território
        e.x = cx + random.uniform(-territory_radius / 2, territory_radius / 2)
        e.y = cy + random.uniform(-territory_radius / 2, territory_radius / 2)
        result.append(e)
    return result

# Itens
items = generate_items(10)

# Botões do menu
btn_start = Button("Start Game", WIDTH // 2 - 120, HEIGHT // 2 - 60, 240, 48)
btn_music = Button("Music: On", WIDTH // 2 - 120, HEIGHT // 2 + 6, 240, 48)
btn_exit = Button("Exit", WIDTH // 2 - 120, HEIGHT // 2 + 72, 240, 48)

# ----------------------------
# Hooks do Pygame Zero
# ----------------------------
def start_new_game():
    """Inicializa / reseta todas as variáveis de jogabilidade para iniciar uma nova partida."""
    global player, enemies, items, player_score, level_time, mode
    player = Player(WIDTH // 2, HEIGHT // 2)
    enemies = spawn_enemies(ENEMY_COUNT)
    items = generate_items(10)
    player_score = 0
    level_time = 0.0
    mode = "playing"
    # Inicia a música de fundo (com tratamento de erros)
    safe_play_music(BGM_FILENAME)


# gera inimigos inicialmente
enemies = spawn_enemies(ENEMY_COUNT)


def on_key_down(key):
    """Lida com pressionamentos de teclas globais: M alterna a música; ESC retorna ao menu."""
    global music_enabled, mode
    if key == keys.M:
        music_enabled = not music_enabled
        if music_enabled:
            safe_play_music(BGM_FILENAME)
        else:
            safe_stop_music()
    if key == keys.ESCAPE:
        if mode == "playing":
            # volta para o menu (pausa)
            mode = "menu"
            safe_stop_music()


def on_mouse_down(pos):
    """Lida com cliques nos botões do menu apenas no modo de menu."""
    global mode, music_enabled
    if mode != "menu":
        return
    if btn_start.clicked(pos):
        safe_play_sound(SOUND_CLICK)
        start_new_game()
    elif btn_music.clicked(pos):
        music_enabled = not music_enabled
        btn_music.text = "Music: On" if music_enabled else "Music: Off"
        if music_enabled:
            safe_play_music(BGM_FILENAME)
        else:
            safe_stop_music()
        safe_play_sound(SOUND_CLICK)
    elif btn_exit.clicked(pos):
        safe_play_sound(SOUND_CLICK)
        # Não podemos chamar sys.exit() porque apenas módulos permitidos foram especificados.
        # Em vez disso, define o modo como "quit", que mostrará uma tela de despedida e interromperá as atualizações.
        mode = "quit"


def update(dt):
    """Loop de atualização principal — chamado com dt (segundos desde a última chamada)."""
    global player_score, level_time, mode

    if mode == "quit":
        # Congela o estado do jogo; não atualiza
        return

    if mode == "menu":
        # Atualiza os estados de hover do menu a partir da posição do mouse
        # Usa uma abordagem simples - os botões atualizarão o hover em on_mouse_down
        return

    if mode == "playing":
        # Atualiza os temporizadores
        level_time += dt
        now = level_time

        # Atualiza o jogador
        player.update(dt)

        # Atualiza os itens
        for it in items:
            if not it.collected:
                it.update(dt)
                if rect_collide(it.rect(), player.rect()):
                    it.collected = True
                    player_score_plus = 10
                    player.score += player_score_plus
                    safe_play_sound(SOUND_PICKUP)

        # Atualiza os inimigos
        for e in enemies:
            e.update(dt, player, now)

            # Verifica colisões com o jogador
            if rect_collide(e.rect(), player.rect()):
                # Causa dano se não estiver invulnerável
                if player.take_damage(1, now):
                    # Quando o jogador morre
                    if player.health <= 0:
                        # Fim de jogo
                        mode = "gameover"
                        safe_stop_music()

        # Condição de vitória: coletar todos os itens
        if all(it.collected for it in items):
            # Pequena recompensa, gera novos itens e inimigos adicionais (progressivo)
            player.score += 50
            new_enemy_count = 2
            enemies.extend(spawn_enemies(new_enemy_count))
            # gera itens novamente, mas em menor quantidade
            items[:] = generate_items(6)

    # Nenhum outro modo requer atualização


def draw_map():
    """Desenha um chão de ladrilhos com algumas paredes nas bordas para dar uma sensação de masmorra."""
    # fundo do chão
    screen.fill(COLOR_BG)
    # chão com padrão simples: ladrilhos alternados
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            x = c * TILE_SIZE
            y = r * TILE_SIZE
            # pequena variação
            if (r + c) % 2 == 0:
                screen.draw.filled_rect(Rect(x, y, TILE_SIZE, TILE_SIZE), COLOR_FLOOR)
            else:
                screen.draw.filled_rect(Rect(x, y, TILE_SIZE, TILE_SIZE), (24, 24, 34))

    # paredes simples: borda
    wall_thickness = 6
    screen.draw.filled_rect(Rect(0, 0, WIDTH, wall_thickness), COLOR_WALL)
    screen.draw.filled_rect(Rect(0, 0, wall_thickness, HEIGHT), COLOR_WALL)
    screen.draw.filled_rect(Rect(0, HEIGHT - wall_thickness, WIDTH, wall_thickness), COLOR_WALL)
    screen.draw.filled_rect(Rect(WIDTH - wall_thickness, 0, wall_thickness, HEIGHT), COLOR_WALL)


def draw_hud():
    """Desenha a vida do jogador, pontuação e dicas."""
    # Corações de vida
    for i in range(PLAYER_MAX_HEALTH):
        x = 12 + i * 28
        y = 12
        if i < player.health:
            screen.draw.filled_rect(Rect(x, y, 20, 12), (220, 50, 50))
        else:
            screen.draw.rect(Rect(x, y, 20, 12), (90, 90, 90))

    # Pontuação
    screen.draw.text(f"Score: {player.score}", (WIDTH - 180, 12), fontsize=28, color=COLOR_TEXT)
    # Dicas
    screen.draw.text("M para alternar música  •  ESC para ir ao menu", (12, HEIGHT - 28), fontsize=18, color=(160, 160, 160))


def draw():
    """Hook de desenho principal chamado pelo PgZero a cada frame."""
    screen.surface.set_alpha(None)  # garante que não haja alfa estranho
    if mode == "menu":
        # Fundo do menu
        screen.fill(MENU_BG_COLOR)
        # Título
        screen.draw.text(TITLE, center=(WIDTH // 2, HEIGHT // 2 - 140), fontsize=46, color=COLOR_TEXT, owidth=1)
        # Subtítulo
        screen.draw.text("Um projeto prático compacto de rogue-lite", center=(WIDTH // 2, HEIGHT // 2 - 100), fontsize=20, color=(180, 180, 200))
        # Botões
        btn_start.draw()
        btn_music.draw()
        btn_exit.draw()

        # Pequenos créditos
        screen.draw.text("Controles: Setas / WASD para mover", (WIDTH // 2, HEIGHT - 60), fontsize=16, color=(170, 170, 170), align="center")
        screen.draw.text("Música e som: alterne com o botão ou pressione M", (WIDTH // 2, HEIGHT - 40), fontsize=14, color=(140, 140, 140), align="center")
        return

    if mode == "quit":
        screen.fill((10, 10, 12))
        screen.draw.text("Até logo!", center=(WIDTH // 2, HEIGHT // 2), fontsize=48, color=COLOR_TEXT)
        screen.draw.text("Feche esta janela para sair.", center=(WIDTH // 2, HEIGHT // 2 + 64), fontsize=20, color=(160, 160, 160))
        return

    if mode == "gameover":
        # Desenha o mapa do último frame como fundo (simples)
        draw_map()
        for it in items:
            if not it.collected:
                it.draw()
        for e in enemies:
            e.draw(level_time)
        player.draw(level_time)

        # Sobrepõe a tela de fim de jogo
        screen.draw.filled_rect(Rect(WIDTH // 2 - 200, HEIGHT // 2 - 80, 400, 160), (20, 20, 30))
        screen.draw.text("FIM DE JOGO", center=(WIDTH // 2, HEIGHT // 2 - 20), fontsize=48, color=(210, 60, 60))
        screen.draw.text(f"Pontuação Final: {player.score}", center=(WIDTH // 2, HEIGHT // 2 + 20), fontsize=28, color=COLOR_TEXT)
        screen.draw.text("Pressione Start no menu para tentar novamente", center=(WIDTH // 2, HEIGHT // 2 + 56), fontsize=16, color=(160, 160, 160))
        return

    # modo == "playing" (jogando)
    draw_map()

    # Desenha os itens
    for it in items:
        if not it.collected:
            it.draw()

    # Desenha os inimigos
    for e in enemies:
        e.draw(level_time)

    # Desenha o jogador
    player.draw(level_time)

    # HUD
    draw_hud()


# ----------------------------
# CARREGAR / PROTEGER ÁUDIO
# ----------------------------
# Inicializa o sistema de áudio do Pygame Zero
def init_audio():
    """Inicializa o sistema de áudio e verifica se os arquivos estão disponíveis."""
    global audio_initialized
    try:
        # Força a inicialização do mixer do pygame
        import pygame
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        audio_initialized = True
        print("Sistema de áudio inicializado com sucesso")
    except Exception as e:
        print(f"Erro ao inicializar áudio: {e}")
        audio_initialized = False

# Verifica se o arquivo de música existe (sem depender de módulos externos)
def music_resource_exists(name: str) -> bool:
    try:
        # PgZero espera um arquivo .ogg em music/<name>.ogg
        with open(f"music/{name}.ogg", "rb") as f:
            # lê alguns bytes para garantir não ser vazio
            _ = f.read(4)
            return True
    except Exception:
        return False

def music_mp3_exists(name: str) -> bool:
    try:
        with open(f"music/{name}.mp3", "rb") as f:
            _ = f.read(4)
            return True
    except Exception:
        return False

def ogg_header_is_valid(name: str) -> bool:
    """Retorna True se o arquivo music/<name>.ogg começar com 'OggS'."""
    try:
        with open(f"music/{name}.ogg", "rb") as f:
            sig = f.read(4)
            return sig == b"OggS"
    except Exception:
        return False

# Tenta carregar os sons necessários; se faltarem, cria placeholders silenciosos para evitar erros de execução.
def safe_load_sound(name):
    try:
        if audio_initialized:
            return sounds[name]
        else:
            return None
    except Exception as e:
        print(f"Erro ao carregar som {name}: {e}")
        # sounds[...] levanta um KeyError se estiver faltando; cria um objeto fictício com o método play()
        class Dummy:
            def play(self, *a, **k): pass
        return Dummy()

def safe_play_sound(sound_name):
    """Reproduz um som de forma segura, com tratamento de erros."""
    if not music_enabled or not audio_initialized:
        return
    try:
        snd = getattr(sounds, sound_name, None)
        if snd is None:
            # Recurso de som ausente; ignore silenciosamente
            return
        snd.play()
    except Exception as e:
        print(f"Erro ao reproduzir som {sound_name}: {e}")

def safe_play_music(music_name):
    """Reproduz música de forma segura, com tratamento de erros."""
    if not music_enabled or not audio_initialized:
        return
    # Primeiro tenta OGG via PgZero quando cabeçalho parece válido
    if music_resource_exists(music_name) and ogg_header_is_valid(music_name):
        try:
            music.play(music_name)
            music.set_volume(0.6)
            return
        except Exception as e:
            print(f"Erro ao reproduzir música {music_name} (OGG): {e}")
    # Caso exista .ogg mas não seja OGG de verdade (ex: MP3 renomeado), tenta carregá-lo direto
    if music_resource_exists(music_name) and not ogg_header_is_valid(music_name):
        try:
            import pygame
            pygame.mixer.music.load(f"music/{music_name}.ogg")
            pygame.mixer.music.set_volume(0.6)
            pygame.mixer.music.play(-1)
            print(f"Reproduzindo música via mixer: music/{music_name}.ogg (provável MP3 renomeado)")
            return
        except Exception as e:
            print(f"Erro ao reproduzir música {music_name} (mixer .ogg): {e}")
    # Fallback: tenta MP3 via pygame.mixer
    if music_mp3_exists(music_name):
        try:
            import pygame
            pygame.mixer.music.load(f"music/{music_name}.mp3")
            pygame.mixer.music.set_volume(0.6)
            pygame.mixer.music.play(-1)
            print(f"Reproduzindo música via MP3: music/{music_name}.mp3")
            return
        except Exception as e:
            print(f"Erro ao reproduzir música {music_name} (MP3): {e}")
    # Caso nenhum formato esteja disponível
    print(f"Arquivo de música não encontrado/compatível: music/{music_name}.ogg ou .mp3 — a música será ignorada.")

def safe_stop_music():
    """Para a música de forma segura."""
    if not audio_initialized:
        return
    try:
        music.stop()
        # Também garante parada do mixer.music
        import pygame
        pygame.mixer.music.stop()
    except Exception as e:
        print(f"Erro ao parar música: {e}")

# Variável global para controlar se o áudio foi inicializado
audio_initialized = False

# Inicializa o áudio na importação
init_audio()

# Garante que os sons existam na tabela de recursos; se o usuário não os adicionou, o objeto fictício evitará falhas
try:
    # Acessa as entradas de som para levantar erro se estiverem faltando
    if audio_initialized:
        # Usa getattr para evitar erro de subscript e apenas validar presença
        _hit = getattr(sounds, SOUND_HIT, None)
        _pickup = getattr(sounds, SOUND_PICKUP, None)
        _click = getattr(sounds, SOUND_CLICK, None)
        if _hit and _pickup and _click:
            print("Todos os arquivos de som carregados com sucesso")
except Exception as e:
    print(f"Alguns arquivos de som não foram encontrados: {e}")
    # Se não estiverem presentes, cria chaves fictícias (o 'sounds' do PgZero é um mapeamento somente leitura, então apenas protegemos com o carregador seguro)
    pass

# Mensagem informativa sobre música ausente
if not music_resource_exists(BGM_FILENAME) and not music_mp3_exists(BGM_FILENAME):
    print(f"Arquivo de música não encontrado: music/{BGM_FILENAME}.ogg/.mp3 — a música será ignorada.")

# ----------------------------
# CONFIGURAÇÃO INICIAL DO TEXTO DO MENU
# ----------------------------
btn_music.text = "Music: On" if music_enabled else "Music: Off"

# ----------------------------
# Pequenos polimentos adicionais:
# mostra FPS no modo de depuração se necessário (comentado)
# ----------------------------
#def draw_fps():
#    screen.draw.text(f"FPS: {int(1 / max(1e-6, clock.get_time() / 1000.0))}", (WIDTH-80, HEIGHT-40), fontsize=14, color=(120,120,120))

# ----------------------------
# FIM DO CÓDIGO
# ----------------------------