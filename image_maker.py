import os
import io
import random
import re
import textwrap
import requests
from io import BytesIO
from requests.auth import HTTPBasicAuth
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

FONT_URL = "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Black.ttf"
LOCAL_FONT_PATH = "Montserrat-Black.ttf"
IMAGES_DIR = "images"


def ensure_font_exists():
    """
    Ensures Montserrat-Black bold font exists locally.
    """
    if os.path.exists(LOCAL_FONT_PATH):
        return LOCAL_FONT_PATH

    print(f"Downloading bold typography font ({LOCAL_FONT_PATH})...")
    try:
        response = requests.get(FONT_URL, timeout=10)
        if response.status_code == 200:
            with open(LOCAL_FONT_PATH, "wb") as f:
                f.write(response.content)
            print("Font downloaded successfully.")
            return LOCAL_FONT_PATH
    except Exception as e:
        print(f"Notice: Could not download font ({e}). Using system fallback.")

    return None


def get_font(size=36):
    """
    Loads ImageFont with system fallbacks.
    """
    font_file = ensure_font_exists()
    if font_file and os.path.exists(font_file):
        try:
            return ImageFont.truetype(font_file, size)
        except Exception:
            pass

    system_font_candidates = [
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "arial.ttf"
    ]
    for candidate in system_font_candidates:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                continue

    return ImageFont.load_default()


def get_available_images(images_dir: str = IMAGES_DIR) -> list:
    """
    Scans the images folder for valid photo files (.jpg, .jpeg, .png).
    """
    if not os.path.exists(images_dir):
        return []

    valid_extensions = ('.jpg', '.jpeg', '.png')
    files = [
        os.path.join(images_dir, f)
        for f in os.listdir(images_dir)
        if f.lower().endswith(valid_extensions) and not f.startswith('.')
    ]
    return files


def render_title_on_top_bar(draw: ImageDraw.ImageDraw, title: str, width: int, bar_height: int, font_path: str):
    """
    Renders the title centered horizontally and vertically inside the top bar.
    Dynamically adjusts font size and word wrapping (single or two lines) for maximum readability.
    """
    clean_title = title.strip()
    
    # Candidate wraps: single line or 2-line wrap
    candidate_wraps = [
        [clean_title],
        textwrap.wrap(clean_title, width=int(len(clean_title) * 0.6)),
        textwrap.wrap(clean_title, width=int(len(clean_title) * 0.45))
    ]

    max_font_size = max(18, int(bar_height * 0.48))
    best_font = None
    best_lines = [clean_title]
    best_size = 14

    for size in range(max_font_size, 12, -2):
        try:
            font = ImageFont.truetype(font_path, size)
        except Exception:
            font = ImageFont.load_default()
            break

        for lines in candidate_wraps:
            if not lines:
                continue
            line_height = int(size * 1.25)
            total_h = len(lines) * line_height
            max_w = max(draw.textbbox((0, 0), l, font=font)[2] - draw.textbbox((0, 0), l, font=font)[0] for l in lines)

            if max_w <= width * 0.92 and total_h <= bar_height * 0.85:
                best_font = font
                best_lines = lines
                best_size = size
                break

        if best_font:
            break

    if not best_font:
        best_font = get_font(18)
        best_lines = [clean_title]

    # Draw centered lines with drop shadow for crisp readability
    line_h = int(best_size * 1.25)
    total_text_h = len(best_lines) * line_h
    start_y = max(4, (bar_height - total_text_h) // 2)

    for line in best_lines:
        bbox = draw.textbbox((0, 0), line, font=best_font)
        lw = bbox[2] - bbox[0]
        lx = (width - lw) // 2 - bbox[0]
        
        # Subtle shadow + pure white text
        draw.text((lx + 1, start_y + 1), line, fill=(0, 0, 0, 180), font=best_font)
        draw.text((lx, start_y), line, fill=(255, 255, 255, 255), font=best_font)
        start_y += line_h


def create_unique_images(title: str, count: int = 3, use_dalle: bool = False, images_dir: str = IMAGES_DIR) -> list:
    """
    Pulls real photos from the `images/` directory, applies a 50% opacity black overlay
    across the top 15% of the image height, and centers the article title in Montserrat-Black white text.
    Saves temporary JPEG images to disk for uploading.
    """
    valid_images = get_available_images(images_dir)
    if len(valid_images) < count:
        raise ValueError(f"Fewer than {count} images found in '{images_dir}'. Found {len(valid_images)}.")

    selected_images = random.sample(valid_images, count)
    font_path = ensure_font_exists() or LOCAL_FONT_PATH
    generated_paths = []

    print(f"\n[Image Engine] Selecting {count} real workshop photos from '{images_dir}' with top title overlay...")

    for idx, img_path in enumerate(selected_images, start=1):
        try:
            with Image.open(img_path) as raw_img:
                # 1. Convert base image to RGBA to preserve full original photo colors
                base_image = raw_img.convert("RGBA")
                width, height = base_image.size

                # 2. Top 15% height calculation
                bar_height = max(1, int(height * 0.15))

                # 3. Create transparent overlay canvas
                overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)

                # 4. Draw 50% opacity black rectangle (alpha 128) across ONLY the top 15%
                draw.rectangle([(0, 0), (width, bar_height)], fill=(0, 0, 0, 128))

                # 5. Render centered title text in pure white
                render_title_on_top_bar(draw, title, width, bar_height, font_path)

                # 6. Alpha composite and convert to RGB
                composite = Image.alpha_composite(base_image, overlay)
                final_img = composite.convert("RGB")

                # 7. Save output JPEG
                # Creates a clean, lowercase URL slug from the title (max 60 chars)
                clean_slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')[:60]
                
                output_filename = f"{clean_slug}-{idx}.jpg"
                final_img.save(output_filename, "JPEG", quality=90)
                generated_paths.append(output_filename)
                print(f" -> Generated branded photo {idx}/{count}: {output_filename} (from {os.path.basename(img_path)})")

        except Exception as e:
            print(f"⚠️ Error processing photo {img_path}: {e}")

    return generated_paths


