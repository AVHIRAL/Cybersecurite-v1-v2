import os
import psutil
import time
import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import pathlib
import threading
import pyperclip  # Ajout de l'importation de pyperclip
import whois

GMEM_MOVEABLE = 0x0002

# Afficher les informations Whois
def show_whois_info(event, tree):
    selected_items = tree.selection()
    if not selected_items:
        return

    item = selected_items[0]
    selected_ip = tree.item(item)['values'][2]

    try:
        whois_result = whois.whois(selected_ip)
    except Exception as e:
        print(f"Erreur lors de la récupération des informations Whois : {e}")
        whois_result = None

    if whois_result:
        whois_window = tk.Toplevel()
        whois_window.title(f"Whois : {selected_ip}")

        whois_text = tk.Text(whois_window, wrap=tk.WORD)
        whois_text.insert(tk.END, str(whois_result))
        whois_text.pack(expand=True, fill=tk.BOTH)

        scrollbar = ttk.Scrollbar(whois_window, orient='vertical', command=whois_text.yview)
        whois_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        whois_window.geometry("800x400")
    else:
        print("Aucune information Whois trouvée.")

def copy_ip_to_clipboard(event, tree):
    selected_items = tree.selection()
    if not selected_items:
        return

    item = selected_items[0]
    selected_ip = tree.item(item)['values'][2]
    pyperclip.copy(selected_ip)

def show_context_menu(event, tree, context_menu):
    item = tree.identify_row(event.y)
    if not item:
        return

    tree.selection_set(item)
    context_menu.post(event.x_root, event.y_root)

def update_process_list(tree):
    tree.delete(*tree.get_children())

    processus_list = []
    for processus in psutil.process_iter(['pid', 'name']):
        try:
            connexions = processus.connections()
            mapped_files = processus.memory_maps()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        else:
            for connexion in connexions:
                if connexion.status == psutil.CONN_ESTABLISHED:
                    dll_set = {mf.path for mf in mapped_files if pathlib.Path(mf.path).suffix.lower() == '.dll'}
                    time.sleep(0.01)
                    # Limiter le nombre de DLL affichées à un maximum de 10 par processus
                    dll_list = list(dll_set)[:10]

                    if connexion.raddr:
                        processus_list.extend([
                            [processus.info['pid'], processus.info['name'], connexion.raddr.ip, connexion.raddr.port, "Out"],
                            *[[processus.info['pid'], pathlib.Path(dll).name, connexion.raddr.ip, connexion.raddr.port, "Out"] for dll in dll_list]
                        ])
                    if connexion.laddr:
                        processus_list.extend([
                            [processus.info['pid'], processus.info['name'], connexion.laddr.ip, connexion.laddr.port, "In"],
                            *[[processus.info['pid'], pathlib.Path(dll).name, connexion.laddr.ip, connexion.laddr.port, "In"] for dll in dll_list]
                        ])

    for process in processus_list:
        tree.insert('', 'end', values=(process[0], process[1], process[2], process[3], process[4]), tags=(f'PID{process[0]}', f'Nom{process[0]}', f'Adresse IP{process[0]}', f'Port{process[0]}', f'Direction{process[0]}'))

    tree.tag_configure('PID', foreground='#0074D9')
    tree.tag_configure('Nom', foreground='#7FDBFF')
    tree.tag_configure('Adresse IP', foreground='#3D9970')
    tree.tag_configure('Port', foreground='#2ECC40')
    tree.tag_configure('Direction', foreground='#FFDC00')

    tree.after(20000, update_process_list, tree)   

def update_process_list_threaded(tree):
    thread = threading.Thread(target=update_process_list, args=(tree,))
    thread.daemon = True
    thread.start()

def open_folder(event, tree):
    item = tree.focus()
    if not item:
        return

    selected_process_pid = tree.item(item)['values'][0]

    try:
        process = psutil.Process(selected_process_pid)
        exe_path = process.exe()
        folder_path = os.path.dirname(exe_path)

        if sys.platform == "win32":
            subprocess.Popen(f'explorer "{folder_path}"')
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder_path])
        else:
            subprocess.Popen(["xdg-open", folder_path])
    except Exception as e:
        print(f"Erreur lors de l'ouverture du dossier : {e}")

def main():
    root = tk.Tk()
    root.title("") 

    root.iconbitmap(default='')

    # Crée un widget Label pour afficher le titre en gras
    title_text = "△ AVHIRAL - CYBERSECURITE V2.0 SCANNE WINDOWS △"
    title_label = tk.Label(root, text=title_text, font=("TkDefaultFont", 11, "bold"), background='#87CEFA')
    title_label.pack(side=tk.TOP, pady=10)
    
    # Modification du fond de la fenêtre
    root.configure(background='#87CEFA')

    # Création du widget Treeview avec les colonnes nécessaires
    tree = ttk.Treeview(root, columns=('PID', 'Nom', 'Adresse IP', 'Port', 'Direction'), show='headings')
    tree.heading('PID', text='PID', anchor='center')
    tree.heading('Nom', text='Nom', anchor='w')
    tree.heading('Adresse IP', text='Adresse IP', anchor='w')
    tree.heading('Port', text='Port', anchor='center')
    tree.heading('Direction', text='Direction', anchor='center')
     
    # Ajout d'une barre de défilement
    scrollbar = ttk.Scrollbar(root, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Affichage du widget Treeview
    tree.pack(fill=tk.BOTH, expand=True)

    # Création du menu contextuel
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="Copier", command=lambda: copy_ip_to_clipboard(None, tree))
    context_menu.add_separator()  
    context_menu.add_command(label="Whois", command=lambda: show_whois_info(None, tree))

    # Ajout du gestionnaire d'événements pour le double-clic
    tree.bind('<Double-1>', lambda event: open_folder(event, tree))
    tree.bind('<Button-3>', lambda event: show_context_menu(event, tree, context_menu))

    # Création du pied de page avec le texte en gras
    footer_text = "DOUBLE CLIQUER SUR LE EXE ET LE DOSSIER OU SE TROUVE LE FICHIER S'OUVRE, BOUTON DROIT COPIER IP OU WHOIS"
    footer_label = tk.Label(root, text=footer_text, font=("TkDefaultFont", 9, "bold"), background='#87CEFA')
    footer_label.pack(side=tk.BOTTOM, pady=10)

    # Modification des dimensions de la fenêtre
    root.geometry("800x400")

    # Personnalisation des styles
    style = ttk.Style(root)
    style.theme_use('default')
    style.configure("Treeview.Heading", background='#0087af', foreground='white', font=('TkDefaultFont', 9, 'bold'))

    # Lancement de la mise à jour de la liste de processus
    update_process_list_threaded(tree)

    # Ajout du gestionnaire d'événements pour le double-clic
    tree.bind('<Double-1>', lambda event: open_folder(event, tree))

    # Lancement de la boucle d'événements Tkinter
    root.mainloop()

if __name__ == "__main__":
    main()
