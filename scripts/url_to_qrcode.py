import sys, qrcode

if len(sys.argv) != 3:
    print("Usage: python url_to_qrcode.py <URL> <output_filename.png>")
    sys.exit(1)

url = sys.argv[1]
output_file = sys.argv[2]
if not output_file.lower().endswith(".png"):
    output_file += ".png"

qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=0,
)
qr.add_data(url)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
img = img.resize((100, 100))
img.save(output_file)
print(f"QR code saved as {output_file}")