import os
from pathlib import Path
import pdfplumber
import docx
import pytesseract
from PIL import Image

DATA_DIR = os.environ.get("DATA_PATH", "data")

class DocumentProcessor:
    def __init__(self, storage_dir=DATA_DIR):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def list_documents(self):
        return [f.name for f in self.storage_dir.glob("*") if f.is_file()]

    def save_upload(self, filename: str, content: bytes):
        path = self.storage_dir / filename
        with open(path, "wb") as f:
            f.write(content)
        return str(path)

    def extract_text(self, filename: str):
        path = self.storage_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Document {filename} not found.")

        ext = path.suffix.lower()
        if ext == ".txt":
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".pdf":
            text = ""
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    # Try digital text extraction first
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        # Fallback to OCR if page contains no digital text
                        # Note: user needs tesseract installed on the system
                        try:
                            # Convert PDF page to image (requires extra deps like pdf2image ideally, 
                            # but simple pytesseract.image_to_string works on image objects)
                            # For simplicity in this demo without heavy pdf2image/poppler:
                            # We advise user to upload images for OCR or rely on digital PDFs.
                            # Real production code would use 'pdf2image' here.
                            text += "[OCR not fully implemented for PDF without system deps, please upload PNG/JPG for OCR test.]\n"
                        except Exception:
                            pass
                            
            return text
        elif ext == ".docx":
            doc = docx.Document(path)
            return "\n".join([para.text for para in doc.paragraphs])
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
             try:
                 image = Image.open(path)
                 text = pytesseract.image_to_string(image)
                 return text
             except Exception as e:
                 return f"Error performing OCR on image: {str(e)}"
        else:
            return f"[Unsupported file type: {ext}]"

# Singleton instance
processor = DocumentProcessor()
