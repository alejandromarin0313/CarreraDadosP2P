# game.py
import pygame
import random
import requests
import string
import socket
import subprocess
import os
import sys
import textwrap
import json
from network import P2PNode
from config import PORT, RELAY_SERVER, TARGET_SCORE

pygame.init()
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Carrera de Dados P2P")
font = pygame.font.SysFont(None, 24)

# ------------------------- FUNCIONES GRÁFICAS ------------------------- #

def draw_text(text, x, y, color=(255, 255, 255)):
    label = font.render(text, True, color)
    screen.blit(label, (x, y))

def draw_menu(name_text, code_text, active_name, active_code, is_join, is_host_selected):
    screen.fill((20, 20, 20))
    draw_text("Tu nombre:", 180, 85)
    draw_input_box("", name_text, pygame.Rect(300, 80, 200, 30), active_name)

    draw_text("Modo:", 180, 135)
    draw_button("Crear sala", pygame.Rect(300, 130, 120, 35), is_host_selected)
    draw_button("Unirse", pygame.Rect(440, 130, 120, 35), is_join)

    if is_join:
        draw_text("Código de sala:", 180, 185)
        draw_input_box("", code_text, pygame.Rect(300, 180, 200, 30), active_code)

    pygame.draw.rect(screen, (80, 180, 80), (340, 250, 120, 40))
    pygame.draw.rect(screen, (255, 255, 255), (340, 250, 120, 40), 2)
    draw_text("Continuar", 365, 260)
    pygame.display.flip()

def draw_input_box(label, text, rect, active):
    pygame.draw.rect(screen, (255, 255, 255) if active else (180, 180, 180), rect, 2)
    draw_text(label, rect.x - 100, rect.y + 5)
    draw_text(text + "_", rect.x + 5, rect.y + 5)

def draw_button(text, rect, selected):
    color = (80, 80, 200) if selected else (100, 100, 100)
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, (255, 255, 255), rect, 2)
    draw_text(text, rect.x + 10, rect.y + 8)

def wrap_chat_message(message, max_chars=28):
    return textwrap.wrap(message, width=max_chars)

def draw(players, current_turn, messages, winner, chat_messages, chat_input, lobby=False, codigo_sala=None, show_start_button=False):
    screen.fill((30, 30, 30))

    if lobby and codigo_sala:
        draw_text(f"Código de sala: {codigo_sala}", 50, 10)

    for i, (name, score) in enumerate(players.items()):
        color = (255, 255, 0) if list(players.keys())[current_turn] == name and not lobby else (200, 200, 200)
        screen.blit(font.render(f"{name}: {score} puntos", True, color), (50, 40 + i * 40))

    y = 240
    for msg in messages[-3:]:
        msg_text = font.render(msg, True, (180, 180, 180))
        screen.blit(msg_text, (50, y))
        y += 25

    pygame.draw.rect(screen, (50, 50, 50), (600, 20, 180, 360))
    pygame.draw.rect(screen, (200, 200, 200), (600, 20, 180, 360), 2)
    screen.blit(font.render("Chat", True, (255, 255, 255)), (670, 25))

    y = 50
    last_lines = []
    for line in chat_messages[-10:]:
        wrapped = wrap_chat_message(line)
        last_lines.extend(wrapped)

    for line in last_lines[-12:]:
        screen.blit(font.render(line, True, (220, 220, 220)), (610, y))
        y += 22

    input_box = font.render(chat_input + "_", True, (255, 255, 255))
    screen.blit(input_box, (610, 340))

    if winner:
        win_text = font.render(f"¡{winner} ha ganado!", True, (0, 255, 0))
        screen.blit(win_text, (50, 350))

    if show_start_button:
        pygame.draw.rect(screen, (80, 180, 80), (300, 320, 200, 40))
        pygame.draw.rect(screen, (255, 255, 255), (300, 320, 200, 40), 2)
        draw_text("Iniciar partida", 335, 330)

    pygame.display.flip()

# ------------------------- FUNCIONES DE JUEGO ------------------------- #

def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def obtener_ip_local():
    return socket.gethostbyname(socket.gethostname())

