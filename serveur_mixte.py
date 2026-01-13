import socket
import threading
from threading import Thread, RLock

# ==============================================================================
# CONFIGURATION DU SERVEUR CENTRALISÉ
# ==============================================================================
TCP_PORT = 9000  # Port d'écoute pour les logs critiques (fiabilité)
UDP_PORT = 9001  # Port d'écoute pour les notifications rapides (vitesse)
HOST = ""        # "" signifie que le serveur écoute sur toutes les interfaces réseau disponibles

# Verrou pour synchroniser l'affichage dans la console 
# Empêche que les messages des différents threads ne se mélangent à l'écran
verrou_affichage = RLock() 

def afficher_safe(msg):
    """
    Affiche un message dans la console de manière thread-safe.
    Utilise un verrou (RLock) pour garantir qu'un seul thread écrit à la fois.
    
    Args:
        msg (str): Le message à afficher.
    """
    with verrou_affichage: 
        print(msg)

# ==============================================================================
# PARTIE 1 : GESTIONNAIRE CLIENT TCP (POUR CHAQUE CONNEXION)
# ==============================================================================
class TCPClientHandler(Thread): 
    """
    Thread dédié à la gestion d'une unique connexion client TCP.
    Permet au serveur de traiter plusieurs clients simultanément sans bloquer.
    """
    
    def __init__(self, sock, client_addr):
        """
        Initialise le gestionnaire.
        
        Args:
            sock (socket): Le socket connecté au client spécifique.
            client_addr (tuple): L'adresse (IP, Port) du client.
        """
        Thread.__init__(self) 
        self.sock = sock
        self.client_addr = client_addr

    def run(self): 
        """
        Logique principale du thread :
        1. Reçoit le message du client.
        2. Affiche le log.
        3. Envoie un accusé de réception.
        """
        try:
            afficher_safe(f"[TCP] Connexion de {self.client_addr}")
            
            # Réception des données (taille du buffer : 1024 octets)
            data = self.sock.recv(1024)
            message = data.decode('utf-8')
            afficher_safe(f"[TCP] Reçu : {message}")
            
            # Envoi de la réponse (Ack) pour confirmer la bonne réception
            reponse = "Bien reçu par le serveur TCP central"
            self.sock.send(reponse.encode('utf-8'))
            
        except Exception as e:
            afficher_safe(f"[TCP] Erreur : {e}")
        finally:
            # Fermeture propre de la connexion quoi qu'il arrive
            self.sock.close()

# ==============================================================================
# PARTIE 2 : SERVEUR TCP PRINCIPAL (LOGS CRITIQUES)
# ==============================================================================
class ServeurTCP(Thread):
    """
    Serveur TCP principal qui écoute en boucle les nouvelles connexions.
    Délègue le traitement de chaque client à un thread TCPClientHandler.
    """
    
    def __init__(self):
        """Initialise le socket d'écoute TCP."""
        Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.sock.bind((HOST, TCP_PORT)) 

    def run(self):
        """
        Boucle principale du serveur TCP :
        Accepte les connexions entrantes et lance les threads de gestion.
        """
        self.sock.listen(5) # File d'attente de 5 connexions max
        afficher_safe(f"🚀 Serveur TCP en écoute sur le port {TCP_PORT}...")
        
        while True:
            try:
                # Bloque jusqu'à ce qu'un client se connecte
                conn, addr = self.sock.accept() 
                
                # Création et démarrage du thread dédié au client
                handler = TCPClientHandler(conn, addr)
                handler.start() 
            except Exception as e:
                afficher_safe(f"Erreur accept TCP: {e}")

# ==============================================================================
# PARTIE 3 : SERVEUR UDP (NOTIFICATIONS RAPIDES)
# ==============================================================================
class ServeurUDP(Thread):
    """
    Serveur UDP pour la réception rapide de messages sans connexion.
    Traite les messages séquentiellement (UDP est sans état et très rapide).
    """
    
    def __init__(self):
        """Initialise le socket d'écoute UDP."""
        Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.sock.bind((HOST, UDP_PORT)) 

    def run(self):
        """
        Boucle principale du serveur UDP :
        Reçoit et affiche les paquets entrants.
        """
        afficher_safe(f"📡 Serveur UDP en écoute sur le port {UDP_PORT}...")
        
        while True: 
            try:
                # Réception du datagramme (Message + Adresse Expéditeur)
                data, addr = self.sock.recvfrom(1024)
                msg = data.decode('utf-8')
                
                afficher_safe(f"[UDP] Log rapide reçu de {addr} : {msg}")
                
                # Note : Pas de réponse envoyée ici pour maximiser la vitesse (Fire & Forget)
            except Exception as e:
                afficher_safe(f"Erreur UDP: {e}")

# ==============================================================================
# LANCEMENT DES SERVICES
# ==============================================================================
if __name__ == "__main__":
    print("--- Démarrage du Système Centralisé ---")
    
    # Instanciation des deux serveurs
    thread_tcp = ServeurTCP()
    thread_udp = ServeurUDP()
    
    # Démarrage des threads (exécution parallèle)
    thread_tcp.start()
    thread_udp.start()
    
    # Maintien du programme principal en vie tant que les serveurs tournent
    thread_tcp.join()
    thread_udp.join()
