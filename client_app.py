import os
import socket
import json
import threading
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog

# ---------------------------------------------------------------------------
# Configuration générale
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COLOR_PRIMARY = "#1a237e"
COLOR_PRIMARY_LIGHT = "#3949ab"
COLOR_ACCENT = "#2962ff"
COLOR_SUCCESS = "#2e7d32"
COLOR_SUCCESS_HOVER = "#1b5e20"
COLOR_DANGER = "#e53935"
COLOR_DANGER_HOVER = "#c62828"
COLOR_WARNING = "#fb8c00"
COLOR_WARNING_HOVER = "#ef6c00"
COLOR_BG = "#eef1f8"
COLOR_CARD = "#ffffff"
COLOR_BORDER = "#e0e3eb"
COLOR_TEXT_MUTED = "#6b7280"

SERVER_IP = "192.168.1.210"
SERVER_PORT = 9999


# ---------------------------------------------------------------------------
# Boîte de dialogue : création du dossier de destination
# ---------------------------------------------------------------------------
class FolderSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Créer un dossier de destination")
        self.geometry("440x560")
        self.minsize(440, 560)
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        self.transient(parent)
        self.after(100, self.grab_set)
        self.result = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color=COLOR_PRIMARY, corner_radius=0, height=64)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        ctk.CTkLabel(
            header, text="📁 Nouveau dossier de destination",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="white"
        ).place(relx=0.5, rely=0.5, anchor="center")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=25, pady=(20, 0))

        ctk.CTkLabel(body, text="Département", font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w").pack(fill="x", pady=(0, 6))
        self.department_combo = ctk.CTkComboBox(
            body,
            values=["Production", "Administration", "Commercial", "RH", "Comptabilité"],
            height=36, border_width=1, button_color=COLOR_ACCENT
        )
        self.department_combo.pack(fill="x", pady=(0, 18))

        ctk.CTkLabel(body, text="Atelier / Service", font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w").pack(fill="x", pady=(0, 6))
        self.workshop_combo = ctk.CTkComboBox(
            body,
            values=["Atelier 1", "Atelier 2", "Atelier 3", "Bureau", "Stockage"],
            height=36, border_width=1, button_color=COLOR_ACCENT
        )
        self.workshop_combo.pack(fill="x", pady=(0, 18))

        ctk.CTkLabel(body, text="Sous-dossier personnalisé (optionnel)",
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(fill="x", pady=(0, 6))
        self.custom_entry = ctk.CTkEntry(body, height=36, placeholder_text="ex: Rapport_Juin_2026",
                                          border_width=1)
        self.custom_entry.pack(fill="x", pady=(0, 10))

        self.preview_label = ctk.CTkLabel(
            body, text="", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED,
            anchor="w", wraplength=360, justify="left"
        )
        self.preview_label.pack(fill="x", pady=(4, 0))

        self.department_combo.configure(command=lambda _v: self.update_preview())
        self.workshop_combo.configure(command=lambda _v: self.update_preview())
        self.custom_entry.bind("<KeyRelease>", lambda _e: self.update_preview())
        self.update_preview()

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=25, pady=20)
        button_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(button_frame, text="Annuler", fg_color="transparent",
                      border_width=1, border_color=COLOR_BORDER, text_color="#333",
                      hover_color="#f1f2f6", height=38, command=self.destroy
                      ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(button_frame, text="Valider", fg_color=COLOR_SUCCESS,
                      hover_color=COLOR_SUCCESS_HOVER, height=38,
                      font=ctk.CTkFont(weight="bold"), command=self.on_ok
                      ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def update_preview(self):
        parts = [self.department_combo.get(), self.workshop_combo.get()]
        custom = self.custom_entry.get().strip()
        if custom:
            parts.append(custom)
        self.preview_label.configure(text="Chemin: " + " / ".join(p for p in parts if p))

    def on_ok(self):
        path_parts = [self.department_combo.get(), self.workshop_combo.get()]
        custom = self.custom_entry.get().strip()
        if custom:
            path_parts.append(custom)
        self.result = "/".join(path_parts)
        self.destroy()


# ---------------------------------------------------------------------------
# Ligne d'affichage d'un fichier sélectionné
# ---------------------------------------------------------------------------
class FileRow(ctk.CTkFrame):
    ICONS = {
        ".pdf": "📕", ".doc": "📘", ".docx": "📘", ".xls": "📗", ".xlsx": "📗",
        ".ppt": "📙", ".pptx": "📙", ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️",
        ".zip": "🗜️", ".rar": "🗜️", ".txt": "📄",
    }

    def __init__(self, parent, filepath, on_remove):
        super().__init__(parent, fg_color=COLOR_CARD, corner_radius=8,
                          border_width=1, border_color=COLOR_BORDER, height=52)
        self.filepath = filepath
        self.on_remove = on_remove
        self.grid_columnconfigure(1, weight=1)
        self.pack_propagate(False)

        ext = os.path.splitext(filepath)[1].lower()
        icon = self.ICONS.get(ext, "📄")

        ctk.CTkLabel(self, text=icon, font=ctk.CTkFont(size=20), width=36
                      ).grid(row=0, column=0, rowspan=2, padx=(12, 6), pady=8)

        name = os.path.basename(filepath)
        ctk.CTkLabel(self, text=name, font=ctk.CTkFont(size=13, weight="bold"),
                      anchor="w").grid(row=0, column=1, sticky="ew", padx=4, pady=(8, 0))

        try:
            size = os.path.getsize(filepath)
            size_text = ClientApp.format_size(size)
        except OSError:
            size_text = "introuvable"

        self.status_label = ctk.CTkLabel(self, text=size_text, font=ctk.CTkFont(size=11),
                      text_color=COLOR_TEXT_MUTED, anchor="w")
        self.status_label.grid(row=1, column=1, sticky="ew", padx=4, pady=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(self, height=4, progress_color=COLOR_ACCENT)
        self.progress_bar.grid(row=2, column=1, sticky="ew", padx=4, pady=(0, 6))
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()

        remove_btn = ctk.CTkButton(self, text="✕", width=28, height=28, fg_color="transparent",
                      text_color=COLOR_TEXT_MUTED, hover_color="#fdecea",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=lambda: self.on_remove(self))
        remove_btn.grid(row=0, column=2, rowspan=2, padx=10)

    def set_progress(self, pct, ok=None):
        self.progress_bar.grid()
        self.progress_bar.set(pct / 100)
        if ok is True:
            self.status_label.configure(text="✓ Envoyé", text_color=COLOR_SUCCESS)
            self.progress_bar.configure(progress_color=COLOR_SUCCESS)
        elif ok is False:
            self.status_label.configure(text="✗ Échec", text_color=COLOR_DANGER)
            self.progress_bar.configure(progress_color=COLOR_DANGER)
        else:
            self.status_label.configure(text=f"Envoi en cours… {pct}%", text_color=COLOR_ACCENT)


# ---------------------------------------------------------------------------
# Thread d'envoi réseau
# ---------------------------------------------------------------------------
class SendThread(threading.Thread):
    def __init__(self, callback_log, callback_progress, callback_finish, files, folder_path):
        super().__init__(daemon=True)
        self.callback_log = callback_log
        self.callback_progress = callback_progress
        self.callback_finish = callback_finish
        self.files = files
        self.folder_path = folder_path
        self.server_ip = SERVER_IP
        self.port = SERVER_PORT
        try:
            self.user_name = os.getlogin()
        except OSError:
            self.user_name = os.environ.get("USERNAME") or os.environ.get("USER") or "inconnu"

    def run(self):
        success_count = 0
        fail_count = 0

        for file_path in self.files:
            file_name = os.path.basename(file_path)
            sock = None
            try:
                if not os.path.exists(file_path):
                    raise FileNotFoundError("fichier introuvable (déplacé ou supprimé)")

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(15)
                sock.connect((self.server_ip, self.port))

                file_size = os.path.getsize(file_path)

                metadata = {
                    'user_name': self.user_name,
                    'folder_path': self.folder_path,
                    'file_name': file_name,
                    'file_size': file_size,
                    'timestamp': datetime.now().isoformat()
                }

                metadata_bytes = json.dumps(metadata).encode()
                sock.sendall(len(metadata_bytes).to_bytes(4, 'big'))
                sock.sendall(metadata_bytes)

                self.callback_log(f"⏳ Envoi de {file_name}…", "info")

                sent = 0
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        sock.sendall(chunk)
                        sent += len(chunk)

                        if file_size > 0:
                            progress = int((sent / file_size) * 100)
                            self.callback_progress(file_path, progress, None)

                size_bytes = sock.recv(4)
                if len(size_bytes) < 4:
                    raise ConnectionError("réponse du serveur incomplète")
                response_size = int.from_bytes(size_bytes, 'big')
                response = json.loads(sock.recv(response_size).decode())

                if response.get('status') == 'success':
                    self.callback_log(f"✓ {file_name} envoyé avec succès", "success")
                    self.callback_progress(file_path, 100, True)
                    success_count += 1
                else:
                    msg = response.get('message', 'erreur inconnue')
                    self.callback_log(f"✗ Erreur pour {file_name}: {msg}", "error")
                    self.callback_progress(file_path, 0, False)
                    fail_count += 1

            except (ConnectionRefusedError, socket.timeout, OSError) as e:
                self.callback_log(f"✗ {file_name}: connexion au serveur impossible ({e})", "error")
                self.callback_progress(file_path, 0, False)
                fail_count += 1
            except Exception as e:
                self.callback_log(f"✗ {file_name}: {e}", "error")
                self.callback_progress(file_path, 0, False)
                fail_count += 1
            finally:
                if sock:
                    try:
                        sock.close()
                    except OSError:
                        pass

        self.callback_finish(success_count, fail_count)


# ---------------------------------------------------------------------------
# Application principale
# ---------------------------------------------------------------------------
class ClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Transfert de Documents — Client")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=COLOR_BG)

        self.selected_files = []
        self.file_rows = {}
        self.folder_path = ""
        self.send_thread = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_ui()

    # ------------------------------------------------------------------ UI
    def create_ui(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(2, weight=1)

        self._build_header(main_container)
        self._build_folder_bar(main_container)
        self._build_content(main_container)
        self._build_footer(main_container)

    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color=COLOR_PRIMARY, corner_radius=12, height=72)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=22, pady=12)

        ctk.CTkLabel(left, text="📤  Transfert de Documents", font=ctk.CTkFont(size=19, weight="bold"),
                      text_color="white").pack(anchor="w")

        try:
            user = os.getlogin()
        except OSError:
            user = os.environ.get("USERNAME") or os.environ.get("USER") or "inconnu"

        ctk.CTkLabel(left, text=f"Connecté en tant que {user}", font=ctk.CTkFont(size=12),
                      text_color="#9fa8da").pack(anchor="w")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e", padx=22)

        self.conn_dot = ctk.CTkLabel(right, text="●", font=ctk.CTkFont(size=14),
                      text_color="#69f0ae")
        self.conn_dot.pack(side="left", padx=(0, 4))
        ctk.CTkLabel(right, text=f"{SERVER_IP}:{SERVER_PORT}", font=ctk.CTkFont(size=12),
                      text_color="#c5cae9").pack(side="left")

    def _build_folder_bar(self, parent):
        folder_frame = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=10,
                                     border_width=1, border_color=COLOR_BORDER)
        folder_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        folder_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(folder_frame, text="📁", font=ctk.CTkFont(size=18)).grid(
            row=0, column=0, padx=(16, 8), pady=14)

        self.folder_display = ctk.CTkEntry(
            folder_frame, height=38, border_width=0, fg_color="#f4f5f9",
            placeholder_text="Aucun dossier de destination sélectionné", state="readonly"
        )
        self.folder_display.grid(row=0, column=1, sticky="ew", padx=4, pady=14)

        ctk.CTkButton(
            folder_frame, text="Choisir / créer un dossier",
            fg_color=COLOR_WARNING, hover_color=COLOR_WARNING_HOVER,
            height=38, width=190, font=ctk.CTkFont(weight="bold"),
            command=self.select_folder
        ).grid(row=0, column=2, padx=14, pady=14)

    def _build_content(self, parent):
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        self._build_files_panel(content)
        self._build_logs_panel(content)

    def _build_files_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=10,
                              border_width=1, border_color=COLOR_BORDER)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(panel, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        head.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(head, text="Fichiers sélectionnés", font=ctk.CTkFont(size=15, weight="bold")
                      ).grid(row=0, column=0, sticky="w")
        self.file_count_badge = ctk.CTkLabel(
            head, text="0", font=ctk.CTkFont(size=11, weight="bold"), text_color="white",
            fg_color=COLOR_ACCENT, corner_radius=10, width=26, height=20
        )
        self.file_count_badge.grid(row=0, column=1, sticky="e")

        self.files_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.files_scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
        self.files_scroll.grid_columnconfigure(0, weight=1)

        self.empty_state = ctk.CTkLabel(
            self.files_scroll, text="Aucun fichier pour le moment.\nUtilisez les boutons ci-dessous pour en ajouter.",
            font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_MUTED, justify="center"
        )
        self.empty_state.grid(row=0, column=0, pady=40)

        buttons_frame = ctk.CTkFrame(panel, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 4))
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(buttons_frame, text="➕ Fichiers", fg_color=COLOR_ACCENT,
                      hover_color=COLOR_PRIMARY_LIGHT, height=36, command=self.add_files
                      ).grid(row=0, column=0, padx=3, sticky="ew")

        ctk.CTkButton(buttons_frame, text="📂 Dossier", fg_color=COLOR_ACCENT,
                      hover_color=COLOR_PRIMARY_LIGHT, height=36, command=self.add_folder
                      ).grid(row=0, column=1, padx=3, sticky="ew")

        ctk.CTkButton(buttons_frame, text="✖ Tout effacer", fg_color="transparent",
                      border_width=1, border_color=COLOR_BORDER, text_color=COLOR_DANGER,
                      hover_color="#fdecea", height=36, command=self.clear_files
                      ).grid(row=0, column=2, padx=3, sticky="ew")

        self.send_btn = ctk.CTkButton(
            panel, text="🚀  Envoyer les fichiers", fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER, height=46, font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled", command=self.send_files
        )
        self.send_btn.grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 16))

    def _build_logs_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=10,
                              border_width=1, border_color=COLOR_BORDER)
        panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        panel.grid_rowconfigure(3, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(panel, text="Progression globale", font=ctk.CTkFont(size=15, weight="bold")
                      ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 6))

        prog_frame = ctk.CTkFrame(panel, fg_color="transparent")
        prog_frame.grid(row=1, column=0, sticky="ew", padx=16)
        prog_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(prog_frame, height=10, progress_color=COLOR_ACCENT)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(panel, text="En attente d'envoi…",
                      font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED)
        self.progress_label.grid(row=2, column=0, sticky="w", padx=16, pady=(6, 14))

        log_head = ctk.CTkFrame(panel, fg_color="transparent")
        log_head.grid(row=3, column=0, sticky="new", padx=16)
        log_head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_head, text="Journal des transferts", font=ctk.CTkFont(size=15, weight="bold")
                      ).grid(row=0, column=0, sticky="w")

        self.log_text = ctk.CTkTextbox(
            panel, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#1e1e2e", text_color="#d4d4f0", corner_radius=8
        )
        self.log_text.grid(row=4, column=0, sticky="nsew", padx=16, pady=(8, 8))
        self.log_text.configure(state="disabled")

        ctk.CTkButton(
            panel, text="Effacer le journal", fg_color="transparent",
            border_width=1, border_color=COLOR_BORDER, text_color="#555",
            hover_color="#f1f2f6", height=34, command=self.clear_log
        ).grid(row=5, column=0, sticky="e", padx=16, pady=(0, 16))

    def _build_footer(self, parent):
        footer = ctk.CTkFrame(parent, fg_color="transparent", height=24)
        footer.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        self.stats_label = ctk.CTkLabel(
            footer, text=f"Serveur {SERVER_IP}:{SERVER_PORT}  •  0 fichier(s)  •  0 KB",
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED
        )
        self.stats_label.pack(side="left")

    # -------------------------------------------------------------- Logic
    def select_folder(self):
        dialog = FolderSelectionDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            self.folder_path = dialog.result
            try:
                user = os.getlogin()
            except OSError:
                user = os.environ.get("USERNAME") or os.environ.get("USER") or "inconnu"

            self.folder_display.configure(state="normal")
            self.folder_display.delete(0, "end")
            self.folder_display.insert(0, f"{user}/{self.folder_path}")
            self.folder_display.configure(state="readonly")

            self.add_log(f"Dossier de destination défini : {self.folder_path}", "info")
            self.update_send_button()

    def add_file(self, filepath):
        if filepath in self.selected_files:
            return
        self.empty_state.grid_remove()

        self.selected_files.append(filepath)
        row = FileRow(self.files_scroll, filepath, self.remove_file_row)
        row.grid(row=len(self.selected_files), column=0, sticky="ew", pady=4)
        self.file_rows[filepath] = row
        self.update_stats()

    def add_files(self):
        files = filedialog.askopenfilenames(title="Sélectionner des fichiers")
        if files:
            for filepath in files:
                self.add_file(filepath)
            self.add_log(f"{len(files)} fichier(s) ajouté(s)", "info")
            self.update_send_button()

    def add_folder(self):
        folder = filedialog.askdirectory(title="Sélectionner un dossier")
        if folder:
            count = 0
            for root, _dirs, files in os.walk(folder):
                for file in files:
                    self.add_file(os.path.join(root, file))
                    count += 1
            self.add_log(f"Contenu du dossier ajouté ({count} fichier(s))", "info")
            self.update_send_button()

    def remove_file_row(self, row):
        if row.filepath in self.selected_files:
            self.selected_files.remove(row.filepath)
        self.file_rows.pop(row.filepath, None)
        row.destroy()
        self._relayout_rows()
        self.update_stats()
        self.update_send_button()
        if not self.selected_files:
            self.empty_state.grid()

    def _relayout_rows(self):
        for i, filepath in enumerate(self.selected_files, start=1):
            self.file_rows[filepath].grid(row=i, column=0, sticky="ew", pady=4)

    def clear_files(self):
        for row in self.file_rows.values():
            row.destroy()
        self.file_rows.clear()
        self.selected_files.clear()
        self.empty_state.grid()
        self.update_stats()
        self.update_send_button()

    def update_send_button(self):
        if self.selected_files and self.folder_path:
            self.send_btn.configure(state="normal")
        else:
            self.send_btn.configure(state="disabled")

    def update_stats(self):
        total_size = sum(os.path.getsize(f) for f in self.selected_files if os.path.exists(f))
        self.file_count_badge.configure(text=str(len(self.selected_files)))
        self.stats_label.configure(
            text=f"Serveur {SERVER_IP}:{SERVER_PORT}  •  {len(self.selected_files)} fichier(s)  •  {self.format_size(total_size)}"
        )

    def add_log(self, message, level="info"):
        prefix = {"info": "ℹ", "success": "✓", "error": "✗"}.get(level, "•")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {prefix} {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def update_progress(self, filepath, progress, ok):
        row = self.file_rows.get(filepath)
        if row:
            row.set_progress(progress, ok)

        done = sum(1 for r in self.file_rows.values()
                   if r.status_label.cget("text").startswith(("✓", "✗")))
        total = len(self.selected_files) or 1
        self.progress_bar.set(done / total)
        self.progress_label.configure(text=f"{done}/{total} fichier(s) traités")

    def send_files(self):
        if not self.selected_files or not self.folder_path:
            return

        self.send_btn.configure(state="disabled", text="Envoi en cours…")
        self.progress_bar.set(0)
        self.send_thread = SendThread(
            lambda msg, lvl="info": self.after(0, self.add_log, msg, lvl),
            lambda fp, pct, ok: self.after(0, self.update_progress, fp, pct, ok),
            lambda s, f: self.after(0, self.send_finished, s, f),
            self.selected_files.copy(),
            self.folder_path
        )
        self.send_thread.start()

    def send_finished(self, success_count, fail_count):
        self.send_btn.configure(state="normal", text="🚀  Envoyer les fichiers")
        self.progress_label.configure(text="Transfert terminé")

        if fail_count == 0:
            messagebox.showinfo("Transfert terminé",
                                 f"{success_count} fichier(s) envoyé(s) avec succès !")
        elif success_count == 0:
            messagebox.showerror("Transfert échoué",
                                  f"Échec de l'envoi pour les {fail_count} fichier(s).")
        else:
            messagebox.showwarning("Transfert partiel",
                                    f"{success_count} fichier(s) envoyé(s), {fail_count} échec(s).\n"
                                    "Consultez le journal pour le détail.")

    @staticmethod
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def main():
    app = ClientApp()
    app.mainloop()


if __name__ == "__main__":
    main()