import json
import os
import subprocess
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

# -------- Funções auxiliares --------
def sanitize_folder_name(name):
    """Remove caracteres inválidos para nomes de pastas no Windows"""
    return re.sub(r'[\\/:*?"<>|]', "_", name)

def download_album(python_exe, album_url, album_dir):
    """Roda spotdl para baixar o álbum na pasta correta"""
    print(f"\n🎵 Baixando álbum na pasta: {album_dir}")
    try:
        subprocess.run(
            [python_exe, "-m", "spotdl", album_url, "--cache-dir", cache_dir],
            cwd=album_dir,
            check=True
        )
        print(f"✅ Download concluído: {album_dir}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no download: {album_dir} -> {e}")

# -------- Configurações --------
data_dir = "data"                      # pasta onde estão os JSONs
download_root = r"Z:\Musica"   # pasta principal para salvar músicas
cache_dir = r"Z:\spotdl-temp"          # pasta temporária para cache do spotdl
python_exe = r"C:\Users\ruime\AppData\Local\Programs\Python\Python314\python.exe"
max_threads = 4                         # número de downloads simultâneos

# criar pastas raiz se não existirem
os.makedirs(download_root, exist_ok=True)
os.makedirs(cache_dir, exist_ok=True)

# -------- Processamento dos JSONs --------
json_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]

# lista de tarefas para paralelização
tasks = []

for json_file_name in json_files:
    file_path = os.path.join(data_dir, json_file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    artist_name = sanitize_folder_name(data["nome_artista"])
    artist_dir = os.path.join(download_root, artist_name)
    os.makedirs(artist_dir, exist_ok=True)

    print(f"\n🎤 Processando artista: {data['nome_artista']}")

    for album in data.get("albuns", []):
        album_name = sanitize_folder_name(album["nome_album"])
        album_dir = os.path.join(artist_dir, album_name)
        album_url = album.get("url_album")

        if not album_url:
            print(f"⚠️ URL do álbum '{album['nome_album']}' não encontrada. Pulando...")
            continue

        # só baixa se a pasta ainda não existir ou estiver vazia
        if os.path.exists(album_dir) and os.listdir(album_dir):
            print(f"⏭️ Álbum já existe, pulando: {album_name}")
            continue

        os.makedirs(album_dir, exist_ok=True)
        tasks.append((python_exe, album_url, album_dir))

# -------- Executar downloads em paralelo --------
with ThreadPoolExecutor(max_workers=max_threads) as executor:
    future_to_album = {executor.submit(download_album, *task): task[2] for task in tasks}

    for future in as_completed(future_to_album):
        album_dir = future_to_album[future]
        try:
            future.result()
        except Exception as e:
            print(f"❌ Erro inesperado no álbum {album_dir}: {e}")

# -------- Limpar cache do spotdl --------
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)
    print(f"\n🧹 Cache temporário apagado: {cache_dir}")

print("\n🎉 Todos os downloads concluídos!")
