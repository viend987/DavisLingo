import os
import re
import subprocess
import sys
import tempfile
import uuid
from PIL import ImageGrab, Image, ImageEnhance, ImageFilter

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class OcrService:
    def __init__(self):
        self.base_dir = get_base_dir()
        self.tesseract_exe = os.path.join(self.base_dir, "tesseract", "tesseract.exe")
        if not os.path.exists(self.tesseract_exe):
            # Fallback to system tesseract if bundled is missing
            self.tesseract_exe = "tesseract"

    def preprocess_image(self, img):
        """
        Enhance FiveM/GTA V chat contrast for accurate OCR recognition.
        Maintains grayscale gradient anti-aliasing so Tesseract LSTM model performs optimally.
        """
        # Convert to grayscale
        gray = img.convert("L")
        
        # Upscale 2x with Lanczos filter for crisp text edges
        w, h = gray.size
        resized = gray.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
        
        # Increase contrast to separate colored chat text from dark background
        enhancer = ImageEnhance.Contrast(resized)
        contrasted = enhancer.enhance(1.8)
        
        # Apply sharpness boost for small GTA V fonts
        sharpener = ImageEnhance.Sharpness(contrasted)
        sharpened = sharpener.enhance(1.6)
        
        return sharpened

    def clean_ocr_text(self, text):
        """
        Clean common FiveM/JGVRP chat noise:
        - Strip timestamps like [12:34:56], [12:34], (12:34)
        - Clean leading junk punctuation and artifact bars
        """
        if not text:
            return ""
        
        lines = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            
            # Remove timestamp patterns: [02:30:15], [02:30], (14:52:10)
            line = re.sub(r"^\[\d{1,2}:\d{2}(?::\d{2})?\]\s*", "", line)
            line = re.sub(r"^\(\d{1,2}:\d{2}(?::\d{2})?\)\s*", "", line)
            
            # Strip leading/trailing artifacts like |, _, ~, .
            line = re.sub(r"^[\~\|\_\.\,\:\;\-\s]+", "", line)
            line = re.sub(r"[\~\|\_\s]+$", "", line)
            
            # Normalize whitespace
            line = re.sub(r"\s+", " ", line).strip()
            
            if line and len(line) >= 2:
                lines.append(line)
                
        return "\n".join(lines)

    def capture_and_read(self, bbox):
        """
        bbox dict: {'left': int, 'top': int, 'width': int, 'height': int}
        Returns: extracted text string
        """
        left = int(bbox.get("left", 0))
        top = int(bbox.get("top", 0))
        width = int(bbox.get("width", 100))
        height = int(bbox.get("height", 50))
        right = left + width
        bottom = top + height

        # 1. Grab screen region (supports single and multi-monitor setups)
        try:
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
        except TypeError:
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        
        # 2. Preprocess
        processed = self.preprocess_image(screenshot)

        # 3. Save to temporary image with unique filename to prevent thread collision
        temp_dir = tempfile.gettempdir()
        temp_img_path = os.path.join(temp_dir, f"prorp_ocr_{uuid.uuid4().hex[:8]}.png")
        processed.save(temp_img_path, format="PNG")

        # 4. Run Tesseract with CREATE_NO_WINDOW so no CMD pops up
        tessdata_dir = os.path.join(self.base_dir, "tesseract", "tessdata")
        cmd = [
            self.tesseract_exe,
            temp_img_path,
            "stdout",
            "--psm", "6"
        ]
        if os.path.exists(tessdata_dir):
            cmd.extend(["--tessdata-dir", tessdata_dir])

        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=creationflags,
                timeout=5
            )
            text = res.stdout.strip()
            return self.clean_ocr_text(text)
        except Exception as e:
            print(f"[OCR] Error executing Tesseract: {e}")
            return ""
        finally:
            try:
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            except Exception:
                pass
