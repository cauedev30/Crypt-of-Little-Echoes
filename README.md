# Crypt of Little Echoes

Um roguelike/top‑down simples feito com [Pygame Zero](https://pygame-zero.readthedocs.io/).

## Como jogar
- Setas ou WASD para mover
- M para alternar a música
- ESC para voltar ao menu
- Colete os itens, evite os inimigos. Ao coletar todos, aparecem mais inimigos e novos itens.

## Requisitos
- Python 3.9+ (testado em 3.13)
- Pygame Zero e Pygame

Instalação rápida (Windows):
```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

## Executando
- Método recomendado (garante UTF‑8 no Windows):
```powershell
py -X utf8 -m pgzero main.py
```
- Ou usando o executável do pgzero (se no PATH):
```powershell
pgzrun main.py
```

## Áudio
Coloque seus arquivos em:
- `music/bg_loop.ogg` (OGG Vorbis válido) ou `music/bg_loop.mp3` (fallback via mixer)
- `sounds/hit.wav`, `sounds/pickup.wav`, `sounds/menu_click.wav`

Observação: O código inclui tratamento para quando `bg_loop.ogg` for na verdade um MP3 renomeado; nesse caso ele tenta usar `pygame.mixer.music` e também aceita `music/bg_loop.mp3`.

## Estrutura
- `main.py`: jogo completo (player, inimigos, itens, menu, HUD, áudio com fallbacks)
- `requirements.txt`: dependências
- `.gitignore`: ignora assets do usuário e virtual env
- `music/.gitkeep` e `sounds/.gitkeep`: placeholders das pastas de assets

## Publicando no GitHub
1. Crie um repositório no GitHub (público ou privado).
2. Inicialize o git na pasta do projeto e faça o primeiro commit:
```powershell
git init
git add .
git commit -m "Initial commit: Crypt of Little Echoes"
```
3. Vincule ao repositório remoto e envie:
```powershell
git branch -M main
git remote add origin https://github.com/<seu-usuario>/<seu-repo>.git
git push -u origin main
```

## Licença
Adicione uma licença se desejar (por exemplo, MIT). Crie um arquivo `LICENSE` com o texto da licença.
