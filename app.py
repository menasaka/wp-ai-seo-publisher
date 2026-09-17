import os
import time
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from generator import generate_article_content, generate_faqs
from processor import process_and_format_article, extract_yoast_description
from image_maker import create_unique_images, cleanup_local_images
from wp_publisher import publish_wordpress_post

load_dotenv()

# Automatically bridge Streamlit Cloud Secrets into environment variables
try:
    if hasattr(st, "secrets"):
        for k, v in st.secrets.items():
            if isinstance(v, str):
                os.environ[k] = v
except Exception:
    pass

# Page configuration
st.set_page_config(
    page_title="SEO Blog Publisher | My Car Collision Center",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for premium look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        background-color: #EEF2FF;
        color: #4F46E5;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
    }
    .success-card {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
    }
    .meta-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)


def get_env_status():
    wp_url = os.getenv("WP_SITE_URL", "").rstrip('/')
    wp_user = os.getenv("WP_USERNAME", "")
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_wp = bool(wp_url and wp_user and os.getenv("WP_APP_PASSWORD"))
    return {
        "wp_url": wp_url,
        "wp_user": wp_user,
        "has_openai": has_openai,
        "has_wp": has_wp
    }


def main():
    env = get_env_status()

    # Sidebar: System Status & Settings
    with st.sidebar:
        st.header("⚙️ System Status")
        if env["has_wp"]:
            st.success(f"Connected to WordPress:\n`{env['wp_url']}`")
            st.caption(f"Authenticated as: **{env['wp_user']}**")
        else:
            st.error("WordPress credentials missing in `.env`")

        if env["has_openai"]:
            st.success("OpenAI API: Connected (GPT-4o & DALL-E 3)")
        else:
            st.error("OpenAI API Key missing in `.env`")

        st.divider()
        st.subheader("🛠️ Publishing Parameters")
        st.markdown("""
        - **Target Word Count:** ~1,200+ words
        - **Headings:** Question-based `H2` (`<h2 class="h2dav">`)
        - **Density:** 3–4 paragraphs per H2
        - **Shortcodes:** 7 evenly distributed
        - **Internal Links:** 3–4 shuffled with fallback
        - **Yoast SEO:** Dynamic Meta + Phone CTA
        - **FAQ Module:** Styled Accordion + JSON-LD Schema
        - **Post Status:** `draft` (100% Zero-Touch)
        """)

        st.divider()
        image_mode = st.radio(
            "Image Generation Engine:",
            options=["DALL-E 3 (Unique Dynamic Images)", "Local Branded Templates"],
            index=0
        )
        use_dalle = "DALL-E 3" in image_mode

    # Main Page Header
    st.markdown('<div class="main-header">🚗 My Car Collision Center</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Zero-Touch Automated SEO Blog Generator & WordPress Publishing Pipeline</div>', unsafe_allow_html=True)

    st.markdown(
        '<div>'
        '<span class="status-badge">OpenAI GPT-4o</span>'
        '<span class="status-badge">DALL-E 3 Engine</span>'
        '<span class="status-badge">WordPress REST API</span>'
        '<span class="status-badge">Yoast SEO & Schema</span>'
        '</div>',
        unsafe_allow_html=True
    )
    st.write("")

    # Main Tabs
    tab_single, tab_batch, tab_inspect = st.tabs(["📝 Single Post Generator", "📊 Google Sheets Batch Queue", "🔍 Post Meta Inspector"])

    with tab_single:
        st.subheader("Generate & Publish Single Article")

        # Preset topic buttons
        st.caption("Quick Select Sample Topics:")
        sample_topics = [
            "24/7 Collision Repair and Emergency Towing in Glendale & Studio City",
            "Why OEM Certified Auto Body Repair Matters for Luxury & Electric Vehicles",
            "How to Handle California Auto Insurance Claims After a Serious Car Accident",
            "Precision Computerized Frame Alignment and Unibody Straightening Guide"
        ]
        
        cols = st.columns(len(sample_topics))
        for idx, topic in enumerate(sample_topics):
            if cols[idx].button(f"Topic {idx+1}", key=f"topic_btn_{idx}", help=topic):
                st.session_state["blog_title"] = topic

        # Title Input
        default_title = st.session_state.get("blog_title", "24/7 Collision Repair and Emergency Towing in Glendale & Studio City")
        title_input = st.text_input("Blog Post Title", value=default_title, placeholder="Enter exact blog post title...")

        publish_clicked = st.button("🚀 Generate & Publish to WordPress", type="primary", use_container_width=True)

        if publish_clicked:
            if not title_input.strip():
                st.warning("Please enter a valid blog post title.")
                return

            progress_bar = st.progress(0)
            status_box = st.empty()

            try:
                # Step 1: Generate Content
                status_box.info("🧠 [1/5] Generating in-depth 1,200+ word article via OpenAI GPT-4o...")
                progress_bar.progress(15)
                raw_content = generate_article_content(title_input)
                word_count = len(raw_content.split())

                # Step 2: Generate FAQs
                status_box.info(f"❓ [2/5] Generated {word_count} words. Creating 10 structured FAQ Q&A pairs...")
                progress_bar.progress(35)
                faq_items = generate_faqs(title_input)

                # Step 3: Process & Format HTML
                status_box.info("⚙️ [3/5] Formatting headings (<h2 class=\"h2dav\">), bolding keywords, and distributing 7 shortcodes evenly...")
                progress_bar.progress(55)
                formatted_content = process_and_format_article(raw_content)

                # Step 4: Generate Images
                status_box.info("🎨 [4/5] Selecting 3 photos from local images folder and applying title overlay...")
                progress_bar.progress(75)
                image_paths = create_unique_images(title_input)

                # Step 5: Publish to WordPress
                status_box.info("🚀 [5/5] Uploading media, building Yoast SEO, FAQ Accordion & Schema, and publishing Draft to WordPress...")
                progress_bar.progress(90)
                post_data = publish_wordpress_post(
                    title=title_input,
                    content=formatted_content,
                    image_paths=image_paths,
                    faq_items=faq_items
                )
                progress_bar.progress(100)

                if post_data:
                    status_box.empty()
                    post_id = post_data.get("id")
                    edit_url = post_data.get("edit_url", f"{env['wp_url']}/wp-admin/post.php?post={post_id}&action=edit")
                    preview_url = post_data.get("preview_url", post_data.get("link", ""))
                    yoast_desc = post_data.get("yoast_metadesc", extract_yoast_description(formatted_content))

                    st.markdown(f"""
                    <div class="success-card">
                        <h3 style="color: #15803D; margin-top: 0;">🎉 Blog Post Successfully Published as DRAFT!</h3>
                        <p><strong>Post ID:</strong> {post_id} | <strong>Status:</strong> Draft | <strong>Target Categories:</strong> Assigned</p>
                        <p><strong>WordPress Edit URL:</strong> <a href="{edit_url}" target="_blank">{edit_url}</a></p>
                        <p><strong>Post Preview URL:</strong> <a href="{preview_url}" target="_blank">{preview_url}</a></p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Quick Action Buttons
                    btn_col1, btn_col2 = st.columns(2)
                    btn_col1.link_button("📝 Open Post in WordPress Editor", edit_url, use_container_width=True)
                    btn_col2.link_button("🌐 Open Post Preview", preview_url, use_container_width=True)

                    st.divider()

                    # Metrics & Review Section
                    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                    m_col1.metric("Article Words", word_count)
                    m_col2.metric("FAQs Included", len(faq_items))
                    m_col3.metric("Shortcodes Injected", 7)
                    m_col4.metric("Media Uploaded", len(post_data.get("media_ids", [])))

                    # Expander Tabs for Full Inspection
                    with st.expander("🔍 Inspect Yoast SEO & Meta Details", expanded=True):
                        st.markdown(f"**SEO Title (`_yoast_wpseo_title`):** `{title_input}`")
                        st.markdown(f"**Dynamic Meta Description (`_yoast_wpseo_metadesc`):**")
                        st.info(yoast_desc)
                        st.markdown(f"**Theme Gallery IDs (`_post_gallery`):** `{','.join(map(str, post_data.get('media_ids', [])))}`")

                    with st.expander("❓ Inspect Generated FAQ Accordion & Header Schema (<head>)"):
                        st.subheader("1. Rendered FAQ Accordion (Injected into Body):")
                        for idx, item in enumerate(faq_items, 1):
                            st.markdown(f"**{idx}. {item.get('question')}**")
                            st.write(item.get('answer'))

                        st.subheader("2. JSON-LD FAQ Schema (Routed to Header Meta / <head>):")
                        st.code(post_data.get("schema_script", ""), language="html")

                    with st.expander("📄 Inspect Full HTML Body Content (Clean Body)"):
                        st.code(formatted_content, language="html")

                else:
                    status_box.error("❌ Failed to publish post to WordPress. Check console logs and credentials.")

            except Exception as ex:
                status_box.error(f"❌ An error occurred during pipeline execution: {ex}")
                st.exception(ex)

    with tab_batch:
        st.subheader("Batch Publish from Google Sheet")
        st.markdown("Publish multiple articles in automated sequence with a safety cooldown between posts.")
        
        sheet_id_input = st.text_input("Google Sheet ID", value=os.getenv("GOOGLE_SHEET_ID", "1kieMk1araaWljeKZh4pxwteTtm6KGeqBAwdBRaw_meE"))
        
        if st.button("📥 Load Sheet & Start Batch Publishing", type="secondary"):
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id_input}/export?format=csv"
            try:
                import io
                import requests
                resp = requests.get(csv_url, timeout=15)
                if resp.status_code == 200:
                    df = pd.read_csv(io.StringIO(resp.text))
                    raw_titles = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
                    titles = [t for t in raw_titles if t and t.lower() not in ["title", "titles", "topic", "topics"]]
                    
                    st.success(f"Found {len(titles)} titles in queue!")
                    
                    batch_progress = st.progress(0)
                    batch_status = st.empty()
                    
                    for idx, topic in enumerate(titles, start=1):
                        batch_status.info(f"Processing ({idx}/{len(titles)}): **{topic}**...")
                        
                        # Pipeline execution
                        content = generate_article_content(topic)
                        faqs = generate_faqs(topic)
                        formatted = process_and_format_article(content)
                        images = create_unique_images(topic, use_dalle=use_dalle)
                        post = publish_wordpress_post(topic, formatted, images, faqs)
                        
                        if post:
                            st.write(f"✅ **[{idx}/{len(titles)}] Published:** {topic} — [Edit Post]({post.get('edit_url')})")
                        else:
                            st.write(f"⚠️ **[{idx}/{len(titles)}] Failed:** {topic}")
                            
                        batch_progress.progress(int(idx / len(titles) * 100))
                        
                        if idx < len(titles):
                            time.sleep(5)  # Cooldown
                            
                    batch_status.success("🏁 All batch titles processed successfully!")
                else:
                    st.error(f"Could not load Google Sheet (HTTP {resp.status_code}). Ensure link sharing is set to 'Anyone with the link can view'.")
            except Exception as e:
                st.error(f"Error processing sheet: {e}")

    with tab_inspect:
        st.subheader("🔍 WordPress Post Meta & Schema Inspector")
        st.markdown("Inspect all raw metadata, categories, and content of any published or draft post via the WordPress REST API.")

        inspect_post_id = st.number_input("Enter WordPress Post ID to Inspect", min_value=1, value=7246, step=1)
        
        if st.button("🔎 Fetch Post Metadata", type="primary"):
            import requests
            from requests.auth import HTTPBasicAuth
            
            wp_url = os.getenv("WP_SITE_URL", "").rstrip('/')
            wp_user = os.getenv("WP_USERNAME")
            wp_pass = os.getenv("WP_APP_PASSWORD")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            with st.spinner(f"Fetching Post {inspect_post_id} from WordPress REST API..."):
                try:
                    resp = requests.get(
                        f"{wp_url}/wp-json/wp/v2/posts/{inspect_post_id}?context=edit",
                        auth=HTTPBasicAuth(wp_user, wp_pass),
                        headers=headers,
                        timeout=20
                    )
                    
                    if resp.status_code == 200:
                        post_json = resp.json()
                        st.success(f"✅ Successfully retrieved Post ID: **{inspect_post_id}**")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Post Status", post_json.get("status", "").upper())
                        col2.metric("Categories", str(post_json.get("categories", [])))
                        col3.metric("Featured Media ID", post_json.get("featured_media", 0))
                        
                        st.markdown(f"**Post Title:** `{post_json.get('title', {}).get('raw', '')}`")
                        st.markdown(f"**WordPress Edit URL:** [Open in Editor]({wp_url}/wp-admin/post.php?post={inspect_post_id}&action=edit)")
                        
                        st.divider()
                        st.subheader("1. Registered Post Meta in WordPress Database:")
                        st.json(post_json.get("meta", {}))
                        
                        st.divider()
                        st.subheader("2. Body Content Check (Verification for Clean Body):")
                        raw_content = post_json.get("content", {}).get("raw", "")
                        if "<script" in raw_content:
                            st.warning("⚠️ <script> tags detected in body content.")
                        else:
                            st.success("✅ Clean Body: Zero <script> tags inside post body content.")
                            
                        with st.expander("View Full Raw Body Content"):
                            st.code(raw_content, language="html")
                            
                    else:
                        st.error(f"❌ Failed to fetch Post ID {inspect_post_id}. HTTP Status: {resp.status_code} - {resp.text}")
                except Exception as e:
                    st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
