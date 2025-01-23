import fitz
import logging
from pathlib import Path
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

def main():
   setup_logging()

   source_pdf = "uploads/source.pdf"
   background_pdf = "target.pdf"
   output_pdf = Path("output") / f"{Path(source_pdf).stem}_output{Path(source_pdf).suffix}"
   
   vertical_offset = 20
   scale = 2
   logo_height = 100

   try:
       for file_path in [source_pdf, background_pdf]:
           if not Path(file_path).is_file():
               raise FileNotFoundError(f"File not found: {file_path}")
           if Path(file_path).stat().st_size == 0:
               raise ValueError(f"File is empty: {file_path}")

       transfer_page_content(
           source_pdf, 
           background_pdf, 
           output_pdf, 
           vertical_offset=vertical_offset, 
           scale=scale,
           logo_height=logo_height
       )
       
   except Exception as e:
       logging.error(f"Script failed: {str(e)}")
       raise

if __name__ == "__main__":
   main()