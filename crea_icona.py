from PIL import Image, ImageDraw

size = 512
img = Image.new('RGB', (size, size), color='#3498db')
draw = ImageDraw.Draw(img)

draw.rectangle([50, 50, size-50, size-50], outline='white', width=10)
draw.text((size//2-80, size//2-30), "🚚", fill='white', font=None)

img.save('static/icon-512.png')
print("Icona creata!")

# Crea le altre dimensioni
for s in [72, 96, 128, 144, 152, 192, 256]:
    img_resized = img.resize((s, s))
    img_resized.save(f'static/icon-{s}.png')
    print(f"Icona {s}x{s} creata")