def process_and_upload_gallery(
    post_topic: str,
    wp_url: str,
    wp_user: str,
    wp_app_pass: str,
    images_dir: str = IMAGES_DIR,
    count: int = 3
) -> str:
    """
    Selects 3 random images from the local images directory, applies a 50% opacity
    black overlay across the top 15% of the image with the post topic rendered in 
    Montserrat-Black bold white text, and directly uploads the in-memory JPEG bytes 
    to the WordPress Media endpoint.
    
    Returns a single, comma-separated string of the 3 new Media IDs (e.g., "7365,7366,7367").
    """
    valid_images = get_available_images(images_dir)
    if len(valid_images) < count:
        raise ValueError(f"Fewer than {count} valid images found in '{images_dir}'. Found {len(valid_images)}.")

    selected_images = random.sample(valid_images, count)
    uploaded_media_ids = []

    clean_slug = re.sub(r'[^a-zA-Z0-9]+', '-', post_topic.lower()).strip('-')[:45] or "gallery-image"
    font_path = ensure_font_exists() or LOCAL_FONT_PATH
    media_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/media"
    auth = HTTPBasicAuth(wp_user, wp_app_pass)

    for idx, img_path in enumerate(selected_images, start=1):
        with Image.open(img_path) as raw_img:
            # Convert to RGBA
            base_image = raw_img.convert("RGBA")
            width, height = base_image.size

            # Top 15% bar
            bar_height = max(1, int(height * 0.15))
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            draw.rectangle([(0, 0), (width, bar_height)], fill=(0, 0, 0, 128))

            render_title_on_top_bar(draw, post_topic, width, bar_height, font_path)

            composite = Image.alpha_composite(base_image, overlay)
            final_img = composite.convert("RGB")

            buffer = io.BytesIO()
            final_img.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)

            filename = f"{clean_slug}-{idx}.jpg"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "image/jpeg"
            }

            response = requests.post(
                media_url,
                auth=auth,
                headers=headers,
                data=buffer.getvalue(),
                timeout=35
            )

            if response.status_code == 201:
                media_id = response.json().get("id")
                uploaded_media_ids.append(str(media_id))
                print(f" -> Uploaded gallery image {idx}/{count} (Media ID: {media_id}) from {os.path.basename(img_path)}")
            else:
                raise RuntimeError(
                    f"Failed to upload image {filename} to WordPress: Status {response.status_code} - {response.text}"
                )

    gallery_ids_csv = ",".join(uploaded_media_ids)
    return gallery_ids_csv


def cleanup_local_images(image_paths: list) -> None:
    """
    Removes generated images locally after they have been uploaded to WordPress,
    preventing file buildup.
    """
    if not image_paths:
        return

    for path in image_paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
                print(f"🧹 Cleaned up local file: {path}")
        except Exception as e:
            print(f"Notice: Could not delete local file {path}: {e}")


# Backward compatibility aliases
create_branded_template_images = create_unique_images
create_branded_images = create_unique_images
generate_blog_images = create_unique_images