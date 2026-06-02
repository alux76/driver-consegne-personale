import re

# Percorso del file manifest.json
file_path = 'static/manifest.json'

# Leggi il file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Sostituisci tutte le occorrenze di /static/icon- con /static/icon-new-
new_content = content.replace('/static/icon-', '/static/icon-new-')

# Scrivi il file modificato
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('✅ manifest.json aggiornato: /static/icon- → /static/icon-new-')