import os
import re
import json
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

from processor import extract_yoast_description
from image_maker import cleanup_local_images

load_dotenv()

WP_URL = os.getenv("WP_SITE_URL", "").rstrip('/')
USERNAME = os.getenv("WP_USERNAME")
PASSWORD = os.getenv("WP_APP_PASSWORD")

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# In-memory category cache to avoid redundant network lookups
_CATEGORY_CACHE = {}


def get_or_create_category(category_name: str = "Guides") -> int:
    """
    Dynamically finds or creates the category ID in WordPress:
    1. Checks in-memory cache.
    2. Searches the WP REST API: /wp-json/wp/v2/categories?search={category_name}
    3. If not found, automatically creates the category via POST /wp-json/wp/v2/categories.
    4. Returns the valid integer category ID (defaults to 'Guides').
    """
    clean_name = category_name.strip()
    cache_key = clean_name.lower()

    if cache_key in _CATEGORY_CACHE:
        return _CATEGORY_CACHE[cache_key]

    categories_url = f"{WP_URL}/wp-json/wp/v2/categories"

    # Step 1: Search for existing category
    try:
        search_res = requests.get(
            categories_url,
            params={"search": clean_name},
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            headers=DEFAULT_HEADERS,
            timeout=15
        )

        if search_res.status_code == 200:
            categories = search_res.json()
            for cat in categories:
                cat_name = cat.get("name", "").strip().lower()
                cat_slug = cat.get("slug", "").strip().lower()
                target_slug = clean_name.lower().replace(" ", "-")

                if cat_name == clean_name.lower() or cat_slug == target_slug:
                    cat_id = cat.get("id")
                    _CATEGORY_CACHE[cache_key] = cat_id
                    print(f"📁 Found existing WordPress category '{clean_name}' (ID: {cat_id})")
                    return cat_id

            # If search returned results and one starts with or matches closely
            if categories:
                cat_id = categories[0].get("id")
                _CATEGORY_CACHE[cache_key] = cat_id
                print(f"📁 Matched category '{clean_name}' -> '{categories[0].get('name')}' (ID: {cat_id})")
                return cat_id

    except Exception as e:
        print(f"Notice: Exception searching category '{clean_name}': {e}")

    # Step 2: If category doesn't exist, create it dynamically
    try:
        create_res = requests.post(
            categories_url,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            headers=DEFAULT_HEADERS,
            json={"name": clean_name},
            timeout=15
        )

        if create_res.status_code == 201:
            cat_data = create_res.json()
            cat_id = cat_data.get("id")
            _CATEGORY_CACHE[cache_key] = cat_id
            print(f"✨ Created new WordPress category '{clean_name}' (ID: {cat_id})")
            return cat_id
        elif create_res.status_code == 400:
            # Handle case where category exists under another slug / term_exists error
            err_data = create_res.json()
            term_id = err_data.get("data", {}).get("term_id")
            if term_id:
                _CATEGORY_CACHE[cache_key] = term_id
                print(f"📁 Retrieved existing term ID for '{clean_name}' (ID: {term_id})")
                return term_id

    except Exception as e:
        print(f"Notice: Exception creating category '{clean_name}': {e}")

    # Step 3: Safe fallback ID for "Guides" (ID: 4)
    fallback_id = 4
    _CATEGORY_CACHE[cache_key] = fallback_id
    return fallback_id


