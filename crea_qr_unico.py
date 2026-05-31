import qrcode

url = "https://driver-consegne.onrender.com/accedi"
qr = qrcode.make(url)
qr.save("qr_commerciante.png", scale=10)
print("✅ QR code salvato come qr_commerciante.png")