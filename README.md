# 🚗 Automated WordPress SEO Publisher & Media Pipeline

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![WordPress](https://img.shields.io/badge/WordPress-REST%20API-0073AA.svg)](https://developer.wordpress.org/rest-api/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991.svg)](https://openai.com/)
[![Pillow](https://img.shields.io/badge/Pillow-Image_Engine-green.svg)](https://python-pillow.org/)
[![Deployment](https://img.shields.io/badge/Streamlit_Cloud-Ready-brightgreen.svg)]()

A complete, enterprise-grade automated content publishing and media branding pipeline built with **Python**, **Streamlit**, **OpenAI (GPT-4o)**, and the **WordPress REST API**.

Designed for collision repair centers and high-authority niche businesses, this turnkey system automates long-form SEO blog drafting (1,200+ words), dynamic branded image generation using real workshop photography, Yoast SEO metadata configuration, and direct WordPress Draft publishing.

---

## 📑 Table of Contents

1. [Executive Summary & Value Proposition](#-executive-summary--value-proposition)
2. [Key Capabilities & Architecture](#-key-capabilities--architecture)
3. [Dashboard Features](#-dashboard-features)
4. [Project Structure](#-project-structure)
5. [Local Installation & Setup Guide](#-local-installation--setup-guide)
6. [How to Deploy to Streamlit Cloud](#-how-to-deploy-to-streamlit-cloud)
7. [WordPress Application Password Setup](#-wordpress-application-password-setup)
8. [Client Customization & Maintenance](#-client-customization--maintenance)
9. [Troubleshooting & Support](#-troubleshooting--support)

---

## 🌟 Executive Summary & Value Proposition

Publishing consistent, high-ranking SEO content typically requires hours of manual research, drafting, image editing, internal linking, and metadata entry.

This application provides a **zero-touch, one-click automated workflow**:
- **1,200+ Word Comprehensive Articles**: Drafted using GPT-4o with strict human-tone guidelines, question-based `<h2 class="h2dav">` headings, and 3–4 detailed paragraphs per section.
- **Branded Image Generation**: Automatically selects 3 real workshop photos from the local gallery, applies a sleek 50% opacity top-15% banner overlay, and centers the post title in bold white typography.
- **Strict Draft Status**: Every post is created in WordPress with `status: 'draft'` so editorial teams can review before going live.
- **Full SEO & Schema Integration**: Yoast SEO title, dynamic phone call-to-action meta description, interactive FAQ accordion HTML, and valid Google JSON-LD schema markup.

---

## ✨ Key Capabilities & Architecture

```
┌─────────────────┐       ┌─────────────────┐       ┌──────────────────┐
│   Streamlit     │  ───> │  OpenAI GPT-4o  │  ───> │  Pillow Image    │
│   Web / Batch   │       │  Content & FAQs │       │  Branding Engine │
└─────────────────┘       └─────────────────┘       └──────────────────┘
                                                              │
                                                              ▼
┌─────────────────┐       ┌─────────────────┐       ┌──────────────────┐
│  WordPress Post │  <─── │  Yoast SEO &    │  <─── │  WordPress Media │
│  Draft (ID:...) │       │  Schema Binding │       │  Library Upload  │
└─────────────────┘       └─────────────────┘       └──────────────────┘
```

### 1. 🤖 AI Content & FAQ Engine (`generator.py`)
- Generates 1,200+ words with 3–4 paragraphs under every H2.
- Adheres to natural, active voice without robotic clichés or em dashes.
- Generates 12 curated, certified collision repair FAQs with exactly 3 sentences per answer.
- Generates Google-compliant JSON-LD FAQ schema `<script>` markup for search engine rich snippets.

### 2. 🎨 Dynamic Branded Photo Engine (`image_maker.py`)
- Scans the local `images/` directory and randomly selects 3 real workshop/car photos.
- **RGBA Compositing Fix**: Converts base images to RGBA to preserve 100% of the photo's original vibrancy.
- Applies a **50% opacity black rectangle (`alpha 128`)** across **ONLY the top 15%** of the image.
- Dynamically calculates font size using `Montserrat-Black.ttf` to center the title in pure white text with a subtle drop shadow.
- Directly uploads to the WordPress Media Library and automatically cleans up local temporary files.

### 3. ⚙️ SEO & HTML Sanitization (`processor.py`)
- Strips markdown asterisks and hash tags for clean HTML body content.
- Evenly distributes 7 client shortcodes across the article.
- Injects 3–4 relevant internal links with fallback routing.
- Generates a compelling Yoast meta description containing the direct phone CTA: `(747) 444-0040`.

### 4. 🔌 WordPress REST API Publishing Client (`wp_publisher.py`)
- Uploads images to `/wp-json/wp/v2/media` and sets alt text, title, and captions.
- Automatically resolves and binds the target WordPress Category (defaults to `Guides` / ID 4).
- Creates posts with `status: 'draft'`, binds `featured_media`, and populates Yoast postmeta.
- Executes secondary force-update requests to populate theme-specific gallery and schema boxes.

---

## 🖥️ Dashboard Features

The Streamlit dashboard (`app.py`) provides three intuitive workspaces:

1. **⚡ Single Post Generator**:
   - Enter any topic or keyword (e.g., *"How to Handle California Auto Insurance Claims After an Accident"*).
   - Select the target category.
   - Click **Generate & Publish Draft**.
   - Monitor real-time step-by-step progress.
   - Instantly access direct links to **Open Post in WordPress Editor** or **Open Post Preview**.

2. **📊 Batch Queue Runner**:
   - Connect any public or private Google Sheet containing pending topic titles.
   - Sequentially generates and publishes entire content calendars with automated cooldown delays.

3. **🔎 Post Meta Inspector**:
   - Enter any existing WordPress Post ID (e.g., `7406`) to query the live REST API.
   - Inspects raw post metadata, media bindings, categories, and custom theme fields.

---

## 📂 Project Structure

```text
wp-ai-seo-publisher/
├── app.py                  # Streamlit web application & user interface
├── generator.py            # OpenAI GPT-4o article & FAQ schema engine
├── processor.py            # HTML formatting, shortcode & link injector
├── image_maker.py          # Real photo selection & typography overlay engine
├── wp_publisher.py         # WordPress REST API publishing client
├── diagnose_post.py        # Diagnostic utility for post meta inspection
├── debug.py                # WordPress authentication tester
├── Montserrat-Black.ttf    # Typography font asset
├── images/                 # Gallery of real workshop & repair photos (50+ assets)
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variables configuration template
├── .gitignore              # Git ignore configuration (protects keys & venv)
└── README.md               # Project documentation
```

---

## ⚙️ Local Installation & Setup Guide

### 1. Prerequisites
- **Python 3.10 or higher** installed on your computer.
- An **OpenAI API Key** with access to GPT-4o.
- A **WordPress administrator/editor account** with REST API access.

### 2. Clone the Repository
```bash
git clone https://github.com/hitttu01/wp-ai-seo-publisher.git
cd wp-ai-seo-publisher
```

### 3. Create & Activate a Virtual Environment
```bash
# On macOS / Linux
python3 -m venv venv
source venv/bin/activate

# On Windows (Command Prompt / PowerShell)
python -m venv venv
venv\Scripts\activate
```

### 4. Install Package Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Local Environment Variables
Create your local `.env` file by copying the example template:

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-your_openai_api_key_here

# WordPress REST API Configuration
WP_SITE_URL=https://mycarautogroup.com
WP_USERNAME=your_wordpress_username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

# Optional Google Sheet ID for batch publishing
GOOGLE_SHEET_ID=1kieMk1araaWljeKZh4pxwteTtm6KGeqBAwdBRaw_meE
```

### 6. Launch the Application

Run the Streamlit web dashboard:

```bash
streamlit run app.py
```

The application will open automatically in your browser at **`http://localhost:8501`**.

*(To run the CLI batch script directly: `python main.py`)*

---

## ☁️ How to Deploy to Streamlit Cloud

You can deploy this application to **Streamlit Community Cloud** in under 3 minutes for free so your entire team or client can access it via a web link.

### Step 1: Push Repository to GitHub
Make sure your latest code is committed and pushed to GitHub:
```bash
git add .
git commit -m "feat: ready for cloud deployment"
git push origin main
```

### Step 2: Sign In to Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Sign in with your **GitHub account**.

### Step 3: Create a New App
1. Click the **"New app"** button.
2. Select your repository: `your-username/wp-ai-seo-publisher` (e.g., `hitttu01/wp-ai-seo-publisher`).
3. Set **Branch** to: `main`.
4. Set **Main file path** to: `app.py`.
5. Set your custom App URL (optional).

### Step 4: Configure Cloud Secrets (Crucial)
Before clicking deploy, configure your API credentials securely:
1. Click **"Advanced settings"** (or go to **App Settings** -> **Secrets** after creating).
2. In the **Secrets (TOML)** editor, paste your configuration:

```toml
OPENAI_API_KEY = "sk-proj-your_openai_api_key_here"
WP_SITE_URL = "https://mycarautogroup.com"
WP_USERNAME = "your_wordpress_username"
WP_APP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"
GOOGLE_SHEET_ID = "1kieMk1araaWljeKZh4pxwteTtm6KGeqBAwdBRaw_meE"
```

3. Click **"Save"** and **"Deploy"**.

### Step 5: Access Your Live Application
Streamlit Cloud will automatically build dependencies from `requirements.txt` and launch the app at your custom URL (e.g., `https://mycar-seo-publisher.streamlit.app`).

---

## 🔑 WordPress Application Password Setup

To authenticate securely without exposing your main password, WordPress uses **Application Passwords**:

1. Log in to your **WordPress Admin Dashboard**.
2. Navigate to **Users** -> **Profile** (or **All Users** -> click your user account).
3. Scroll down to the **Application Passwords** section.
4. Enter a recognizable name in the *New Application Password Name* field (e.g., `Streamlit Cloud Publisher`).
5. Click **Add New Application Password**.
6. Copy the generated 24-character string (e.g., `abcd efgh ijkl mnop qrst uvwx`).
7. Paste this string into your `.env` file or Streamlit Cloud Secrets under `WP_APP_PASSWORD`.

---

## 🛠️ Client Customization & Maintenance

### Adding New Photos
To add more shop photos to the automatic gallery rotation:
1. Simply drop your `.jpg`, `.jpeg`, or `.png` photo files into the [`images/`](file:///Users/hiteshyadav/Desktop/David/images) directory.
2. The image engine will automatically detect and include them in future randomized selections.

### Modifying Company Information or FAQs
- **Business Details & Tone Rules**: Edit `SYSTEM_PROMPT` in [`generator.py`](file:///Users/hiteshyadav/Desktop/David/generator.py).
- **Default FAQ Q&A Pairs**: Edit `FALLBACK_12_FAQS` in [`generator.py`](file:///Users/hiteshyadav/Desktop/David/generator.py).
- **Internal Links & Shortcodes**: Edit `INTERNAL_LINKS_POOL` and `SHORTCODES` in [`processor.py`](file:///Users/hiteshyadav/Desktop/David/processor.py).

---

## 🛡️ Troubleshooting & Support

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **HTTP 401 Unauthorized** | Invalid WordPress credentials or Application Password | Verify `WP_USERNAME` and recreate the Application Password in WP Admin. |
| **HTTP 403 Forbidden** | Cloudflare WAF or security plugin blocking script | The application includes desktop `User-Agent` headers automatically. Ensure your IP is not blocked by Wordfence/Cloudflare. |
| **OpenAI Quota Exceeded** | API credit balance is $0 or key expired | Check your billing balance at [platform.openai.com](https://platform.openai.com/account/billing). |
| **Category Not Found** | WordPress category slug mismatch | The publisher automatically resolves and creates the `Guides` category (ID 4) if missing. |

---

## 👥 Authors & Deliverable Handoff

- **Project Lead & Developer**: Hitesh Yadav
- **Client**: My Car Collision Center
- **Repository**: [wp-ai-seo-publisher](https://github.com/hitttu01/wp-ai-seo-publisher)
- **License**: Proprietary / Client Commercial License