from PIL import Image
import os

src = os.path.join('static','background.jpg')
if not os.path.exists(src):
    print('No background.jpg found at', src)
    raise SystemExit(1)

img = Image.open(src)
# Save optimized JPEG
jpg_out = os.path.join('static','background_opt.jpg')
img.save(jpg_out, 'JPEG', quality=75, optimize=True)
print('Saved', jpg_out)
# Save WebP
webp_out = os.path.join('static','background.webp')
img.save(webp_out, 'WEBP', quality=72, optimize=True)
print('Saved', webp_out)
# Overwrite background.jpg with optimized jpeg (optional)
img.save(src, 'JPEG', quality=85, optimize=True)
print('Rewrote', src)