def main():
    state = "menu"
    name_text = ""
    code_text = ""
    active_name = False
    active_code = False
    is_join = False
    is_host_selected = True

    players = {}
    all_names = []
    messages = []
    chat_messages = []
    chat_input = ""
    current_turn = 0
    winner = None
    node = None
    name = ""
    codigo_sala = None
    game_started = False
    clock = pygame.time.Clock()

    while True:
        clock.tick(30)
        screen.fill((0, 0, 0))

        if state == "menu":
            draw_menu(name_text, code_text, active_name, active_code, is_join, is_host_selected)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    active_name = pygame.Rect(300, 80, 200, 30).collidepoint(mx, my)
                    active_code = pygame.Rect(300, 180, 200, 30).collidepoint(mx, my)
                    if pygame.Rect(300, 130, 120, 35).collidepoint(mx, my):
                        is_host_selected = True
                        is_join = False
                    if pygame.Rect(440, 130, 120, 35).collidepoint(mx, my):
                        is_join = True
                        is_host_selected = False
                    if pygame.Rect(340, 250, 120, 40).collidepoint(mx, my):
                        name = name_text.strip() if name_text else "Jugador"
                        if is_host_selected:
                            try:
                                subprocess.Popen([sys.executable, "relay_server.py"], cwd=os.getcwd())
                            except Exception as e:
                                print("⚠️ Error iniciando el servidor Flask:", e)

                            codigo_sala = generar_codigo()
                            ip = obtener_ip_local()
                            try:
                                requests.post(f"{RELAY_SERVER}/register", json={"codigo": codigo_sala, "ip": ip})
                            except Exception as e:
                                print("⚠️ Error registrando la sala en el servidor:", e)

                            node = P2PNode(name, True, ip)
                            node.start()
                            players = {name: 0}
                            state = "lobby"
                        else:
                            r = requests.get(f"{RELAY_SERVER}/sala/{code_text.strip().upper()}")
                            if r.status_code == 200:
                                ip = r.json()["ip"]
                                node = P2PNode(name, False, ip)
                                node.start()
                                players = {}
                                state = "lobby"

                if event.type == pygame.KEYDOWN:
                    if active_name:
                        if event.key == pygame.K_BACKSPACE:
                            name_text = name_text[:-1]
                        else:
                            name_text += event.unicode
                    elif active_code:
                        if event.key == pygame.K_BACKSPACE:
                            code_text = code_text[:-1]
                        else:
                            code_text += event.unicode

        elif state == "lobby":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        chat_input = chat_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if chat_input.strip():
                            chat_messages.append(name + ": " + chat_input)
                            node.send_to_all({"type": "chat", "from": name, "text": chat_input})
                            print(f"[DEBUG] Enviado: {chat_input}")
                            chat_input = ""
                    else:
                        if len(chat_input) < 30:
                            chat_input += event.unicode

                if node.is_host:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if pygame.Rect(300, 320, 200, 40).collidepoint(event.pos):
                            if len(node.peers) >= 0:
                                for i, conn in enumerate(node.peers):
                                    conn.send(json.dumps({"type": "assign_name", "name": f"Jugador{i+2}"}).encode())
                                    players[f"Jugador{i+2}"] = 0
                                all_names = list(players.keys())
                                state = "game"
                                game_started = True

            msgs = node.get_messages()
            for m in msgs:
                print("[DEBUG] Recibido:", m)
                if m["type"] == "assign_name":
                    name = m["name"]
                    players[name] = 0
                    all_names = [name]
                    state = "game"
                elif m["type"] == "chat":
                    chat_messages.append(m["from"] + ": " + m["text"])

            show_start_button = node.is_host and len(node.peers) >= 0 and not game_started
            draw(players, 0, ["Esperando jugadores..."], None, chat_messages, chat_input, lobby=True, codigo_sala=codigo_sala, show_start_button=show_start_button)

        elif state == "game":
            msgs = node.get_messages()
            for msg in msgs:
                print("[DEBUG] Recibido:", msg)
                if msg["type"] == "roll":
                    p = msg["player"]
                    roll = msg["value"]
                    players[p] += roll
                    messages.append(f"{p} tiró un {roll}")
                    if players[p] >= TARGET_SCORE:
                        winner = p
                    current_turn = (current_turn + 1) % len(players)
                elif msg["type"] == "chat":
                    chat_messages.append(msg["from"] + ": " + msg["text"])

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if winner:
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        chat_input = chat_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if chat_input.strip():
                            chat_messages.append(name + ": " + chat_input)
                            node.send_to_all({"type": "chat", "from": name, "text": chat_input})
                            print(f"[DEBUG] Enviado: {chat_input}")
                            chat_input = ""
                    elif event.key == pygame.K_SPACE:
                        if list(players.keys())[current_turn] == name:
                            roll = random.randint(1, 6)
                            players[name] += roll
                            messages.append(f"Tiraste un {roll}")
                            node.send_to_all({"type": "roll", "player": name, "value": roll})
                            if players[name] >= TARGET_SCORE:
                                winner = name
                            current_turn = (current_turn + 1) % len(players)
                    else:
                        if len(chat_input) < 30:
                            chat_input += event.unicode

            draw(players, current_turn, messages, winner, chat_messages, chat_input)

if __name__ == "__main__":
    main()
