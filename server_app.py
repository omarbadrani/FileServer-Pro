import sys
import os
import socket
import threading
import json
import csv
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog


# ============================================
# CONFIGURATION CENTRALISÉE
# ============================================
class Config:
    """Configuration centralisée de l'application"""
    # Réseau
    SERVER_IP = "192.168.1.210"
    SERVER_PORT = 9999

    # Stockage
    BASE_PATH = Path("C:/ServeurData")
    LOGS_PATH = Path("C:/ServeurData/.logs")
    AUTH_FILE = Path("C:/ServeurData/.logs/users.json")

    # Interface
    APP_NAME = "Serveur de Transfert Pro"
    APP_VERSION = "v3.1.0"
    WINDOW_SIZE = "1400x900"
    WINDOW_MIN_SIZE = (1200, 700)
    LOGIN_SIZE = "450x550"

    # Thème
    COLOR_PRIMARY = "#1a237e"
    COLOR_PRIMARY_LIGHT = "#3949ab"
    COLOR_SUCCESS = "#4CAF50"
    COLOR_DANGER = "#f44336"
    COLOR_WARNING = "#FF9800"
    COLOR_INFO = "#2196F3"
    COLOR_BG_LIGHT = "#f5f6fa"
    COLOR_BG_WHITE = "#ffffff"
    COLOR_TEXT_DARK = "#2c3e50"
    COLOR_TEXT_LIGHT = "#757575"
    COLOR_TEXT_WHITE = "#ffffff"

    # Dossiers de destination par défaut
    DEFAULT_FOLDERS = [
        "Production",
        "Administration",
        "Commercial",
        "RH",
        "Comptabilité"
    ]

    DEFAULT_SUBFOLDERS = {
        "Production": ["Atelier 1", "Atelier 2", "Atelier 3"],
        "Administration": ["Bureau", "Direction", "Archives"],
        "Commercial": ["Ventes", "Marketing", "Export"],
        "RH": ["Recrutement", "Formation", "Paie"],
        "Comptabilité": ["Factures", "Rapports", "Budget"]
    }

    # Rôles
    ROLE_ADMIN = "admin"
    ROLE_USER = "user"


# ============================================
# GESTIONNAIRE D'AUTHENTIFICATION
# ============================================
class AuthManager:
    """Gère l'authentification des utilisateurs avec mots de passe hashés"""

    def __init__(self):
        self.users = {}
        Config.AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.load_users()
        self._create_default_admin()

    def _create_default_admin(self):
        """Crée le compte admin par défaut s'il n'existe pas"""
        if "admin" not in self.users:
            self.create_user("admin", "admin123", "Administrateur", Config.ROLE_ADMIN)
            print("✅ Compte admin par défaut créé (admin / admin123)")

    def _hash_password(self, password, salt=None):
        """Hash un mot de passe avec SHA-256 + salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        salted = salt + password
        hash_value = hashlib.sha256(salted.encode()).hexdigest()
        return salt, hash_value

    def load_users(self):
        """Charge les utilisateurs depuis le fichier JSON"""
        try:
            if Config.AUTH_FILE.exists():
                with open(Config.AUTH_FILE, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
        except Exception as e:
            print(f"Erreur chargement utilisateurs: {e}")
            self.users = {}

    def save_users(self):
        """Sauvegarde les utilisateurs dans le fichier JSON"""
        try:
            with open(Config.AUTH_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde utilisateurs: {e}")
            return False

    def create_user(self, username, password, full_name, role=Config.ROLE_USER):
        """Crée un nouvel utilisateur"""
        if username in self.users:
            return False, "Cet utilisateur existe déjà"
        if len(password) < 4:
            return False, "Le mot de passe doit contenir au moins 4 caractères"

        salt, hash_value = self._hash_password(password)
        self.users[username] = {
            'username': username,
            'full_name': full_name,
            'role': role,
            'salt': salt,
            'password_hash': hash_value,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        self.save_users()
        return True, "Utilisateur créé avec succès"

    def authenticate(self, username, password):
        """Authentifie un utilisateur"""
        if username not in self.users:
            return False, "Utilisateur inconnu"

        user = self.users[username]
        salt = user['salt']
        _, hash_value = self._hash_password(password, salt)

        if hash_value != user['password_hash']:
            return False, "Mot de passe incorrect"

        # Mise à jour de la dernière connexion
        self.users[username]['last_login'] = datetime.now().isoformat()
        self.save_users()
        return True, user

    def change_password(self, username, new_password):
        """Change le mot de passe d'un utilisateur"""
        if username not in self.users:
            return False, "Utilisateur inconnu"
        if len(new_password) < 4:
            return False, "Le mot de passe doit contenir au moins 4 caractères"

        salt, hash_value = self._hash_password(new_password)
        self.users[username]['salt'] = salt
        self.users[username]['password_hash'] = hash_value
        self.save_users()
        return True, "Mot de passe modifié"

    def delete_user(self, username):
        """Supprime un utilisateur"""
        if username == "admin":
            return False, "Impossible de supprimer le compte admin"
        if username in self.users:
            del self.users[username]
            self.save_users()
            return True, "Utilisateur supprimé"
        return False, "Utilisateur inconnu"

    def get_all_users(self):
        """Retourne la liste des utilisateurs (sans les données sensibles)"""
        result = []
        for username, data in self.users.items():
            result.append({
                'username': data['username'],
                'full_name': data['full_name'],
                'role': data['role'],
                'created_at': data['created_at'],
                'last_login': data['last_login']
            })
        return result