def upload_image_to_wordpress(image_path: str, title: str):
    """
    Uploads an image to the WordPress Media Library via /wp-json/wp/v2/media.
    Sets alt_text, title, and caption matching the post title for image SEO.
    Returns (media_id, source_url).
    """
    if not os.path.exists(image_path):
        print(f"Warning: Image file not found: {image_path}")
        return None, None

    media_url = f"{WP_URL}/wp-json/wp/v2/media"
    headers = {
        **DEFAULT_HEADERS,
        'Content-Disposition': f'attachment; filename={os.path.basename(image_path)}'
    }

    try:
        with open(image_path, 'rb') as img_file:
            response = requests.post(
                media_url,
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                headers=headers,
                files={'file': img_file},
                timeout=35
            )

        if response.status_code == 201:
            media_data = response.json()
            media_id = media_data.get('id')
            source_url = media_data.get('source_url', '')

            # Set alt_text, title, and caption for image SEO
            requests.post(
                f"{media_url}/{media_id}",
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                headers=DEFAULT_HEADERS,
                json={
                    'alt_text': title,
                    'title': title,
                    'caption': title
                },
                timeout=15
            )
            print(f" -> Uploaded image to Media Library: {image_path} (Media ID: {media_id})")
            return media_id, source_url
        else:
            print(f"Failed to upload image {image_path}: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print(f"Error uploading image {image_path}: {e}")
        return None, None


def generate_faq_accordion_html(faq_items: list) -> str:
    """
    Generates styled HTML <details> and <summary> accordion markup for the FAQs.
    Matches Easy Accordion styling:
    - Light gray background (#f5f5f5) for summary question box
    - Bold dark text
    - 15px padding
    - 10px bottom margin
    - White background with 15px padding for answer box
    """
    if not faq_items:
        return ""

    accordion_html = (
        '\n\n<div class="sp-easy-accordion-wrapper" style="margin-top: 35px; margin-bottom: 25px; font-family: inherit;">\n'
        '  <h2 class="h2dav">Frequently Asked Questions?</h2>\n'
    )

    for idx, item in enumerate(faq_items, start=1):
        if isinstance(item, dict):
            q = item.get("question", "")
            a = item.get("answer", "")
        else:
            q = f"Question {idx}"
            a = str(item)

        accordion_html += (
            f'  <details style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 4px; margin-bottom: 10px; overflow: hidden;">\n'
            f'    <summary style="background: #f5f5f5; color: #222222; font-weight: bold; font-size: 16px; padding: 15px; cursor: pointer; outline: none; list-style: none; user-select: none;">\n'
            f'      {idx}. {q}\n'
            f'    </summary>\n'
            f'    <div style="background: #ffffff; color: #444444; padding: 15px; font-size: 15px; line-height: 1.6; border-top: 1px solid #eeeeee;">\n'
            f'      {a}\n'
            f'    </div>\n'
            f'  </details>\n'
        )

    accordion_html += '</div>\n'
    return accordion_html


def generate_faq_schema_jsonld(faq_items: list) -> str:
    """
    Generates strict Google-compliant JSON-LD FAQ Schema markup for insertion into the <head> scripts.
    """
    if not faq_items:
        return ""

    main_entities = []
    for idx, item in enumerate(faq_items, start=1):
        if isinstance(item, dict):
            q = item.get("question", "")
            a = item.get("answer", "")
        else:
            q = f"Question {idx}"
            a = str(item)

        main_entities.append({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": a
            }
        })

    schema_dict = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entities
    }

    schema_json = json.dumps(schema_dict, indent=2, ensure_ascii=False)
    return f'<script type="application/ld+json">\n{schema_json}\n</script>'


