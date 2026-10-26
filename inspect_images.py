import os
from PIL import Image

artifacts_dir = r"C:\Users\Yashnar\.gemini\antigravity\brain\5abed9ff-648e-4971-bb94-f942c7d742a5\.user_uploaded"
files = [f for f in os.listdir(artifacts_dir) if f.endswith(".png") or f.endswith(".jpg")]

for f in files:
    p = os.path.join(artifacts_dir, f)
    im = Image.open(p)
    print(f, im.size, im.format, im.mode)
