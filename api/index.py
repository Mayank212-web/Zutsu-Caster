import os
from io import BytesIO
from http.server import BaseHTTPRequestHandler
import requests
from PIL import Image, ImageDraw, ImageFont
from vercel_blob import put

# --- Setup ---
API_KEY = os.environ.get("AIzaSyDLp9gYCXnqwQGdk6FitLlZBTY1YS-kxHk")
SHEET_ID = "1_VuwkfW1kN9FGr4aBrGwgaKNd7udCbSkYde-jmCOZ_s"
RANGE = "A2:D3" 
FONT_PATH = "fonts/ChakraPetch-Bold.ttf"

# Coordinates (same as before)
layout = [
    {"name": (455, 715), "slots": [(560, 485, 675, 600), (685, 485, 800, 600), (810, 485, 925, 600)]},
    {"name": (1100, 715), "slots": [(1185, 485, 1300, 600), (1310, 485, 1425, 600), (1435, 485, 1550, 600)]}
]

def run_gen():
    # Fetch Data
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{RANGE}?key={API_KEY}"
    rows = requests.get(url).json().get("values", [])
    
    img = Image.open("template.png").convert("RGBA")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 32)

    for i, row in enumerate(rows):
        if i >= len(layout): break
        data = row + [""] * 4
        # Draw Name
        draw.text(layout[i]["name"], data[0].upper(), fill="white", font=font, anchor="mm")
        # Draw Logos
        for s_idx, tag in enumerate(data[1:4]):
            logo_path = f"logos/{tag}.png"
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                box = layout[i]["slots"][s_idx]
                logo.thumbnail((box[2]-box[0], box[3]-box[1]), Image.LANCZOS)
                img.paste(logo, (box[0], box[1]), logo)

    # Save to memory and upload to Vercel Blob
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    # This overwrites the same file so the URL in OBS never changes
    blob = put("predictions.png", buffer.getvalue(), {"access": "public", "addRandomSuffix": "false"})
    return blob['url']

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            url = run_gen()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"Updated! Image URL: {url}".encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())