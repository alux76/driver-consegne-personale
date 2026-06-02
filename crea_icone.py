from PIL import Image
import os

# Usa l'icona che hai appena copiato in static
img = Image.open('static/icon-512.png')
print('✅ Icona 512x512 caricata')

# Crea le altre dimensioni
for s in [72, 96, 128, 144, 152, 192, 256]:
    img_resized = img.resize((s, s))
    img_resized.save(f'static/icon-{s}.png')
    print(f'✅ Icona {s}x{s} creata')

print('✅ Tutte le icone sono state generate!')