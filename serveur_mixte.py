import socket
import threading
from threading import Thread, RLock

# Configuration
TCP_PORT = 9000
UDP_PORT = 9001
HOST = ""  # Écoute sur toutes les interfaces

# Verrou pour synchroniser l'affichage dans la console 
verrou_affichage = RLock() 

def afficher_safe(msg):
    """Affiche un message de manière thread-safe"""
    with verrou_affichage: 
        print(msg)

# --- PARTIE 1 : GESTIONNAIRE CLIENT TCP (Slide 44) ---
class TCPClientHandler(Thread): 
    def __init__(self, sock, client_addr):
        Thread.__init__(self) 
        self.sock = sock
        self.client_addr = client_addr

    def run(self): 
        try:
            afficher_safe(f"[TCP] Connexion de {self.client_addr}")
            
            # On écoute ce que le client (Flask) a à dire
            data = self.sock.recv(1024)
            message = data.decode('utf-8')
            afficher_safe(f"[TCP] Reçu : {message}")
            
            # [cite_start]On répond (Protocole TCP mode connecté) 
            reponse = "Bien reçu par le serveur TCP central"
            self.sock.send(reponse.encode('utf-8'))
            
        except Exception as e:
            afficher_safe(f"[TCP] Erreur : {e}")
        finally:
            self.sock.close()

# --- PARTIE 2 : SERVEUR TCP PRINCIPAL (Slide 44 adapté) ---
class ServeurTCP(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.sock.bind((HOST, TCP_PORT)) 

    def run(self):
        self.sock.listen(5) 
        afficher_safe(f"🚀 Serveur TCP en écoute sur le port {TCP_PORT}...")
        
        while True: # [cite: 884]
            try:
                # Accepte la connexion et lance un thread dédié 
                conn, addr = self.sock.accept() 
                handler = TCPClientHandler(conn, addr)
                handler.start() 
            except Exception as e:
                afficher_safe(f"Erreur accept TCP: {e}")

# --- PARTIE 3 : SERVEUR UDP (Slide 45 adapté en Thread) ---
class ServeurUDP(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.sock.bind((HOST, UDP_PORT)) 

    def run(self):
        afficher_safe(f"📡 Serveur UDP en écoute sur le port {UDP_PORT}...")
        
        while True: 
            try:
                # Réception du datagramme 
                data, addr = self.sock.recvfrom(1024)
                msg = data.decode('utf-8')
                
                afficher_safe(f"[UDP] Log rapide reçu de {addr} : {msg}")
                
                # Optionnel : Réponse UDP
                # self.sock.sendto(b"Ack", addr)
            except Exception as e:
                afficher_safe(f"Erreur UDP: {e}")

# --- LANCEMENT ---
if __name__ == "__main__":
    print("--- Démarrage du Système Centralisé (Cours R309) ---")
    
    # On lance les deux serveurs en parallèle grâce aux Threads
    thread_tcp = ServeurTCP()
    thread_udp = ServeurUDP()
    
    thread_tcp.start()
    thread_udp.start()
    
    # On attend qu'ils finissent (jamais, car boucle infinie)
    thread_tcp.join()
    thread_udp.join()