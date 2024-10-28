import time
import logging
from plyer import notification
from multiprocessing import Process
import os
import sys

# Configuração do logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_notification(message: str, title: str, timeout: int = 10) -> None:
    """Função que envia a notificação na tela"""
    notification.notify(
        title=title,
        message=message,
        app_name="Bet Notification",
        timeout=timeout  # Duração da notificação em segundos
    )

def play_sound(sound_file: str) -> None:
    """Função que emite um som ao final do temporizador"""
    with open(os.devnull, 'w') as f:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = f
        sys.stderr = f
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    # Aguarda até o som terminar de tocar
    while pygame.mixer.music.get_busy():
        time.sleep(1)

def run_timer(duration: int, message: str, title: str, timeout: int) -> None:
    """Função que roda o timer em um processo separado"""
    logging.info(f"Timer para iniciado...")
    time.sleep(duration * 60)

    # Envia a notificação e toca o som
    send_notification(message, title, timeout)
    play_sound("/home/marcos/Música/corneta.mp3")

def start_timer(duration: int, message: str, title: str, timeout: int) -> None:
    """Inicia um timer em um processo separado"""
    try:
        p = Process(target=run_timer, args=(duration, message, title, timeout))
        p.start()
    except KeyboardInterrupt:
        print("Saida solicitada pelo usuário.")