# ============================================
# FENÊTRE DE LOGIN
# ============================================
class LoginWindow(ctk.CTkToplevel):
    """Fenêtre de connexion"""

    def __init__(self, auth_manager, on_success):
        super().__init__()
        self.auth_manager = auth_manager
        self.on_success = on_success
        self.authenticated_user = None

        self.title("Connexion - Serveur de Transfert Pro")
        self.geometry(Config.LOGIN_SIZE)
        self.resizable(False, False)
        self.configure(fg_color=Config.COLOR_PRIMARY)

        # Centrer la fenêtre
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (550 // 2)
        self.geometry(f"450x550+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.create_login_ui()

        # Rendre modale
        self.transient()
        self.grab_set()
        self.focus_force()

    def create_login_ui(self):
        """Crée l'interface de connexion"""
        # Carte principale
        card = ctk.CTkFrame(self, fg_color=Config.COLOR_BG_WHITE, corner_radius=15)
        card.pack(expand=True, fill="both", padx=30, pady=30)

        # Logo / Titre
        title_frame = ctk.CTkFrame(card, fg_color="transparent")
        title_frame.pack(fill="x", pady=(30, 10))

        ctk.CTkLabel(title_frame, text="🔐", font=ctk.CTkFont(size=48)).pack()
        ctk.CTkLabel(title_frame, text="Connexion",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=Config.COLOR_TEXT_DARK).pack(pady=(10, 5))
        ctk.CTkLabel(title_frame, text="Serveur de Transfert Pro",
                     font=ctk.CTkFont(size=13),
                     text_color=Config.COLOR_TEXT_LIGHT).pack()

        # Formulaire
        form_frame = ctk.CTkFrame(card, fg_color="transparent")
        form_frame.pack(fill="x", padx=40, pady=20)

        # Nom d'utilisateur
        ctk.CTkLabel(form_frame, text="👤 Nom d'utilisateur",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Config.COLOR_TEXT_DARK,
                     anchor="w").pack(fill="x", pady=(10, 5))
        self.username_entry = ctk.CTkEntry(form_frame, height=40,
                                           placeholder_text="Entrez votre identifiant",
                                           font=ctk.CTkFont(size=13))
        self.username_entry.pack(fill="x", pady=(0, 15))

        # Mot de passe
        ctk.CTkLabel(form_frame, text="🔑 Mot de passe",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Config.COLOR_TEXT_DARK,
                     anchor="w").pack(fill="x", pady=(10, 5))
        self.password_entry = ctk.CTkEntry(form_frame, height=40,
                                           placeholder_text="Entrez votre mot de passe",
                                           show="•", font=ctk.CTkFont(size=13))
        self.password_entry.pack(fill="x", pady=(0, 10))
        self.password_entry.bind("<Return>", lambda e: self.login())

        # Message d'erreur
        self.error_label = ctk.CTkLabel(form_frame, text="",
                                        font=ctk.CTkFont(size=11),
                                        text_color=Config.COLOR_DANGER)
        self.error_label.pack(fill="x", pady=5)

        # Bouton de connexion
        self.login_btn = ctk.CTkButton(card, text="Se connecter",
                                       height=45,
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       fg_color=Config.COLOR_PRIMARY,
                                       hover_color=Config.COLOR_PRIMARY_LIGHT,
                                       command=self.login)
        self.login_btn.pack(fill="x", padx=40, pady=(10, 20))

        # Info
        ctk.CTkLabel(card, text="Compte par défaut : admin / admin123",
                     font=ctk.CTkFont(size=10),
                     text_color=Config.COLOR_TEXT_LIGHT).pack(pady=(0, 20))

        # Focus sur le champ username
        self.username_entry.focus_set()

    def login(self):
        """Tente de connecter l'utilisateur"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.error_label.configure(text="⚠️ Veuillez remplir tous les champs")
            return

        success, result = self.auth_manager.authenticate(username, password)

        if success:
            self.authenticated_user = result
            self.on_success(result)
            self.destroy()
        else:
            self.error_label.configure(text=f"❌ {result}")
            self.password_entry.delete(0, "end")
            self.password_entry.focus_set()
            # Effet de shake
            self.shake()

    def shake(self):
        """Animation de secousse pour indiquer une erreur"""
        x = self.winfo_x()
        for offset in [10, -10, 8, -8, 5, -5, 0]:
            self.geometry(f"+{x + offset}+{self.winfo_y()}")
            self.update()
            self.after(20, lambda: None)

    def on_close(self):
        """Fermeture de la fenêtre"""
        self.destroy()
        sys.exit(0)


# ============================================
# GESTIONNAIRE DE CONNEXIONS ET TRANSFERTS
# ============================================
class ConnectionManager:
    """Gère le suivi des PC connectés et leur activité avec historique permanent"""

    def __init__(self):
        self.connections = {}
        self.transfer_history = []
        self.lock = threading.Lock()

        # Créer le dossier de logs
        Config.LOGS_PATH.mkdir(parents=True, exist_ok=True)

        # Charger l'historique au démarrage
        self.load_all_history()

    def load_all_history(self):
        """Charge l'historique complet depuis les fichiers permanents"""
        try:
            # Charger les connexions
            connections_file = Config.LOGS_PATH / "connections_permanent.json"
            if connections_file.exists():
                try:
                    with open(connections_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for ip, info in data.items():
                            if 'first_seen' in info and isinstance(info['first_seen'], str):
                                info['first_seen'] = datetime.fromisoformat(info['first_seen'])
                            if 'last_seen' in info and isinstance(info['last_seen'], str):
                                info['last_seen'] = datetime.fromisoformat(info['last_seen'])

                            self.connections[ip] = info
                            self.connections[ip]['status'] = 'disconnected'
                            self.connections[ip]['current_transfers'] = 0
                except Exception as e:
                    print(f"Erreur chargement connexions: {e}")

            # Charger les transferts
            transfers_file = Config.LOGS_PATH / "transfers_permanent.json"
            if transfers_file.exists():
                try:
                    with open(transfers_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for transfer in data:
                            if 'timestamp' in transfer and isinstance(transfer['timestamp'], str):
                                transfer['timestamp'] = datetime.fromisoformat(transfer['timestamp'])
                            self.transfer_history.append(transfer)
                except Exception as e:
                    print(f"Erreur chargement transferts: {e}")

            # Trier par date
            self.transfer_history.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)

        except Exception as e:
            print(f"Erreur chargement historique: {e}")

    def add_connection(self, ip, hostname=None):
        """Ajoute ou met à jour une connexion"""
        with self.lock:
            if ip not in self.connections:
                self.connections[ip] = {
                    'ip': ip,
                    'hostname': hostname or ip,
                    'first_seen': datetime.now(),
                    'last_seen': datetime.now(),
                    'total_transfers': 0,
                    'total_size': 0,
                    'current_transfers': 0,
                    'status': 'connected'
                }
            else:
                self.connections[ip]['last_seen'] = datetime.now()
                self.connections[ip]['status'] = 'connected'
                self.connections[ip]['current_transfers'] += 1

            self.save_connections_log()

    def remove_connection(self, ip):
        """Marque une connexion comme déconnectée"""
        with self.lock:
            if ip in self.connections:
                self.connections[ip]['status'] = 'disconnected'
                self.connections[ip]['current_transfers'] = max(0, self.connections[ip]['current_transfers'] - 1)
                self.save_connections_log()

    def add_transfer(self, ip, user_name, file_name, file_size, folder_path):
        """Enregistre un transfert"""
        with self.lock:
            transfer = {
                'timestamp': datetime.now(),
                'ip': ip,
                'user_name': user_name,
                'file_name': file_name,
                'file_size': file_size,
                'folder_path': folder_path,
                'status': 'success'
            }
            self.transfer_history.insert(0, transfer)

            if ip in self.connections:
                self.connections[ip]['total_transfers'] += 1
                self.connections[ip]['total_size'] += file_size

            if len(self.transfer_history) > 5000:
                self.transfer_history = self.transfer_history[:5000]

            self.save_transfer_log(transfer)
            self.save_connections_log()

    def save_connections_log(self):
        """Sauvegarde permanente des connexions"""
        try:
            permanent_file = Config.LOGS_PATH / "connections_permanent.json"
            daily_file = Config.LOGS_PATH / f"connections_{datetime.now().strftime('%Y%m%d')}.json"

            data_to_save = {}
            for ip, info in self.connections.items():
                data_to_save[ip] = {
                    'ip': info['ip'],
                    'hostname': info['hostname'],
                    'first_seen': info['first_seen'].isoformat() if isinstance(info['first_seen'], datetime) else info[
                        'first_seen'],
                    'last_seen': info['last_seen'].isoformat() if isinstance(info['last_seen'], datetime) else info[
                        'last_seen'],
                    'total_transfers': info.get('total_transfers', 0),
                    'total_size': info.get('total_size', 0),
                    'status': info['status']
                }

            for file_path in [permanent_file, daily_file]:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde connexions: {e}")

    def save_transfer_log(self, transfer):
        """Sauvegarde permanente d'un transfert"""
        try:
            permanent_file = Config.LOGS_PATH / "transfers_permanent.json"
            daily_file = Config.LOGS_PATH / f"transfers_{datetime.now().strftime('%Y%m%d')}.json"

            transfer_data = {
                'timestamp': transfer['timestamp'].isoformat() if isinstance(transfer['timestamp'], datetime) else
                transfer['timestamp'],
                'ip': transfer['ip'],
                'user_name': transfer['user_name'],
                'file_name': transfer['file_name'],
                'file_size': transfer['file_size'],
                'folder_path': transfer['folder_path'],
                'status': transfer['status']
            }

            for file_path in [permanent_file, daily_file]:
                existing = []
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            existing = json.load(f)
                    except:
                        existing = []

                existing.append(transfer_data)

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(existing, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde transfert: {e}")

    def get_all_transfers(self):
        """Retourne TOUS les transferts depuis le fichier permanent"""
        all_transfers = []
        try:
            permanent_file = Config.LOGS_PATH / "transfers_permanent.json"
            if permanent_file.exists():
                with open(permanent_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for transfer in data:
                        if 'timestamp' in transfer and isinstance(transfer['timestamp'], str):
                            transfer['timestamp'] = datetime.fromisoformat(transfer['timestamp'])
                        all_transfers.append(transfer)

            all_transfers.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
        except Exception as e:
            print(f"Erreur chargement transferts: {e}")

        return all_transfers

    def get_connections_list(self):
        """Retourne la liste des connexions"""
        with self.lock:
            return list(self.connections.values())

    def get_recent_transfers(self, limit=50):
        """Retourne les transferts récents en mémoire"""
        with self.lock:
            return self.transfer_history[:limit]

    def search_transfers(self, search_term):
        """Recherche dans les transferts"""
        all_transfers = self.get_all_transfers()
        search_term = search_term.lower()

        results = []
        for transfer in all_transfers:
            if (search_term in transfer.get('file_name', '').lower() or
                    search_term in transfer.get('user_name', '').lower() or
                    search_term in transfer.get('ip', '').lower() or
                    search_term in transfer.get('folder_path', '').lower()):
                results.append(transfer)

        return results

    def clear_permanent_history(self):
        """Efface l'historique permanent"""
        try:
            for pattern in ["*_permanent.json", "*.json"]:
                for file in Config.LOGS_PATH.glob(pattern):
                    try:
                        file.unlink()
                    except:
                        pass

            self.transfer_history.clear()
            self.connections.clear()
            return True
        except Exception as e:
            print(f"Erreur effacement historique: {e}")
            return False


# ============================================
# THREAD DE RÉCEPTION
# ============================================
class ReceiveThread(threading.Thread):
    def __init__(self, callback_log, callback_progress, callback_file, callback_stats, conn_manager):
        super().__init__(daemon=True)
        self.callback_log = callback_log
        self.callback_progress = callback_progress
        self.callback_file = callback_file
        self.callback_stats = callback_stats
        self.conn_manager = conn_manager
        self.server_socket = None
        self.running = False
        self.stats = {
            'total_files': 0,
            'total_size': 0,
            'today_transfers': 0,
            'active_connections': 0
        }

    def run(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((Config.SERVER_IP, Config.SERVER_PORT))
            self.server_socket.listen(5)
            self.callback_log(f"✅ Serveur démarré sur {Config.SERVER_IP}:{Config.SERVER_PORT}", "success")
            self.callback_stats(self.stats, self.conn_manager)

            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    client_socket, address = self.server_socket.accept()

                    ip = address[0]
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except:
                        hostname = ip

                    self.conn_manager.add_connection(ip, hostname)
                    self.stats['active_connections'] = len(
                        [c for c in self.conn_manager.get_connections_list() if c['status'] == 'connected'])
                    self.callback_stats(self.stats, self.conn_manager)
                    self.callback_log(f"🔗 Nouvelle connexion de {hostname} ({ip})", "info")

                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.callback_log(f"❌ Erreur d'acceptation: {str(e)}", "error")

        except Exception as e:
            self.callback_log(f"❌ Erreur serveur: {str(e)}", "error")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def handle_client(self, client_socket, address):
        ip = address[0]
        try:
            metadata_size = int.from_bytes(client_socket.recv(4), 'big')
            metadata = json.loads(client_socket.recv(metadata_size).decode())

            user_name = metadata['user_name']
            folder_path = metadata['folder_path']
            file_name = metadata['file_name']
            file_size = metadata['file_size']

            self.callback_log(
                f"📥 Réception de {file_name} ({self.format_size(file_size)}) de {user_name} ({ip})",
                "info"
            )

            if folder_path:
                dest_folder = Config.BASE_PATH / folder_path
            else:
                dest_folder = Config.BASE_PATH / user_name

            dest_folder.mkdir(parents=True, exist_ok=True)
            file_path = dest_folder / file_name

            received = 0
            start_time = datetime.now()

            with open(file_path, 'wb') as f:
                while received < file_size:
                    chunk = client_socket.recv(min(8192, file_size - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)

                    if file_size > 0:
                        progress = int((received / file_size) * 100)
                        self.callback_progress(file_name, progress)

            transfer_time = (datetime.now() - start_time).total_seconds()

            if received == file_size:
                speed = file_size / transfer_time if transfer_time > 0 else 0
                self.callback_log(
                    f"✅ {file_name} reçu avec succès ({self.format_size(speed)}/s)",
                    "success"
                )

                self.conn_manager.add_transfer(ip, user_name, file_name, file_size, folder_path)

                self.stats['total_files'] += 1
                self.stats['total_size'] += file_size
                self.stats['today_transfers'] += 1
                self.stats['active_connections'] = len(
                    [c for c in self.conn_manager.get_connections_list() if c['status'] == 'connected'])
                self.callback_stats(self.stats, self.conn_manager)
                self.callback_file(user_name, str(file_path), str(dest_folder))

                response = json.dumps({
                    "status": "success",
                    "message": "Fichier reçu avec succès",
                    "speed": f"{self.format_size(speed)}/s"
                }).encode()
                client_socket.send(len(response).to_bytes(4, 'big'))
                client_socket.send(response)
            else:
                self.callback_log(f"❌ Erreur: {file_name} incomplet", "error")

        except Exception as e:
            self.callback_log(f"❌ Erreur client {ip}: {str(e)}", "error")
        finally:
            client_socket.close()
            self.conn_manager.remove_connection(ip)
            self.stats['active_connections'] = len(
                [c for c in self.conn_manager.get_connections_list() if c['status'] == 'connected'])
            self.callback_stats(self.stats, self.conn_manager)

    def stop_server(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

    @staticmethod
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# ============================================
# APPLICATION PRINCIPALE
# ============================================
class ServerApp(ctk.CTk):
    def __init__(self, current_user):
        super().__init__()

        self.current_user = current_user
        self.is_admin = current_user['role'] == Config.ROLE_ADMIN

        self.title(Config.APP_NAME)
        self.geometry(Config.WINDOW_SIZE)
        self.minsize(*Config.WINDOW_MIN_SIZE)

        self.center_window()

        self.conn_manager = ConnectionManager()
        self.auth_manager = AuthManager()

        self.server_running = False
        self.receive_thread = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_content()

        self.after(100, self.load_file_structure)
        self.after(200, self.refresh_connections_view)
        self.after(300, lambda: self.add_log(
            f"✅ Connecté en tant que {current_user['full_name']} ({current_user['role']})", "success"))

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    # ============================================
    # BARRE LATÉRALE
    # ============================================
    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=Config.COLOR_PRIMARY)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(11, weight=1)
        sidebar.grid_propagate(False)

        logo_label = ctk.CTkLabel(sidebar, text="📡 SERVEUR PRO", font=ctk.CTkFont(size=20, weight="bold"),
                                  text_color=Config.COLOR_TEXT_WHITE)
        logo_label.grid(row=0, column=0, padx=20, pady=(30, 10))

        subtitle_label = ctk.CTkLabel(sidebar, text="Gestion de fichiers", font=ctk.CTkFont(size=12),
                                      text_color="#b3e5fc")
        subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 10))

        # Info utilisateur connecté
        user_frame = ctk.CTkFrame(sidebar, fg_color=Config.COLOR_PRIMARY_LIGHT, corner_radius=8)
        user_frame.grid(row=2, column=0, padx=15, pady=10, sticky="ew")

        user_icon = "👑" if self.is_admin else "👤"
        role_text = "Administrateur" if self.is_admin else "Utilisateur"
        ctk.CTkLabel(user_frame, text=f"{user_icon} {self.current_user['full_name']}",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=Config.COLOR_TEXT_WHITE).pack(pady=(8, 2))
        ctk.CTkLabel(user_frame, text=role_text,
                     font=ctk.CTkFont(size=10),
                     text_color="#b3e5fc").pack(pady=(0, 8))

        separator = ctk.CTkFrame(sidebar, height=2, fg_color=Config.COLOR_PRIMARY_LIGHT)
        separator.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "📊 Dashboard"),
            ("Connexions", "🖥️ PC Connectés"),
            ("Transferts", "📋 Transferts"),
            ("Fichiers", "📁 Fichiers"),
            ("Logs", "📝 Logs"),
            ("Utilisateurs", "👥 Utilisateurs"),
            ("Paramètres", "⚙️ Paramètres")
        ]

        for i, (tab_name, btn_text) in enumerate(nav_items):
            # Masquer les onglets sensibles pour les utilisateurs non-admin
            if tab_name in ["Utilisateurs", "Paramètres"] and not self.is_admin:
                continue

            btn = ctk.CTkButton(
                sidebar, text=btn_text,
                fg_color="transparent" if i > 0 else Config.COLOR_PRIMARY_LIGHT,
                hover_color="#283593", anchor="w", height=40, corner_radius=8,
                font=ctk.CTkFont(size=13),
                command=lambda name=tab_name: self.switch_tab(name)
            )
            btn.grid(row=i + 4, column=0, padx=10, pady=3, sticky="ew")
            self.nav_buttons[tab_name] = btn

        # Bouton de déconnexion
        logout_btn = ctk.CTkButton(
            sidebar, text="🚪 Déconnexion",
            fg_color=Config.COLOR_DANGER, hover_color="#d32f2f",
            anchor="w", height=40, corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.logout
        )
        logout_btn.grid(row=12, column=0, padx=10, pady=(10, 5), sticky="ew")

        version_label = ctk.CTkLabel(sidebar, text=Config.APP_VERSION, text_color="gray60",
                                     font=ctk.CTkFont(size=11))
        version_label.grid(row=13, column=0, padx=20, pady=(5, 20))

    def switch_tab(self, tab_name):
        try:
            if tab_name in self.tabview._tab_dict:
                self.tabview.set(tab_name)
                for key, btn in self.nav_buttons.items():
                    btn.configure(fg_color=Config.COLOR_PRIMARY_LIGHT if key == tab_name else "transparent")
                if tab_name == "Connexions":
                    self.refresh_connections_view()
                elif tab_name == "Transferts":
                    self.refresh_transfers_view()
                elif tab_name == "Utilisateurs":
                    self.refresh_users_view()
        except Exception as e:
            print(f"Erreur switch_tab: {e}")

    # ============================================
    # CONTENU PRINCIPAL
    # ============================================
    def create_main_content(self):
        main_container = ctk.CTkFrame(self, fg_color=Config.COLOR_BG_LIGHT)
        main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(2, weight=1)

        self.create_header(main_container)

        self.tabview = ctk.CTkTabview(main_container, fg_color=Config.COLOR_BG_WHITE)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.tabview.grid_columnconfigure(0, weight=1)
        self.tabview.grid_rowconfigure(0, weight=1)

        self.dashboard_tab = self.tabview.add("Dashboard")
        self.connections_tab = self.tabview.add("Connexions")
        self.transfers_tab = self.tabview.add("Transferts")
        self.files_tab = self.tabview.add("Fichiers")
        self.logs_tab = self.tabview.add("Logs")

        if self.is_admin:
            self.users_tab = self.tabview.add("Utilisateurs")
            self.settings_tab = self.tabview.add("Paramètres")

        self.create_dashboard()
        self.create_connections_view()
        self.create_transfers_view()
        self.create_files_view()
        self.create_logs_view()

        if self.is_admin:
            self.create_users_view()
            self.create_settings_view()

        self.create_footer(main_container)

    def create_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color=Config.COLOR_PRIMARY, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_columnconfigure(0, weight=1)

        header_left = ctk.CTkFrame(header, fg_color="transparent")
        header_left.grid(row=0, column=0, sticky="w", padx=25, pady=15)

        title_label = ctk.CTkLabel(header_left, text="Serveur de Transfert de Documents",
                                   font=ctk.CTkFont(size=22, weight="bold"),
                                   text_color=Config.COLOR_TEXT_WHITE)
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(header_left, text="Gestion centralisée des fichiers d'entreprise",
                                      font=ctk.CTkFont(size=13), text_color="#b3e5fc")
        subtitle_label.pack(anchor="w")

        status_frame = ctk.CTkFrame(header_left, fg_color="transparent")
        status_frame.pack(anchor="w", pady=(10, 0))

        self.status_indicator = ctk.CTkLabel(status_frame, text="●", font=ctk.CTkFont(size=20),
                                             text_color=Config.COLOR_WARNING)
        self.status_indicator.pack(side="left", padx=(0, 5))

        self.status_label = ctk.CTkLabel(status_frame, text="Serveur en attente", font=ctk.CTkFont(size=13),
                                         text_color="#b3e5fc")
        self.status_label.pack(side="left")

        header_right = ctk.CTkFrame(header, fg_color="transparent")
        header_right.grid(row=0, column=1, sticky="e", padx=25, pady=15)

        self.start_btn = ctk.CTkButton(header_right, text="▶ Démarrer le serveur", fg_color=Config.COLOR_SUCCESS,
                                       hover_color="#45a049", width=160, height=42,
                                       font=ctk.CTkFont(size=14, weight="bold"), command=self.start_server)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ctk.CTkButton(header_right, text="⏹ Arrêter le serveur", fg_color=Config.COLOR_DANGER,
                                      hover_color="#d32f2f", width=160, height=42,
                                      font=ctk.CTkFont(size=14, weight="bold"), command=self.stop_server,
                                      state="disabled")
        self.stop_btn.pack(side="left", padx=5)

    def create_footer(self, parent):
        footer = ctk.CTkFrame(parent, fg_color=Config.COLOR_BG_WHITE, corner_radius=8)
        footer.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))

        self.stats_label = ctk.CTkLabel(footer, text="📊 Fichiers: 0 | 💾 Taille: 0 MB | 🖥️ Connectés: 0",
                                        text_color=Config.COLOR_TEXT_LIGHT, font=ctk.CTkFont(size=11))
        self.stats_label.pack(side="left", padx=20, pady=8)

        self.clock_label = ctk.CTkLabel(footer, text="", text_color=Config.COLOR_TEXT_LIGHT,
                                        font=ctk.CTkFont(size=11))
        self.clock_label.pack(side="right", padx=20, pady=8)
        self.update_clock()

    def update_clock(self):
        self.clock_label.configure(text=f"🕐 {datetime.now().strftime('%H:%M:%S')}")
        self.after(1000, self.update_clock)

    # ============================================
    # ONGLET DASHBOARD
    # ============================================
    def create_dashboard(self):
        stats_frame = ctk.CTkFrame(self.dashboard_tab, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.stats_cards = {}
        cards_data = [
            ("📄", "Fichiers Reçus", "0", Config.COLOR_SUCCESS),
            ("💾", "Taille Totale", "0 MB", Config.COLOR_INFO),
            ("🖥️", "PC Connectés", "0", Config.COLOR_WARNING),
            ("📅", "Transferts Aujourd'hui", "0", "#9C27B0")
        ]

        for icon, title, value, color in cards_data:
            card = ctk.CTkFrame(stats_frame, fg_color=Config.COLOR_BG_WHITE, corner_radius=10)
            card.pack(side="left", expand=True, fill="both", padx=8, pady=5)

            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=36)).pack(pady=(15, 5))
            value_label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=26, weight="bold"), text_color=color)
            value_label.pack(pady=5)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color=Config.COLOR_TEXT_LIGHT).pack(
                pady=(0, 15))
            self.stats_cards[title] = value_label

        activity_frame = ctk.CTkFrame(self.dashboard_tab, fg_color=Config.COLOR_BG_WHITE, corner_radius=10)
        activity_frame.pack(fill="both", expand=True, padx=20, pady=10)

        activity_header = ctk.CTkFrame(activity_frame, fg_color="transparent")
        activity_header.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(activity_header, text="📋 Activité Récente", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=Config.COLOR_TEXT_DARK).pack(side="left")

        ctk.CTkButton(activity_header, text="Effacer", fg_color="transparent", hover_color="#ffebee",
                      text_color=Config.COLOR_DANGER, width=80, height=30, font=ctk.CTkFont(size=11),
                      command=lambda: self.recent_listbox.delete("1.0", "end")).pack(side="right")

        self.recent_listbox = ctk.CTkTextbox(activity_frame, height=200, font=ctk.CTkFont(size=12), fg_color="#fafafa")
        self.recent_listbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    # ============================================
    # ONGLET CONNEXIONS
    # ============================================
    def create_connections_view(self):
        toolbar = ctk.CTkFrame(self.connections_tab, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(toolbar, text="🖥️ Ordinateurs Connectés", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=Config.COLOR_TEXT_DARK).pack(side="left", padx=5)

        self.connections_count_label = ctk.CTkLabel(toolbar, text="0 connecté(s)", font=ctk.CTkFont(size=13),
                                                    text_color=Config.COLOR_TEXT_LIGHT)
        self.connections_count_label.pack(side="left", padx=10)

        ctk.CTkButton(toolbar, text="🔄 Actualiser", fg_color=Config.COLOR_INFO, hover_color="#1976D2",
                      width=120, command=self.refresh_connections_view).pack(side="right", padx=5)

        table_frame = ctk.CTkFrame(self.connections_tab, fg_color=Config.COLOR_BG_WHITE)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Connections.Treeview", background="white", fieldbackground="white", rowheight=35,
                        font=('Segoe UI', 10))
        style.configure("Connections.Treeview.Heading", background=Config.COLOR_PRIMARY, foreground="white",
                        font=('Segoe UI', 10, 'bold'), padding=10)

        self.connections_tree = ttk.Treeview(table_frame,
                                             columns=("hostname", "ip", "first_seen", "last_seen", "transfers", "size",
                                                      "status"),
                                             show="headings", height=15, style="Connections.Treeview")

        for col, text, width in [("hostname", "🖥️ Nom du PC", 180), ("ip", "🌐 Adresse IP", 140),
                                 ("first_seen", "🕐 Première connexion", 160),
                                 ("last_seen", "🕑 Dernière activité", 160), ("transfers", "📄 Transferts", 100),
                                 ("size", "💾 Volume total", 120), ("status", "🔌 Statut", 100)]:
            self.connections_tree.heading(col, text=text)
            self.connections_tree.column(col, width=width)

        scrollbar = ctk.CTkScrollbar(table_frame, command=self.connections_tree.yview)
        self.connections_tree.configure(yscrollcommand=scrollbar.set)
        self.connections_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        details_frame = ctk.CTkFrame(self.connections_tab, fg_color=Config.COLOR_BG_WHITE)
        details_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(details_frame, text="📋 Détails de la connexion sélectionnée",
                     font=ctk.CTkFont(size=14, weight="bold"), text_color=Config.COLOR_TEXT_DARK).pack(anchor="w",
                                                                                                       padx=20,
                                                                                                       pady=(10, 5))

        self.connection_details = ctk.CTkTextbox(details_frame, height=80, font=ctk.CTkFont(size=11),
                                                 fg_color="#fafafa")
        self.connection_details.pack(fill="x", padx=20, pady=(0, 10))

        self.connections_tree.bind("<<TreeviewSelect>>", self.on_connection_select)

    def refresh_connections_view(self):
        for item in self.connections_tree.get_children():
            self.connections_tree.delete(item)

        connections = self.conn_manager.get_connections_list()
        connections.sort(key=lambda x: x.get('last_seen', datetime.min), reverse=True)

        for conn in connections:
            status_text = "🟢 Connecté" if conn['status'] == 'connected' else "🔴 Déconnecté"
            tag = "connected" if conn['status'] == 'connected' else "disconnected"

            self.connections_tree.insert("", "end", values=(
                conn['hostname'], conn['ip'],
                conn['first_seen'].strftime("%d/%m/%Y %H:%M") if isinstance(conn['first_seen'], datetime) else conn[
                    'first_seen'],
                conn['last_seen'].strftime("%d/%m/%Y %H:%M") if isinstance(conn['last_seen'], datetime) else conn[
                    'last_seen'],
                conn['total_transfers'], ReceiveThread.format_size(conn['total_size']), status_text
            ), tags=(tag,))

        self.connections_tree.tag_configure("connected", background="#e8f5e9")
        self.connections_tree.tag_configure("disconnected", background="#ffebee")

        active = len([c for c in connections if c['status'] == 'connected'])
        self.connections_count_label.configure(text=f"{active} connecté(s) / {len(connections)} connu(s)")

    def on_connection_select(self, event):
        selected = self.connections_tree.selection()
        if not selected:
            return
        item = self.connections_tree.item(selected[0])
        values = item['values']
        details = f"""Nom du PC: {values[0]}
Adresse IP: {values[1]}
Première connexion: {values[2]}
Dernière activité: {values[3]}
Nombre de transferts: {values[4]}
Volume total transféré: {values[5]}
Statut: {values[6]}"""
        self.connection_details.delete("1.0", "end")
        self.connection_details.insert("1.0", details)

    # ============================================
    # ONGLET TRANSFERTS
    # ============================================
    def create_transfers_view(self):
        toolbar = ctk.CTkFrame(self.transfers_tab, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(toolbar, text="📋 Historique des Transferts", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=Config.COLOR_TEXT_DARK).pack(side="left", padx=5)

        self.transfers_count_label = ctk.CTkLabel(toolbar, text="0 transfert(s)", font=ctk.CTkFont(size=13),
                                                  text_color=Config.COLOR_TEXT_LIGHT)
        self.transfers_count_label.pack(side="left", padx=10)

        if self.is_admin:
            ctk.CTkButton(toolbar, text="🗑 Vider historique", fg_color=Config.COLOR_DANGER, hover_color="#d32f2f",
                          width=140, command=self.clear_permanent_history).pack(side="right", padx=5)
        ctk.CTkButton(toolbar, text="📊 Exporter CSV", fg_color="#9C27B0", hover_color="#7B1FA2",
                      width=120, command=self.export_transfers).pack(side="right", padx=5)
        ctk.CTkButton(toolbar, text="🔄 Actualiser", fg_color=Config.COLOR_INFO, hover_color="#1976D2",
                      width=120, command=self.refresh_transfers_view).pack(side="right", padx=5)

        # Barre de recherche
        search_frame = ctk.CTkFrame(self.transfers_tab, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(search_frame, text="🔍 Rechercher:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(search_frame, width=300,
                                         placeholder_text="Rechercher par nom, utilisateur, IP...")
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_transfers())

        ctk.CTkButton(search_frame, text="Rechercher", fg_color=Config.COLOR_INFO, width=100,
                      command=self.search_transfers).pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="✖ Effacer", fg_color="transparent", hover_color="#ffebee",
                      text_color=Config.COLOR_DANGER, width=80,
                      command=lambda: [self.search_entry.delete(0, "end"), self.refresh_transfers_view()]).pack(
            side="left", padx=5)

        table_frame = ctk.CTkFrame(self.transfers_tab, fg_color=Config.COLOR_BG_WHITE)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Transfers.Treeview", background="white", fieldbackground="white", rowheight=32,
                        font=('Segoe UI', 10))
        style.configure("Transfers.Treeview.Heading", background=Config.COLOR_PRIMARY, foreground="white",
                        font=('Segoe UI', 10, 'bold'), padding=10)

        self.transfers_tree = ttk.Treeview(table_frame,
                                           columns=("timestamp", "ip", "user", "file", "size", "folder", "status"),
                                           show="headings", height=15, style="Transfers.Treeview")

        for col, text, width in [("timestamp", "🕐 Date/Heure", 150), ("ip", "🌐 IP", 130),
                                 ("user", "👤 Utilisateur", 120), ("file", "📄 Fichier", 250),
                                 ("size", "💾 Taille", 100), ("folder", "📁 Dossier", 200),
                                 ("status", "✅ Statut", 80)]:
            self.transfers_tree.heading(col, text=text)
            self.transfers_tree.column(col, width=width)

        scrollbar = ctk.CTkScrollbar(table_frame, command=self.transfers_tree.yview)
        self.transfers_tree.configure(yscrollcommand=scrollbar.set)
        self.transfers_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

    def refresh_transfers_view(self):
        for item in self.transfers_tree.get_children():
            self.transfers_tree.delete(item)

        transfers = self.conn_manager.get_all_transfers()
        display_transfers = transfers[:1000]

        for transfer in display_transfers:
            timestamp = transfer['timestamp']
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
            elif isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp).strftime("%d/%m/%Y %H:%M:%S")
                except:
                    pass

            self.transfers_tree.insert("", "end", values=(
                timestamp, transfer.get('ip', 'N/A'), transfer.get('user_name', 'N/A'),
                transfer.get('file_name', 'N/A'), ReceiveThread.format_size(transfer.get('file_size', 0)),
                transfer.get('folder_path', 'N/A'),
                "✅ Succès" if transfer.get('status') == 'success' else "❌ Échec"
            ))

        total = len(transfers)
        displayed = len(display_transfers)
        self.transfers_count_label.configure(text=f"{total} transfert(s) au total | {displayed} affichés")

    def search_transfers(self):
        search_term = self.search_entry.get().strip()
        if not search_term:
            self.refresh_transfers_view()
            return

        results = self.conn_manager.search_transfers(search_term)

        for item in self.transfers_tree.get_children():
            self.transfers_tree.delete(item)

        for transfer in results[:500]:
            timestamp = transfer['timestamp']
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")

            self.transfers_tree.insert("", "end", values=(
                timestamp, transfer.get('ip', 'N/A'), transfer.get('user_name', 'N/A'),
                transfer.get('file_name', 'N/A'), ReceiveThread.format_size(transfer.get('file_size', 0)),
                transfer.get('folder_path', 'N/A'),
                "✅ Succès" if transfer.get('status') == 'success' else "❌ Échec"
            ))

        self.transfers_count_label.configure(
            text=f"{len(results)} résultat(s) trouvé(s) pour '{search_term}'")

    def export_transfers(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Fichier CSV", "*.csv")])
        if file_path:
            transfers = self.conn_manager.get_all_transfers()
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["Date/Heure", "IP", "Utilisateur", "Fichier", "Taille (octets)", "Dossier", "Statut"])
                for t in transfers:
                    timestamp = t['timestamp']
                    if isinstance(timestamp, datetime):
                        timestamp = timestamp.isoformat()
                    writer.writerow([timestamp, t.get('ip', ''), t.get('user_name', ''),
                                     t.get('file_name', ''), t.get('file_size', 0),
                                     t.get('folder_path', ''), t.get('status', '')])
            self.add_log(f"✅ {len(transfers)} transferts exportés vers {file_path}", "success")
            messagebox.showinfo("Export réussi", f"{len(transfers)} transferts exportés avec succès!")

    def clear_permanent_history(self):
        if not self.is_admin:
            messagebox.showerror("Accès refusé", "Seul un administrateur peut effacer l'historique.")
            return

        if messagebox.askyesno("⚠️ Confirmation",
                               "Voulez-vous vraiment supprimer TOUT l'historique permanent?\n\nCette action est IRRÉVERSIBLE!"):
            if self.conn_manager.clear_permanent_history():
                self.refresh_transfers_view()
                self.refresh_connections_view()
                self.add_log("🗑 Historique permanent effacé", "warning")
                messagebox.showinfo("Succès", "Historique effacé avec succès!")
            else:
                messagebox.showerror("Erreur", "Erreur lors de l'effacement de l'historique!")

    # ============================================
    # ONGLET FICHIERS
    # ============================================
    def create_files_view(self):
        toolbar = ctk.CTkFrame(self.files_tab, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(toolbar, text="🔄 Actualiser", fg_color=Config.COLOR_INFO, hover_color="#1976D2",
                      width=130, command=self.load_file_structure).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="📂 Ouvrir le dossier", fg_color=Config.COLOR_WARNING, hover_color="#F57C00",
                      width=150, command=lambda: os.startfile(str(Config.BASE_PATH))).pack(side="left", padx=5)

        if self.is_admin:
            ctk.CTkButton(toolbar, text="🏗 Créer la structure", fg_color="#9C27B0", hover_color="#7B1FA2",
                          width=150, command=self.create_folder_structure).pack(side="left", padx=5)

        tree_frame = ctk.CTkFrame(self.files_tab, fg_color=Config.COLOR_BG_WHITE)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", rowheight=32, font=('Segoe UI', 10))
        style.configure("Treeview.Heading", background=Config.COLOR_PRIMARY, foreground="white",
                        font=('Segoe UI', 10, 'bold'), padding=10)

        self.file_tree = ttk.Treeview(tree_frame, columns=("size", "date", "path"), show="tree headings", height=20)
        self.file_tree.heading("#0", text="📄 Nom du fichier")
        self.file_tree.heading("size", text="📏 Taille")
        self.file_tree.heading("date", text="📅 Date de modification")
        self.file_tree.heading("path", text="📂 Chemin complet")
        self.file_tree.column("#0", width=350)
        self.file_tree.column("size", width=100)
        self.file_tree.column("date", width=160)
        self.file_tree.column("path", width=350)

        scrollbar = ctk.CTkScrollbar(tree_frame, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        self.file_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        self.file_tree.bind("<Double-1>", self.on_tree_double_click)

    def on_tree_double_click(self, event):
        selected = self.file_tree.selection()
        if selected:
            item = self.file_tree.item(selected[0])
            file_path = item['values'][2] if len(item['values']) > 2 else None
            if file_path and os.path.exists(file_path):
                os.startfile(file_path if os.path.isdir(file_path) else os.path.dirname(file_path))

    def create_folder_structure(self):
        if not self.is_admin:
            messagebox.showerror("Accès refusé", "Seul un administrateur peut créer la structure.")
            return
        try:
            for folder in Config.DEFAULT_FOLDERS:
                folder_path = Config.BASE_PATH / folder
                folder_path.mkdir(parents=True, exist_ok=True)
                if folder in Config.DEFAULT_SUBFOLDERS:
                    for subfolder in Config.DEFAULT_SUBFOLDERS[folder]:
                        (folder_path / subfolder).mkdir(exist_ok=True)
            self.load_file_structure()
            messagebox.showinfo("Succès", "Structure de dossiers créée avec succès!")
            self.add_log("Structure de dossiers créée", "success")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création: {str(e)}")

    # ============================================
    # ONGLET LOGS
    # ============================================
    def create_logs_view(self):
        toolbar = ctk.CTkFrame(self.logs_tab, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=10)

        if self.is_admin:
            ctk.CTkButton(toolbar, text="🗑 Effacer les logs", fg_color=Config.COLOR_DANGER, hover_color="#d32f2f",
                          width=140, command=lambda: self.log_text.delete("1.0", "end")).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="💾 Exporter", fg_color=Config.COLOR_INFO, hover_color="#1976D2",
                      width=120, command=self.export_logs).pack(side="left", padx=5)

        self.log_counter = ctk.CTkLabel(toolbar, text="0 messages", font=ctk.CTkFont(size=11),
                                        text_color=Config.COLOR_TEXT_LIGHT)
        self.log_counter.pack(side="right", padx=10)

        log_frame = ctk.CTkFrame(self.logs_tab, fg_color=Config.COLOR_BG_WHITE)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.log_text = ctk.CTkTextbox(log_frame, font=ctk.CTkFont(family="Consolas", size=11),
                                       fg_color="#fafafa", text_color=Config.COLOR_TEXT_DARK, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    # ============================================
    # ONGLET UTILISATEURS (ADMIN UNIQUEMENT)
    # ============================================
    def create_users_view(self):
        toolbar = ctk.CTkFrame(self.users_tab, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(toolbar, text="👥 Gestion des Utilisateurs", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=Config.COLOR_TEXT_DARK).pack(side="left", padx=5)

        ctk.CTkButton(toolbar, text="➕ Nouvel utilisateur", fg_color=Config.COLOR_SUCCESS, hover_color="#45a049",
                      width=160, command=self.create_new_user).pack(side="right", padx=5)
        ctk.CTkButton(toolbar, text="🔄 Actualiser", fg_color=Config.COLOR_INFO, hover_color="#1976D2",
                      width=120, command=self.refresh_users_view).pack(side="right", padx=5)

        table_frame = ctk.CTkFrame(self.users_tab, fg_color=Config.COLOR_BG_WHITE)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        style = ttk.Style()
        style.configure("Users.Treeview", background="white", fieldbackground="white", rowheight=35,
                        font=('Segoe UI', 10))
        style.configure("Users.Treeview.Heading", background=Config.COLOR_PRIMARY, foreground="white",
                        font=('Segoe UI', 10, 'bold'), padding=10)

        self.users_tree = ttk.Treeview(table_frame,
                                       columns=("username", "full_name", "role", "created", "last_login"),
                                       show="headings", height=15, style="Users.Treeview")

        for col, text, width in [("username", "👤 Identifiant", 150),
                                 ("full_name", "📝 Nom complet", 200),
                                 ("role", "🔐 Rôle", 120),
                                 ("created", "📅 Créé le", 160),
                                 ("last_login", "🕐 Dernière connexion", 160)]:
            self.users_tree.heading(col, text=text)
            self.users_tree.column(col, width=width)

        scrollbar = ctk.CTkScrollbar(table_frame, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        self.users_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        # Boutons d'action
        actions_frame = ctk.CTkFrame(self.users_tab, fg_color=Config.COLOR_BG_WHITE)
        actions_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(actions_frame, text="🔑 Changer mot de passe", fg_color=Config.COLOR_WARNING,
                      hover_color="#F57C00", width=180,
                      command=self.change_user_password).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(actions_frame, text="🗑 Supprimer", fg_color=Config.COLOR_DANGER,
                      hover_color="#d32f2f", width=150,
                      command=self.delete_selected_user).pack(side="left", padx=10, pady=10)

        self.refresh_users_view()

    def refresh_users_view(self):
        if not hasattr(self, 'users_tree'):
            return
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)

        users = self.auth_manager.get_all_users()
        for user in users:
            role_text = "👑 Admin" if user['role'] == Config.ROLE_ADMIN else "👤 Utilisateur"
            created = user['created_at']
            if isinstance(created, str):
                try:
                    created = datetime.fromisoformat(created).strftime("%d/%m/%Y %H:%M")
                except:
                    pass

            last_login = user['last_login'] or "Jamais"
            if isinstance(last_login, str) and last_login != "Jamais":
                try:
                    last_login = datetime.fromisoformat(last_login).strftime("%d/%m/%Y %H:%M")
                except:
                    pass

            self.users_tree.insert("", "end", values=(
                user['username'], user['full_name'], role_text, created, last_login
            ))

    def create_new_user(self):
        if not self.is_admin:
            messagebox.showerror("Accès refusé", "Seul un administrateur peut créer des utilisateurs.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Nouvel utilisateur")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="➕ Créer un nouvel utilisateur",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="x", padx=30)

        ctk.CTkLabel(form, text="Identifiant:", anchor="w").pack(fill="x", pady=(5, 0))
        username_entry = ctk.CTkEntry(form, placeholder_text="nom.utilisateur")
        username_entry.pack(fill="x", pady=5)

        ctk.CTkLabel(form, text="Nom complet:", anchor="w").pack(fill="x", pady=(5, 0))
        fullname_entry = ctk.CTkEntry(form, placeholder_text="Jean Dupont")
        fullname_entry.pack(fill="x", pady=5)

        ctk.CTkLabel(form, text="Mot de passe:", anchor="w").pack(fill="x", pady=(5, 0))
        password_entry = ctk.CTkEntry(form, show="•", placeholder_text="••••••••")
        password_entry.pack(fill="x", pady=5)

        ctk.CTkLabel(form, text="Rôle:", anchor="w").pack(fill="x", pady=(5, 0))
        role_var = ctk.StringVar(value=Config.ROLE_USER)
        role_menu = ctk.CTkOptionMenu(form, values=["user", "admin"], variable=role_var)
        role_menu.pack(fill="x", pady=5)

        def save():
            username = username_entry.get().strip()
            fullname = fullname_entry.get().strip()
            password = password_entry.get()
            role = role_var.get()

            if not username or not fullname or not password:
                messagebox.showerror("Erreur", "Tous les champs sont obligatoires")
                return

            success, msg = self.auth_manager.create_user(username, password, fullname, role)
            if success:
                messagebox.showinfo("Succès", msg)
                self.refresh_users_view()
                self.add_log(f"👤 Nouvel utilisateur créé: {username} ({role})", "success")
                dialog.destroy()
            else:
                messagebox.showerror("Erreur", msg)

        ctk.CTkButton(dialog, text="💾 Créer", fg_color=Config.COLOR_SUCCESS,
                      command=save).pack(pady=20)

    def change_user_password(self):
        if not self.is_admin:
            messagebox.showerror("Accès refusé", "Seul un administrateur peut modifier les mots de passe.")
            return

        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
            return

        item = self.users_tree.item(selected[0])
        username = item['values'][0]

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Changer mot de passe - {username}")
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"🔑 Nouveau mot de passe pour {username}",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=20)

        password_entry = ctk.CTkEntry(dialog, show="•", placeholder_text="Nouveau mot de passe", width=250)
        password_entry.pack(pady=10)

        def save():
            new_password = password_entry.get()
            success, msg = self.auth_manager.change_password(username, new_password)
            if success:
                messagebox.showinfo("Succès", msg)
                self.add_log(f"🔑 Mot de passe modifié pour {username}", "success")
                dialog.destroy()
            else:
                messagebox.showerror("Erreur", msg)

        ctk.CTkButton(dialog, text="💾 Sauvegarder", fg_color=Config.COLOR_SUCCESS,
                      command=save).pack(pady=10)

    def delete_selected_user(self):
        if not self.is_admin:
            messagebox.showerror("Accès refusé", "Seul un administrateur peut supprimer des utilisateurs.")
            return

        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
            return

        item = self.users_tree.item(selected[0])
        username = item['values'][0]

        if username == self.current_user['username']:
            messagebox.showerror("Erreur", "Vous ne pouvez pas supprimer votre propre compte!")
            return

        if messagebox.askyesno("Confirmation", f"Supprimer l'utilisateur '{username}' ?"):
            success, msg = self.auth_manager.delete_user(username)
            if success:
                messagebox.showinfo("Succès", msg)
                self.refresh_users_view()
                self.add_log(f"🗑 Utilisateur supprimé: {username}", "warning")
            else:
                messagebox.showerror("Erreur", msg)

    # ============================================
    # ONGLET PARAMÈTRES (ADMIN UNIQUEMENT)
    # ============================================
    def create_settings_view(self):
        ctk.CTkLabel(self.settings_tab, text="⚙️ Configuration du Serveur", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=Config.COLOR_TEXT_DARK).pack(anchor="w", padx=30, pady=(20, 10))

        for title, entries in [
            ("🌐 Paramètres Réseau", [("Adresse IP:", "ip_entry", Config.SERVER_IP, 250),
                                     ("Port:", "port_entry", str(Config.SERVER_PORT), 250)]),
            ("💾 Paramètres de Stockage", [("Dossier racine:", "path_entry", str(Config.BASE_PATH), 350)])
        ]:
            frame = ctk.CTkFrame(self.settings_tab, fg_color=Config.COLOR_BG_WHITE)
            frame.pack(fill="x", padx=30, pady=10)

            ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=Config.COLOR_TEXT_DARK).pack(anchor="w", padx=20, pady=(15, 10))

            for label_text, attr_name, default_value, width in entries:
                entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
                entry_frame.pack(fill="x", padx=20, pady=8)

                ctk.CTkLabel(entry_frame, text=label_text, width=120, anchor="w").pack(side="left", padx=5)
                entry = ctk.CTkEntry(entry_frame, width=width)
                entry.insert(0, default_value)
                entry.pack(side="left", padx=10)
                setattr(self, attr_name, entry)

        ctk.CTkButton(self.settings_tab, text="📂 Parcourir", width=120, command=self.browse_folder).pack(anchor="w",
                                                                                                         padx=50,
                                                                                                         pady=5)

        save_frame = ctk.CTkFrame(self.settings_tab, fg_color="transparent")
        save_frame.pack(fill="x", padx=30, pady=20)

        ctk.CTkButton(save_frame, text="💾 Sauvegarder", fg_color=Config.COLOR_SUCCESS, hover_color="#45a049",
                      height=45, font=ctk.CTkFont(size=15, weight="bold"), command=self.save_settings).pack(
            side="left", padx=5)
        ctk.CTkButton(save_frame, text="🔄 Réinitialiser", fg_color="transparent", hover_color="#ffebee",
                      text_color=Config.COLOR_DANGER, border_width=2, border_color=Config.COLOR_DANGER,
                      height=45, font=ctk.CTkFont(size=15), command=self.reset_settings).pack(side="left", padx=10)

        # Section : Changer mon mot de passe
        pwd_frame = ctk.CTkFrame(self.settings_tab, fg_color=Config.COLOR_BG_WHITE)
        pwd_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(pwd_frame, text="🔐 Changer mon mot de passe", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=Config.COLOR_TEXT_DARK).pack(anchor="w", padx=20, pady=(15, 10))

        pwd_entry_frame = ctk.CTkFrame(pwd_frame, fg_color="transparent")
        pwd_entry_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(pwd_entry_frame, text="Nouveau mot de passe:", width=180, anchor="w").pack(side="left", padx=5)
        self.new_password_entry = ctk.CTkEntry(pwd_entry_frame, show="•", width=250)
        self.new_password_entry.pack(side="left", padx=10)

        ctk.CTkButton(pwd_frame, text="💾 Modifier mon mot de passe", fg_color=Config.COLOR_WARNING,
                      hover_color="#F57C00", command=self.change_my_password).pack(pady=15)

    def change_my_password(self):
        new_password = self.new_password_entry.get()
        if not new_password:
            messagebox.showerror("Erreur", "Veuillez entrer un nouveau mot de passe")
            return

        success, msg = self.auth_manager.change_password(self.current_user['username'], new_password)
        if success:
            messagebox.showinfo("Succès", "✅ Mot de passe modifié avec succès!")
            self.new_password_entry.delete(0, "end")
            self.add_log("🔑 Mot de passe modifié", "success")
        else:
            messagebox.showerror("Erreur", msg)

    # ============================================
    # MÉTHODES DE CONTRÔLE DU SERVEUR
    # ============================================
    def start_server(self):
        if not self.is_admin:
            messagebox.showerror("Accès refusé", "Seul un administrateur peut démarrer le serveur.")
            return

        try:
            Config.SERVER_IP = self.ip_entry.get()
            Config.SERVER_PORT = int(self.port_entry.get())
            Config.BASE_PATH = Path(self.path_entry.get())
            Config.BASE_PATH.mkdir(parents=True, exist_ok=True)

            self.receive_thread = ReceiveThread(
                callback_log=self.add_log, callback_progress=self.update_progress,
                callback_file=self.on_file_received, callback_stats=self.update_stats_display,
                conn_manager=self.conn_manager
            )
            self.receive_thread.start()

            self.server_running = True
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.status_indicator.configure(text_color=Config.COLOR_SUCCESS)
            self.status_label.configure(text=f"Serveur en écoute sur {Config.SERVER_IP}:{Config.SERVER_PORT}",
                                        text_color="#b3e5fc")
            self.add_log(f"Serveur démarré sur {Config.SERVER_IP}:{Config.SERVER_PORT}", "success")
            self.add_recent_activity("✅ Serveur démarré")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de démarrer le serveur:\n{str(e)}")
            self.add_log(f"Erreur de démarrage: {str(e)}", "error")

    def stop_server(self):
        if not self.is_admin:
            messagebox.showerror("Accès refusé", "Seul un administrateur peut arrêter le serveur.")
            return

        if self.receive_thread:
            self.receive_thread.stop_server()
            self.receive_thread = None
        self.server_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_indicator.configure(text_color=Config.COLOR_DANGER)
        self.status_label.configure(text="Serveur arrêté", text_color="#b3e5fc")
        self.add_log("Serveur arrêté", "info")
        self.add_recent_activity("⏹ Serveur arrêté")

    def update_stats_display(self, stats, conn_manager=None):
        self.after(0, lambda: self._update_stats(stats))

    def _update_stats(self, stats):
        try:
            self.stats_cards["Fichiers Reçus"].configure(text=str(stats['total_files']))
            self.stats_cards["Taille Totale"].configure(text=ReceiveThread.format_size(stats['total_size']))
            self.stats_cards["PC Connectés"].configure(text=str(stats['active_connections']))
            self.stats_cards["Transferts Aujourd'hui"].configure(text=str(stats['today_transfers']))
            self.stats_label.configure(
                text=f"📊 Fichiers: {stats['total_files']} | 💾 Taille: {ReceiveThread.format_size(stats['total_size'])} | 🖥️ Connectés: {stats['active_connections']} | 🕐 {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Erreur mise à jour stats: {e}")

    def add_log(self, message, log_type="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix_map = {"success": "✅", "error": "❌", "info": "ℹ️", "warning": "⚠️"}
        prefix = prefix_map.get(log_type, "ℹ️")
        self.after(0, lambda: self._insert_log(timestamp, prefix, message))

    def _insert_log(self, timestamp, prefix, message):
        try:
            self.log_text.insert("end", f"[{timestamp}] {prefix} {message}\n")
            self.log_text.see("end")
            line_count = int(self.log_text.index('end-1c').split('.')[0])
            self.log_counter.configure(text=f"{line_count} messages")
        except:
            pass

    def update_progress(self, file_name, progress):
        pass

    def on_file_received(self, user_name, file_path, folder_path):
        self.after(0, lambda: self._on_file_received(user_name, file_path, folder_path))

    def _on_file_received(self, user_name, file_path, folder_path):
        self.load_file_structure()
        self.refresh_transfers_view()
        self.add_recent_activity(f"📥 {os.path.basename(file_path)} reçu de {user_name}")

    def add_recent_activity(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.after(0, lambda: self.recent_listbox.insert("1.0", f"[{timestamp}] {message}\n"))

    def load_file_structure(self):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        if not Config.BASE_PATH.exists():
            Config.BASE_PATH.mkdir(parents=True, exist_ok=True)

        def add_directory(parent, path):
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.'):
                        continue
                    if item.is_dir():
                        dir_id = self.file_tree.insert(parent, "end", text=f"📁 {item.name}",
                                                       values=("", "", str(item)))
                        add_directory(dir_id, item)
                    else:
                        size = item.stat().st_size
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        self.file_tree.insert(parent, "end", text=f"📄 {item.name}",
                                              values=(
                                                  ReceiveThread.format_size(size), mtime.strftime("%d/%m/%Y %H:%M"),
                                                  str(item)))
            except PermissionError:
                pass

        add_directory("", Config.BASE_PATH)

    def export_logs(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Fichiers texte", "*.txt")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get("1.0", "end"))
            self.add_log(f"Logs exportés vers {file_path}", "success")
            messagebox.showinfo("Export réussi", f"Logs exportés vers:\n{file_path}")

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=str(Config.BASE_PATH), title="Sélectionner le dossier")
        if folder:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)

    def save_settings(self):
        if not self.is_admin:
            messagebox.showerror("Accès refusé", "Seul un administrateur peut modifier les paramètres.")
            return
        try:
            Config.SERVER_IP = self.ip_entry.get()
            Config.SERVER_PORT = int(self.port_entry.get())
            Config.BASE_PATH = Path(self.path_entry.get())
            Config.BASE_PATH.mkdir(parents=True, exist_ok=True)
            messagebox.showinfo("Succès", "✅ Paramètres sauvegardés avec succès!")
            self.add_log("Paramètres sauvegardés", "success")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur: {str(e)}")

    def reset_settings(self):
        if not self.is_admin:
            messagebox.showerror("Accès refusé", "Seul un administrateur peut réinitialiser les paramètres.")
            return
        if messagebox.askyesno("Confirmation", "Réinitialiser tous les paramètres?"):
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, "192.168.1.210")
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, "9999")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, "C:/ServeurData")
            self.add_log("Paramètres réinitialisés", "warning")

    def logout(self):
        """Déconnecte l'utilisateur et retourne à l'écran de login"""
        if self.server_running:
            if not messagebox.askyesno("Confirmation",
                                       "Le serveur est en cours d'exécution.\nVoulez-vous vraiment vous déconnecter?"):
                return
            self.stop_server()

        if messagebox.askyesno("Déconnexion", "Voulez-vous vraiment vous déconnecter?"):
            self.add_log(f"🚪 Déconnexion de {self.current_user['full_name']}", "info")
            self.destroy()
            # Retour à l'écran de login
            main()

    def on_closing(self):
        if self.server_running:
            if messagebox.askyesno("Confirmation",
                                   "Le serveur est en cours d'exécution.\nVoulez-vous vraiment quitter?"):
                self.stop_server()
                self.destroy()
        else:
            self.destroy()


# ============================================
# POINT D'ENTRÉE
# ============================================
def main():
    """Point d'entrée principal avec système de login"""
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Créer le gestionnaire d'authentification
    auth_manager = AuthManager()

    # Créer la fenêtre racine cachée pour le login
    root = ctk.CTk()
    root.withdraw()  # Cacher la fenêtre principale

    authenticated_user = [None]  # Utiliser une liste pour permettre la modification dans la closure

    def on_login_success(user):
        authenticated_user[0] = user

    # Afficher la fenêtre de login
    login_window = LoginWindow(auth_manager, on_login_success)
    root.wait_window(login_window)

    # Si l'utilisateur s'est authentifié, lancer l'application
    if authenticated_user[0]:
        root.destroy()
        app = ServerApp(authenticated_user[0])
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    else:
        root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    main()