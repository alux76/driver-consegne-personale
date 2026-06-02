from PIL import Image

# Apri l'immagine nuova
img = Image.open('static/icon-new-512.png')
print('✅ Immagine icon-new-512.png caricata')

# Genera tutte le altre dimensioni
for s in [72, 96, 128, 144, 152, 192, 256]:
    img_resized = img.resize((s, s))
    img_resized.save(f'static/icon-new-{s}.png')
    print(f'✅ Icona icon-new-{s}.png creata')

print('✅ Tutte le icone sono state rigenerate dalla nuova immagine!')