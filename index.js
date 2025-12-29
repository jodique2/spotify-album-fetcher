import { getAccessToken, searchSpotify, getArtistAlbums } from "./spotify.js";
import readline from "node:readline";
import fs from "fs/promises";
import path from "path";
import { execSync } from "child_process";

// criar interface do terminal
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function ask(question) {
  return new Promise(resolve => rl.question(question, resolve));
}

async function main() {
  const searchText = await ask("🔎 Pesquisa artista ou álbum: ");
  rl.close();

  if (!searchText.trim()) {
    console.log("Pesquisa vazia. A sair...");
    return;
  }

  const token = await getAccessToken();
  const results = await searchSpotify(searchText, token);

  const artistFromSearch = results.artists.items[0];
  const artistFromAlbum = results.albums.items[0]?.artists[0];
  const artistFinal = artistFromSearch || artistFromAlbum;

  if (!artistFinal) {
    console.log("Nenhum resultado encontrado");
    return;
  }

  const albums = await getArtistAlbums(artistFinal.id, token);

  const output = {
    id_artista: artistFinal.id,
    nome_artista: artistFinal.name,
    albuns: albums.map(album => ({
      id_album: album.id,
      nome_album: album.name,
      url_album: `https://open.spotify.com/album/${album.id}`
    })),
  };

  // criar pasta data se não existir
  const dataDir = path.join(process.cwd(), "data");
  await fs.mkdir(dataDir, { recursive: true });

  const fileName = `${output.nome_artista.toLowerCase().replace(/\s+/g, "_")}.json`;
  const filePath = path.join(dataDir, fileName);

  await fs.writeFile(filePath, JSON.stringify(output, null, 2), "utf-8");
  console.log(`\n💾 JSON criado: ${filePath}`);

  // chamar o script Python automaticamente
  const pythonScriptPath = path.join(process.cwd(), "processData.py");
  try {
    console.log("\n🚀 Iniciando downloads com Python...");
    execSync(`python "${pythonScriptPath}"`, { stdio: "inherit" });
  } catch (err) {
    console.error("❌ Erro ao executar o Python:", err.message);
  }
}

main();
