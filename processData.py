import json
import os
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# -------- Funções auxiliares --------
def sanitize_folder_name(name):
    return re.sub(r'[\\/:*?"<>|]', "_", name)

def download_album(python_exe, album_url, album_dir, artist_name, album_name, lock):
    """Roda spotdl para baixar o álbum na pasta correta e atualiza log"""
    print(f"\n🎵 Baixando: {artist_name} - {album_name}")
    try:
        subprocess.run(
            [python_exe, "-m", "spotdl", album_url],
            cwd=album_dir,
            check=True
        )
        print(f"✅ Concluído: {artist_name} - {album_name}")

        # atualizar log thread-safe
        with lock:
            downloaded_log.setdefault(artist_name, []).append(album_name)
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(downloaded_log, f, indent=2, ensure_ascii=False)

    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no download: {artist_name} - {album_name} -> {e}")

# -------- Configurações --------
data_dir = "data"
download_root = r"Z:\Musica"
python_exe = r"C:\Users\ruime\AppData\Local\Programs\Python\Python314\python.exe"
max_threads = 4
log_file = "downloaded_log.json"

os.makedirs(download_root, exist_ok=True)

# carregar log existente
if os.path.exists(log_file):
    with open(log_file, "r", encoding="utf-8") as f:
        downloaded_log = json.load(f)
else:
    downloaded_log = {}

lock = threading.Lock()

# -------- Perguntar qual JSON processar --------
json_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
if not json_files:
    print("❌ Nenhum JSON encontrado na pasta 'data/'")
    exit()

print("JSONs disponíveis para download:")
for i, f in enumerate(json_files, 1):
    print(f"{i}. {f}")

choice = input("\nDigite o número do JSON que quer processar: ").strip()
try:
    choice_idx = int(choice) - 1
    selected_json = json_files[choice_idx]
except:
    print("❌ Escolha inválida. Saindo...")
    exit()

file_path = os.path.join(data_dir, selected_json)
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

artist_name = sanitize_folder_name(data["nome_artista"])
artist_dir = os.path.join(download_root, artist_name)
os.makedirs(artist_dir, exist_ok=True)

# -------- Preparar tarefas --------
tasks = []
for album in data.get("albuns", []):
    album_name = sanitize_folder_name(album["nome_album"])
    album_dir = os.path.join(artist_dir, album_name)
    album_url = album.get("url_album")

    if not album_url:
        continue

    # só baixa se ainda não estiver no log
    if data["nome_artista"] in downloaded_log and album["nome_album"] in downloaded_log[data["nome_artista"]]:
        print(f"⏭️ Já baixado: {artist_name} - {album_name}")
        continue

    os.makedirs(album_dir, exist_ok=True)
    tasks.append((python_exe, album_url, album_dir, data["nome_artista"], album["nome_album"], lock))

# -------- Executar downloads em paralelo --------
with ThreadPoolExecutor(max_workers=max_threads) as executor:
    futures = [executor.submit(download_album, *task) for task in tasks]
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

print("\n🎉 Todos os downloads concluídos!")
