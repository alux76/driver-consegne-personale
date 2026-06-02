from PIL import Image
import os

# Nome del tuo file icona originale (cambialo se necessario)
nome_file = 'icon-512.png'  # <-- metti il nome del tuo file

# Percorso del file
percorso_file = os.path.join('static', nome_file)

# Se il file non esiste, prova nella cartella corrente
if not os.path.exists(percorso_file):
    percorso_file = nome_file
    print(f"Cerco {nome_file} nella cartella corrente...")

# Apri l'immagine
img = Image.open(percorso_file)
print(f"✅ Immagine {percorso_file} caricata")

# Dimensioni da generare
dimensioni = [72, 96, 128, 144, 152, 192, 256, 512]

# Genera e salva le icone (sovrascrive quelle vecchie)
for s in dimensioni:
    img_resized = img.resize((s, s))
    img_resized.save(f'static/icon-{s}.png')
    print(f'✅ Icona {s}x{s} salvata (sovrascritta)')

print('✅ Tutte le icone sono state rigenerate!')