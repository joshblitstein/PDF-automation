import sys
import os
import logging
from pathlib import Path
import fitz
from PIL import Image
import io
import numpy as np

def setup_logging():
   logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def remove_background(image, threshold=250):
   image = image.convert('RGBA')
   data = np.array(image)
   gray = np.mean(data[:, :, :3], axis=2)
   mask = gray > threshold
   data[mask, 3] = 0
   return Image.fromarray(data)

def capture_page_as_image(page, scale=1, skip_top_portion=100):
   pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
   img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
   width = img.width
   height = img.height
   img_cropped = img.crop((0, skip_top_portion * scale, width, height))
   return remove_background(img_cropped)

def transfer_page_content(source_pdf, background_pdf, output_pdf, vertical_offset=0, scale=2, logo_height=100):
   logging.info(f"Starting content transfer from {source_pdf} to {output_pdf} with background {background_pdf}")
   
   try:
       source_doc = fitz.open(source_pdf)
       background_doc = fitz.open(background_pdf)
       output_doc = fitz.open()

       source_page = source_doc[0]
       background_page = background_doc[0]
           
       output_page = output_doc.new_page(width=background_page.rect.width, 
                                       height=background_page.rect.height)
       
       output_page.show_pdf_page(background_page.rect, background_doc, 0)
       
       try:
           page_image = capture_page_as_image(source_page, scale, logo_height)
           
           rect = fitz.Rect(
               0,
               vertical_offset + logo_height,
               background_page.rect.width,
               background_page.rect.height + vertical_offset
           )
           
           img_bytes = io.BytesIO()
           page_image.save(img_bytes, format="PNG")
           img_bytes.seek(0)
           
           output_page.insert_image(rect, stream=img_bytes.getvalue())
           
       except Exception as e:
           logging.error(f"Error processing page: {str(e)}")
           raise
       
       output_doc.save(output_pdf)
       logging.info(f"Content transfer completed. Output saved to {output_pdf}")
   
   except Exception as e:
       logging.error(f"An error occurred: {str(e)}")
       raise
   finally:
       for doc in [source_doc, background_doc, output_doc]:
           if doc:
               try:
                   doc.close()
               except:
                   pass

def process_pdf(source_pdf_path):
   try:
       os.makedirs('uploads', exist_ok=True)
       dest_path = os.path.join('uploads', 'source.pdf')
       with open(source_pdf_path, 'rb') as src, open(dest_path, 'wb') as dst:
           dst.write(src.read())

       setup_logging()
       background_pdf = "target.pdf"
       output_pdf = "output_with_content.pdf"
       
       if not all(Path(p).is_file() for p in [dest_path, background_pdf]):
           raise FileNotFoundError("Required files not found")
           
       if any(Path(p).stat().st_size == 0 for p in [dest_path, background_pdf]):
           raise ValueError("One or more files are empty")

       transfer_page_content(
           dest_path,
           background_pdf,
           output_pdf,
           vertical_offset=20,
           scale=2,
           logo_height=100
       )
       
       print(f"Successfully processed PDF. Output saved to: {output_pdf}")

   except Exception as e:
       print(f"Error processing PDF: {str(e)}")
       
if __name__ == "__main__":
   if len(sys.argv) != 2:
       print("Usage: Drag and drop a PDF file onto this script")
       sys.exit(1)
       
   source_pdf = sys.argv[1]
   process_pdf(source_pdf)