def publish_wordpress_post(
    title: str,
    content: str,
    image_paths: list = None,
    faq_items: list = None,
    category_name: str = "Guides",
    category_id: int = None,
    category_ids: list = None,
    gallery_ids_csv: str = None,
    status: str = "publish"
):
    """
    Publishes the blog post to WordPress directly as PUBLISHED.
    
    1. FEATURED IMAGE BINDING:
       - Uploads images to WordPress Media Library first or uses provided gallery Media IDs.
       - Assigns the primary uploaded media ID to 'featured_media' and meta['_thumbnail_id'].
       
    2. CUSTOM GALLERY / IN-CONTENT IMAGES ("Images" Box via Custom PHP Interceptor):
       - Sets top-level key 'custom_grid_images' to the uploaded Media IDs formatted strictly as a single comma-separated string (e.g., "7294,7295,7296"), NOT a Python list.
       - Strictly avoids injecting raw <img> tags into the HTML body content.
       
    3. SCHEMA HEADER INJECTION ("Insert Script to <head>" via Custom PHP Interceptor):
       - Builds Google-compliant JSON-LD FAQ Schema script.
       - Maps the schema script directly to top-level key 'custom_faq_schema'.
       - Strictly excludes raw schema from body content.
       
    4. YOAST SEO METADATA & LIVE PUBLISH STATUS:
       - Sets Yoast SEO title and dynamic meta description.
       - Sets status to 'publish' and assigns target categories.
       - Cleans up temporary local images after upload.
    """
    posts_url = f"{WP_URL}/wp-json/wp/v2/posts"

    # Step 1: Dynamically resolve category IDs (supports multiple selections)
    target_category_ids = []
    if category_ids:
        target_category_ids = [int(c) for c in category_ids if int(c) != 1]
    elif category_id is not None and int(category_id) != 1:
        target_category_ids = [int(category_id)]
    elif category_name:
        target_category_ids = [get_or_create_category(category_name)]

    if not target_category_ids:
        target_category_ids = [4]  # Default to Guides (ID: 4)

    # Step 2: Handle Media IDs from either gallery_ids_csv or image_paths
    if gallery_ids_csv:
        media_ids_csv = str(gallery_ids_csv).strip()
        media_ids = [int(i.strip()) for i in media_ids_csv.split(",") if i.strip().isdigit()]
        featured_media_id = media_ids[0] if media_ids else 0
    else:
        media_ids = []
        source_urls = []
        if image_paths:
            for path in image_paths:
                m_id, s_url = upload_image_to_wordpress(path, title)
                if m_id:
                    media_ids.append(m_id)
                    source_urls.append(s_url)

        featured_media_id = media_ids[0] if media_ids else 0
        media_ids_csv = ",".join(map(str, media_ids))

    # Step 3: Build clean body content (No raw <img> tags and no raw schema <script>)
    clean_body = re.sub(
        r'<script\b[^>]*type=[\'"]application/ld\+json[\'"][^>]*>.*?</script>',
        '',
        content,
        flags=re.DOTALL | re.IGNORECASE
    ).rstrip()

    schema_script = ""
    if faq_items:
        faq_accordion_html = generate_faq_accordion_html(faq_items)
        clean_body += faq_accordion_html
        schema_script = generate_faq_schema_jsonld(faq_items)

    # Step 4: Yoast SEO Metadata
    yoast_title = title
    yoast_metadesc = extract_yoast_description(content)

    # Step 5: Build WordPress Post Payload with multiple category IDs
    payload = {
        'title': title,
        'content': clean_body,
        'status': status,  # Published live immediately ('publish')
        'featured_media': featured_media_id,  # Direct Featured Image Binding
        'categories': target_category_ids,
        # --- Top-Level Custom Keys for Theme Interceptor Snippet ---
        'custom_grid_images': media_ids_csv,
        'custom_faq_schema': schema_script,
        'meta': {
            # --- Yoast SEO Meta ---
            '_yoast_wpseo_title': yoast_title,
            '_yoast_wpseo_metadesc': yoast_metadesc,
            
            # --- Featured Image Postmeta Binding ---
            '_thumbnail_id': featured_media_id,
        }
    }

    try:
        response = requests.post(
            posts_url,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            headers=DEFAULT_HEADERS,
            json=payload,
            timeout=35
        )

        if response.status_code == 201:
            post_data = response.json()
            post_id = post_data.get('id')
            edit_url = f"{WP_URL}/wp-admin/post.php?post={post_id}&action=edit"
            preview_url = post_data.get('link', '')

            print(f"\n✅ Post successfully published LIVE! (Post ID: {post_id}, Status: {status})")
            print(f"🖼️ Featured Media ID      : {featured_media_id}")
            print(f"📁 Categories Assigned    : IDs {target_category_ids} ({category_name})")
            print(f"📝 WordPress Edit URL     : {edit_url}")
            print(f"🌐 Post Live URL          : {preview_url}")

            # --- Second Request: Force-Update Custom Fields via Custom Endpoint ---
            force_meta_url = f"{WP_URL}/wp-json/custom/v1/force-meta/{post_id}"
            force_payload = {
                'grid_images': media_ids_csv,
                'faq_schema': schema_script
            }

            try:
                force_res = requests.post(
                    force_meta_url,
                    auth=HTTPBasicAuth(USERNAME, PASSWORD),
                    headers=DEFAULT_HEADERS,
                    json=force_payload,
                    timeout=25
                )

                if force_res.status_code == 200:
                    print(f"✨ Custom Meta Fields Force-Updated Successfully! (200 OK)")
                    print(f"   - Grid Images (boldthemes_theme_images) : {media_ids_csv}")
                    print(f"   - FAQ Schema (<head> script)            : Injected successfully")
                else:
                    print(f"⚠️ Failed to force-update custom fields: Status {force_res.status_code} - {force_res.text}")
            except Exception as force_err:
                print(f"⚠️ Exception during custom meta force-update request: {force_err}")

            # Local cleanup after successful upload
            cleanup_local_images(image_paths)

            # Attach URLs and metadata to returned dictionary
            post_data['edit_url'] = edit_url
            post_data['preview_url'] = preview_url
            post_data['yoast_metadesc'] = yoast_metadesc
            post_data['media_ids'] = media_ids
            post_data['featured_media_id'] = featured_media_id
            post_data['category_ids'] = target_category_ids
            post_data['category_id'] = target_category_ids[0] if target_category_ids else 4
            post_data['schema_script'] = schema_script

            return post_data
        else:
            print(f"❌ Failed to publish post: {response.status_code} - {response.text}")
            cleanup_local_images(image_paths)
            return None
    except Exception as e:
        print(f"❌ Exception during WordPress publication: {e}")
        cleanup_local_images(image_paths)
        return None