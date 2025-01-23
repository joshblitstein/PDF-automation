import fitz
import logging
from pathlib import Path
import statistics
import io
from PIL import Image

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def safe_color(color):
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        return color[:3]  # Return only RGB values
    return (0, 0, 0)  # Default to black if color is not in expected format

def normalize_font_size(size, mean_size, min_size, max_size, size_range):
    normalized = (size - min_size) / (max_size - min_size) if max_size > min_size else 0.5
    adjusted = (normalized * 0.5) + 0.25
    return min_size + (adjusted * size_range)

def transfer_content(source_pdf, background_pdf, output_pdf, min_size=8, max_size=16, size_scale=1.0, vertical_offset=0):
    logging.info(f"Starting content transfer from {source_pdf} to {output_pdf} with background {background_pdf}")
    
    try:
        source_doc = fitz.open(source_pdf)
        background_doc = fitz.open(background_pdf)
        output_doc = fitz.open()

        for page_num in range(min(len(source_doc), len(background_doc))):
            logging.info(f"Processing page {page_num + 1}")
            source_page = source_doc[page_num]
            background_page = background_doc[page_num]
            
            # Create new page with background
            output_page = output_doc.new_page(width=background_page.rect.width, height=background_page.rect.height)
            output_page.show_pdf_page(background_page.rect, background_doc, page_num)
            
            # Extract text
            text_instances = source_page.get_text("words")
            
            # Calculate statistics for font sizes
            font_sizes = [inst[5] for inst in text_instances]
            if font_sizes:
                mean_size = statistics.mean(font_sizes)
                min_observed = min(font_sizes)
                max_observed = max(font_sizes)
            else:
                mean_size, min_observed, max_observed = 12, 12, 12  # Default if no text
            
            size_range = max_size - min_size
            
            # Transfer text with normalized sizes and adjusted vertical position
            for inst in text_instances:
                try:
                    text = inst[4]
                    x, y = inst[0], inst[1] + vertical_offset  # Add vertical offset
                    original_font_size = inst[5]
                    normalized_size = normalize_font_size(original_font_size, mean_size, min_observed, max_observed, size_range)
                    font_size = (normalized_size + min_size) * size_scale
                    color = safe_color(inst[3])
                    
                    output_page.insert_text(
                        (x, y),
                        text,
                        fontsize=font_size,
                        color=color
                    )
                except Exception as e:
                    logging.warning(f"Failed to insert text: {e}")
            
            # Transfer images
            image_list = source_page.get_images(full=True)
            for img_index, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]
                    base_image = source_doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_rect = source_page.get_image_bbox(img_index)
                    
                    # Adjust image position
                    adjusted_rect = fitz.Rect(image_rect.x0, image_rect.y0 + vertical_offset,
                                              image_rect.x1, image_rect.y1 + vertical_offset)
                    
                    # Try to insert the image directly
                    try:
                        output_page.insert_image(adjusted_rect, stream=image_bytes)
                    except Exception as e:
                        logging.warning(f"Failed to insert image directly: {e}")
                        
                        # If direct insertion fails, try to convert and re-insert
                        try:
                            pil_image = Image.open(io.BytesIO(image_bytes))
                            pil_image = pil_image.convert("RGB")
                            with io.BytesIO() as buffer:
                                pil_image.save(buffer, format="PNG")
                                png_bytes = buffer.getvalue()
                            output_page.insert_image(adjusted_rect, stream=png_bytes)
                        except Exception as e:
                            logging.warning(f"Failed to insert converted image: {e}")
                
                except Exception as e:
                    logging.warning(f"Failed to process image: {e}")
        
        output_doc.save(output_pdf)
        logging.info(f"Content transfer completed. Output saved to {output_pdf}")
    
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        source_doc.close()
        background_doc.close()
        output_doc.close()

def main():
    setup_logging()

    # Specify your file paths here
    source_pdf = "source.pdf"
    background_pdf = "target.pdf"
    output_pdf = "output.pdf"
    
    # Adjust these parameters to fine-tune text sizes and position
    min_size = 8    # Minimum font size
    max_size = 16   # Maximum font size
    size_scale = 1.0  # Overall size scaling factor
    vertical_offset = 20  # Adjust this value to move content down (positive) or up (negative)

    source_path = Path(source_pdf)
    background_path = Path(background_pdf)
    output_path = Path(output_pdf)

    if not source_path.is_file():
        logging.error(f"Source file not found: {source_path}")
        return
    if not background_path.is_file():
        logging.error(f"Background file not found: {background_path}")
        return

    transfer_content(str(source_path), str(background_path), str(output_path), 
                     min_size, max_size, size_scale, vertical_offset)

if __name__ == "__main__":
    main()