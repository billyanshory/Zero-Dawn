import os
import sys
from dotenv import load_dotenv

# Load env variables FIRST before any other logic
load_dotenv()

# Validate crucial environment variables
REQUIRED_VARS = ["DATABASE_URL", "LLM_API_KEY", "LLM_MODEL_NAME", "APP_SECRET", "SANIC_ENV"]
for var in REQUIRED_VARS:
    if not os.getenv(var):
        raise RuntimeError(f"FATAL: {var} is not set in .env. GambitHunter cannot start without it.")

import re
import json
import uuid
import logging
import asyncio
import traceback
import html
from datetime import datetime, timezone
import urllib.parse
from contextlib import asynccontextmanager

from sanic import Sanic, response, Request
from sanic.exceptions import SanicException, NotFound, InvalidUsage, ServerError

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, Integer, Float, DateTime, Boolean, func, select, desc

from jinja2 import Environment, BaseLoader

from playwright.async_api import async_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import langchain_core.exceptions

# Determine LLM Provider
llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
if llm_provider == "anthropic":
    from langchain_anthropic import ChatAnthropic as LLMClass
else:
    from langchain_openai import ChatOpenAI as LLMClass

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
sanic_env = os.getenv("SANIC_ENV", "production")
log_level = logging.DEBUG if sanic_env == "development" else logging.INFO

logger = logging.getLogger("gambithunter")
logger.setLevel(log_level)
formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(stream_handler)
logger.propagate = False

# -----------------------------------------------------------------------------
# APP CONFIG
# -----------------------------------------------------------------------------
app = Sanic("GambitHunter")
app.config.FALLBACK_ERROR_FORMAT = "json"
app.config.REQUEST_TIMEOUT = 120
app.config.RESPONSE_TIMEOUT = 120
app.config.REQUEST_MAX_SIZE = 1_000_000
if sanic_env == "development":
    @app.middleware('response')
    def allow_cors(request, response):
        response.headers['Access-Control-Allow-Origin'] = '*'
else:
    @app.middleware('response')
    def allow_cors(request, response):
        # Limit to expected production domains if needed
        response.headers['Access-Control-Allow-Origin'] = 'https://gambithunter.id'

# -----------------------------------------------------------------------------
# DATABASE LAYER
# -----------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

engine_kwargs = {
    "echo": False
}

if "sqlite" not in DATABASE_URL:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
        "connect_args": {"server_settings": {"application_name": "gambithunter"}},
    })

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@asynccontextmanager
async def get_db_session():
    session = async_session_factory()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {str(e)}", exc_info=True)
        await session.rollback()
        raise
    finally:
        await session.close()

class Base(DeclarativeBase):
    pass

class ScanLog(Base):
    __tablename__ = "scan_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    target_url: Mapped[str] = mapped_column(String)
    verdict: Mapped[str] = mapped_column(String, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    evidence_snippet: Mapped[str] = mapped_column(Text, nullable=True)
    raw_page_text: Mapped[str] = mapped_column(Text, nullable=True)
    llm_raw_response: Mapped[str] = mapped_column(Text, nullable=True)
    scan_status: Mapped[str] = mapped_column(String, default="completed")
    error_message: Mapped[str] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

@app.before_server_start
async def setup_db(app, loop):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created successfully")

@app.after_server_stop
async def teardown_db(app, loop):
    await engine.dispose()
    logger.info("Database engine disposed, all connections closed")

# -----------------------------------------------------------------------------
# CORE LOGIC
# -----------------------------------------------------------------------------
def validate_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty.")

    if not url.startswith("http://") and not url.startswith("https://"):
        if re.match(r'^[^/]+\.[^/]+', url):
            url = "https://" + url
        else:
            raise ValueError("URL must start with http:// or https://")

    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid URL structure.")

    if parsed.username or parsed.password:
        raise ValueError("The URL contains embedded credentials (user:password@host), which is not permitted for security reasons.")

    if len(url) > 2048:
        raise ValueError("URL is too long (maximum 2048 characters).")

    if parsed.scheme not in ["http", "https"]:
        raise ValueError(f"Scheme '{parsed.scheme}' is not permitted.")

    # Extremely basic IP block check (socket resolution could be added but might block async loop, rely on string matching for IPs here)
    host = parsed.hostname
    if host:
        blocked_ips = [
            "127.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.", "192.168.", "169.254."
        ]
        if any(host.startswith(prefix) for prefix in blocked_ips) or host == "localhost" or ":" in host: # simple ipv6 block
            raise ValueError("Private or loopback IP addresses are not permitted.")

    return url

async def scrape_url_with_playwright(url: str) -> str:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                    "--disable-gpu", "--disable-extensions", "--disable-background-networking",
                    "--disable-sync", "--disable-translate", "--no-first-run", "--disable-infobars"
                ]
            )
            try:
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    java_script_enabled=True,
                    ignore_https_errors=False,
                    locale="id-ID"
                )
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2.5) # Buffer for late rendering

                text_content = await page.evaluate("() => document.body.innerText")
                page_title = await page.title()

                full_text = f"Page Title: {page_title}\n\n{text_content}"
                full_text = re.sub(r'\s+', ' ', full_text).strip()
                full_text = full_text[:15000]
                return full_text
            finally:
                await browser.close()
    except PlaywrightTimeoutError as e:
        logger.warning(f"Playwright navigation failed for URL={url}: TimeoutError after 30s")
        raise Exception("The target website did not respond within 30 seconds. It may be offline or blocking automated access.")
    except PlaywrightError as e:
        logger.warning(f"Playwright error for URL={url}: {str(e)}")
        raise Exception("Failed to render the target website. The site may use advanced bot detection or require interaction that automated scanning cannot provide.")
    except Exception as e:
        logger.error(f"Unexpected error in scrape_url_with_playwright for URL={url}", exc_info=True)
        raise Exception("An unexpected error occurred during website scanning. The technical team has been notified.")

async def analyze_text_with_llm(extracted_text: str) -> dict:
    system_prompt = (
        "You are a highly specialized Indonesian cyber forensics analyst. Your sole mission is to analyze the provided text extracted from a website and determine whether the website is an illegal online gambling operation (known in Indonesia as 'judol' or 'judi online'). You must look for the following categories of indicators: (1) Primary gambling keywords in Indonesian: 'slot', 'gacor', 'maxwin', 'scatter', 'depo', 'deposit', 'withdraw', 'wd', 'rtp', 'jackpot', 'pragmatic', 'pg soft', 'habanero', 'joker', 'togel', 'toto', 'bandar', 'taruhan', 'sbobet', 'parlay', 'live casino', 'baccarat', 'roulette', 'poker online', 'daftar slot', 'login slot', 'link alternatif', 'bonus new member', 'bonus deposit', 'turnover'; (2) Pattern indicators such as references to minimum deposits (e.g., 'depo 10rb', 'minimal deposit'), promises of winning or easy money ('menang mudah', 'kemenangan pasti', 'cuan', 'jp', 'pola gacor'), fake testimonials with screenshots of winnings, WhatsApp or Telegram contact numbers for 'customer service', references to payment via Indonesian bank transfers or e-wallets (Dana, OVO, GoPay, LinkAja, QRIS) specifically in a gambling context; (3) Structural indicators such as the presence of multiple game provider logos, 'live RTP' tables showing return-to-player percentages, registration/login forms combined with deposit instructions, domain names containing gambling-related words. Analyze the text holistically. A website selling legitimate slot car toys or a financial website discussing investment returns should NOT be flagged. Context matters. You must respond with ONLY a valid JSON object and absolutely nothing else — no markdown, no explanation, no preamble, no commentary. The JSON must have exactly three fields: 'verdict' (string, either 'JUDOL' or 'AMAN' — use 'JUDOL' if the site is identified as illegal gambling, 'AMAN' if it appears to be a legitimate website), 'confidence' (integer from 0 to 100 representing your confidence percentage in the verdict), and 'evidence' (string, a brief excerpt of the most damning text that supports your verdict, or a note explaining why the site appears legitimate). If you cannot determine the nature of the site with confidence, default to 'AMAN' with a low confidence score and explain your uncertainty in the evidence field."
    )

    safe_default = {"verdict": "AMAN", "confidence": 0, "evidence": "LLM response was malformed; defaulting to safe verdict for manual review."}

    try:
        kwargs = {
            "api_key": os.getenv("LLM_API_KEY"),
            "model": os.getenv("LLM_MODEL_NAME"),
            "temperature": 0.0,
            "max_tokens": 1000
        }
        if os.getenv("LLM_BASE_URL"):
            kwargs["base_url"] = os.getenv("LLM_BASE_URL")

        llm = LLMClass(**kwargs)
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Analyze the following website text and determine if it is an illegal gambling site:\n\n{text}")
        ])
        chain = prompt | llm | JsonOutputParser()
        result = await chain.ainvoke({"text": extracted_text})

        if not isinstance(result, dict) or not all(k in result for k in ("verdict", "confidence", "evidence")):
            logger.warning(f"Malformed LLM output missing keys: {result}")
            return safe_default

        if result["verdict"] not in ["JUDOL", "AMAN"]:
            logger.warning(f"Malformed LLM output verdict value: {result.get('verdict')}")
            return safe_default

        if not isinstance(result["confidence"], (int, float)) or not (0 <= result["confidence"] <= 100):
            logger.warning(f"Malformed LLM output confidence value: {result.get('confidence')}")
            return safe_default

        return result

    except langchain_core.exceptions.OutputParserException as e:
        logger.warning(f"LLM JSON parse error: {str(e)}")
        return safe_default
    except json.JSONDecodeError as e:
        logger.warning(f"LLM Manual parse error: {str(e)}")
        return safe_default
    except TimeoutError as e:
        logger.warning(f"LLM Timeout error: {str(e)}")
        return safe_default
    except ConnectionError as e:
        logger.warning(f"LLM Connection error: {str(e)}")
        return safe_default
    except Exception as e:
        logger.error("Unexpected error in analyze_text_with_llm", exc_info=True)
        return safe_default

def generate_forensic_pdf(scan_data: dict) -> bytes:
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(name="TitleStyle", parent=styles['Heading1'], fontName="Helvetica-Bold", fontSize=16, alignment=1)
        subtitle_style = ParagraphStyle(name="SubtitleStyle", parent=styles['Normal'], fontName="Helvetica-Oblique", fontSize=12, alignment=1)
        normal_style = styles['Normal']

        verdict_color = HexColor("#e85d5d") if scan_data.get("verdict") == "JUDOL" else HexColor("#5dba7d")
        verdict_style = ParagraphStyle(name="VerdictStyle", parent=styles['Heading2'], fontName="Helvetica-Bold", fontSize=14, textColor=verdict_color)

        evidence_style = ParagraphStyle(name="EvidenceStyle", parent=styles['Normal'], fontName="Courier", fontSize=10, backColor=HexColor("#f0f0f0"), borderPadding=5)

        elements = []

        elements.append(Paragraph("LAPORAN FORENSIK DIGITAL — GAMBITHUNTER", title_style))
        elements.append(Paragraph("Berita Acara Pemeriksaan (BAP) Digital", subtitle_style))
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(HRFlowable(width="100%", thickness=1, color="black"))
        elements.append(Spacer(1, 0.2 * inch))

        # Convert created_at to WITA (UTC+8)
        created_at = scan_data.get("created_at")
        if isinstance(created_at, datetime):
            # The database timezone is UTC, manually add 8 hours
            import datetime as dt
            created_at = (created_at + dt.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        else:
            created_at = str(created_at) if created_at else "Unknown"

        elements.append(Paragraph(f"<b>Scan ID:</b> {scan_data.get('scan_id')}", normal_style))
        elements.append(Paragraph(f"<b>Target URL:</b> {html.escape(scan_data.get('target_url', ''))}", normal_style))
        elements.append(Paragraph(f"<b>Timestamp (WITA):</b> {created_at}", normal_style))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(f"VERDICT: {scan_data.get('verdict')} ({scan_data.get('confidence')}%)", verdict_style))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph("<b>Bukti Teks (Evidence):</b>", normal_style))
        elements.append(Spacer(1, 0.1 * inch))

        # Clean evidence to avoid platypus parse errors if text has weird chars
        evidence = html.escape(scan_data.get("evidence_snippet", "None"))
        elements.append(Paragraph(evidence, evidence_style))
        elements.append(Spacer(1, 0.4 * inch))

        elements.append(HRFlowable(width="100%", thickness=1, color="black"))
        elements.append(Spacer(1, 0.1 * inch))

        footer_text = ("<i>Disclaimer: This report was generated automatically by GambitHunter and should be "
                       "verified by qualified forensic analysts before being used as legal evidence. "
                       f"Report ID: {scan_data.get('scan_id')}</i>")
        elements.append(Paragraph(footer_text, normal_style))

        doc.build(elements)
        return buffer.getvalue()
    except Exception as e:
        logger.error("Failed to generate PDF", exc_info=True)
        raise RuntimeError("Gagal membuat dokumen PDF.")

# -----------------------------------------------------------------------------
# TEMPLATES
# -----------------------------------------------------------------------------
jinja_env = Environment(loader=BaseLoader(), autoescape=True)

MAIN_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="GambitHunter - Pemburu Judol di Samarinda">
    <meta name="theme-color" content="#1a1a1a">
    <title>GambitHunter</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2a2a2a;
            --border-color: #3a3a3a;
            --text-primary: #e8e8e8;
            --text-secondary: #a0a0a0;
            --accent: #d4a574;
            --accent-hover: #e0b584;
            --danger: #e85d5d;
            --safe: #5dba7d;
            --radius-container: 12px;
            --radius-element: 8px;
        }
        body {
            font-family: 'Inter', -apple-system, system-ui, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            margin: 0;
            padding: 0;
            line-height: 1.6;
            font-size: 16px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        header {
            text-align: center;
            margin-bottom: 40px;
        }
        h1 {
            font-size: 2.5rem;
            margin: 0 0 10px 0;
            color: var(--text-primary);
        }
        .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        .search-box {
            display: flex;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-element);
            padding: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            transition: border-color 0.3s;
        }
        .search-box:focus-within {
            border-color: var(--accent);
        }
        .search-input {
            flex-grow: 1;
            background: transparent;
            border: none;
            color: var(--text-primary);
            padding: 15px;
            font-size: 1rem;
            outline: none;
        }
        .search-btn {
            background: var(--accent);
            color: var(--bg-primary);
            border: none;
            border-radius: var(--radius-element);
            padding: 0 20px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .search-btn:hover:not(:disabled) {
            background: var(--accent-hover);
        }
        .search-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }
        .spinner {
            width: 20px;
            height: 20px;
            border: 3px solid rgba(26,26,26,0.3);
            border-top-color: var(--bg-primary);
            border-radius: 50%;
            animation: rotate 1s linear infinite;
            display: none;
        }
        @keyframes rotate { to { transform: rotate(360deg); } }

        .progress-section {
            text-align: center;
            margin-top: 20px;
            color: var(--text-secondary);
            height: 24px;
            display: none;
        }
        .progress-msg {
            animation: fadeIn 0.5s;
        }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

        .result-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-container);
            padding: 24px;
            margin-top: 30px;
            display: none;
            transform: translateY(20px);
            opacity: 0;
            transition: all 0.5s ease;
        }
        .result-card.show {
            transform: translateY(0);
            opacity: 1;
            display: block;
        }
        .verdict-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: var(--radius-element);
            font-weight: bold;
            font-size: 1.2rem;
            margin-bottom: 15px;
        }
        .judol { background: rgba(232, 93, 93, 0.1); color: var(--danger); border: 1px solid var(--danger); }
        .aman { background: rgba(93, 186, 125, 0.1); color: var(--safe); border: 1px solid var(--safe); }

        .progress-bar-bg {
            background: var(--border-color);
            border-radius: 4px;
            height: 8px;
            width: 100%;
            margin: 10px 0;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            transition: width 1s ease;
        }
        .evidence-box {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: var(--radius-element);
            font-family: monospace;
            color: var(--text-secondary);
            margin: 15px 0;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .download-btn {
            display: inline-block;
            background: var(--bg-primary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: 10px 20px;
            border-radius: var(--radius-element);
            text-decoration: none;
            margin-top: 15px;
            transition: border-color 0.3s;
        }
        .download-btn:hover { border-color: var(--text-primary); }

        .history-section {
            margin-top: 60px;
        }
        .history-item {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-element);
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        @media (max-width: 600px) {
            .history-item { flex-direction: column; align-items: flex-start; gap: 10px; }
        }
        .history-url {
            color: var(--text-primary);
            text-decoration: none;
            word-break: break-all;
        }
        .history-meta {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        .history-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .err-msg {
            color: var(--danger);
            margin-top: 10px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>GambitHunter</h1>
            <div class="subtitle">Pemburu Judol di Samarinda — Forensik Digital Otomatis</div>
        </header>

        <main>
            <div class="search-box">
                <input type="text" id="urlInput" class="search-input" placeholder="Paste URL yang mencurigakan di sini...">
                <button id="scanBtn" class="search-btn">
                    <span id="btnText">Scan</span>
                    <div id="spinner" class="spinner"></div>
                </button>
            </div>
            <div id="errMsg" class="err-msg"></div>

            <div id="progressSection" class="progress-section">
                <div id="progressMsg" class="progress-msg"></div>
            </div>

            <div id="resultCard" class="result-card">
                <div id="verdictBadge" class="verdict-badge"></div>
                <div>Confidence: <span id="confText"></span></div>
                <div class="progress-bar-bg">
                    <div id="confBar" class="progress-bar-fill"></div>
                </div>
                <div class="evidence-box" id="evidenceBox"></div>
                <a href="#" id="downloadBtn" class="download-btn">Download Laporan PDF</a>
            </div>

            <div class="history-section">
                <h3>Riwayat Pemindaian Terbaru</h3>
                <div id="historyContainer">
                    {% for item in history %}
                    <div class="history-item">
                        <div>
                            <a href="/scan/{{ item.scan_id }}" class="history-url">{{ item.target_url }}</a>
                            <div class="history-meta">{{ item.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</div>
                        </div>
                        <div>
                            {% if item.verdict == 'JUDOL' %}
                                <span class="history-badge judol">JUDOL ({{ item.confidence|int }}%)</span>
                            {% elif item.verdict == 'AMAN' %}
                                <span class="history-badge aman">AMAN ({{ item.confidence|int }}%)</span>
                            {% else %}
                                <span class="history-badge" style="background:#333">{{ item.scan_status }}</span>
                            {% endif %}
                        </div>
                    </div>
                    {% else %}
                    <p style="color:var(--text-secondary)">Belum ada riwayat pemindaian.</p>
                    {% endfor %}
                </div>
            </div>
        </main>
    </div>

    <script>
        const scanBtn = document.getElementById('scanBtn');
        const urlInput = document.getElementById('urlInput');
        const spinner = document.getElementById('spinner');
        const btnText = document.getElementById('btnText');
        const progressSection = document.getElementById('progressSection');
        const progressMsg = document.getElementById('progressMsg');
        const resultCard = document.getElementById('resultCard');
        const verdictBadge = document.getElementById('verdictBadge');
        const confText = document.getElementById('confText');
        const confBar = document.getElementById('confBar');
        const evidenceBox = document.getElementById('evidenceBox');
        const downloadBtn = document.getElementById('downloadBtn');
        const errMsg = document.getElementById('errMsg');

        const phases = [
            "Menginisialisasi browser forensik...",
            "Memindai konten website...",
            "Menganalisis dengan AI forensik...",
            "Menyusun laporan..."
        ];

        let phaseInterval;

        scanBtn.addEventListener('click', async () => {
            const url = urlInput.value.trim();
            if (!url) return;

            // Reset UI
            errMsg.style.display = 'none';
            resultCard.classList.remove('show');
            scanBtn.disabled = true;
            urlInput.disabled = true;
            btnText.style.display = 'none';
            spinner.style.display = 'block';
            progressSection.style.display = 'block';

            let phaseIdx = 0;
            progressMsg.innerText = phases[phaseIdx];
            phaseInterval = setInterval(() => {
                phaseIdx = Math.min(phaseIdx + 1, phases.length - 1);
                progressMsg.innerText = phases[phaseIdx];
            }, 5000);

            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Terjadi kesalahan sistem.');
                }

                clearInterval(phaseInterval);
                progressSection.style.display = 'none';

                // Display Result
                const isJudol = data.verdict === 'JUDOL';
                verdictBadge.className = 'verdict-badge ' + (isJudol ? 'judol' : 'aman');
                verdictBadge.innerText = data.verdict;

                confText.innerText = data.confidence + '%';
                confBar.style.width = data.confidence + '%';
                confBar.style.backgroundColor = isJudol ? 'var(--danger)' : 'var(--safe)';

                evidenceBox.innerText = data.evidence_snippet;
                downloadBtn.href = '/api/scan/' + data.scan_id + '/pdf';

                resultCard.classList.add('show');

            } catch (error) {
                clearInterval(phaseInterval);
                progressSection.style.display = 'none';
                errMsg.innerText = error.message;
                errMsg.style.display = 'block';
            } finally {
                scanBtn.disabled = false;
                urlInput.disabled = false;
                btnText.style.display = 'block';
                spinner.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

RESULT_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Detail Scan - GambitHunter</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2a2a2a;
            --border-color: #3a3a3a;
            --text-primary: #e8e8e8;
            --text-secondary: #a0a0a0;
            --accent: #d4a574;
            --danger: #e85d5d;
            --safe: #5dba7d;
        }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            margin: 0; padding: 40px 20px; line-height: 1.6;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 30px;
        }
        h2 { margin-top: 0; }
        .badge {
            display: inline-block; padding: 8px 16px; border-radius: 8px; font-weight: bold; font-size: 1.2rem; margin-bottom: 20px;
        }
        .judol { background: rgba(232, 93, 93, 0.1); color: var(--danger); border: 1px solid var(--danger); }
        .aman { background: rgba(93, 186, 125, 0.1); color: var(--safe); border: 1px solid var(--safe); }
        .evidence {
            background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; font-family: monospace; color: var(--text-secondary); white-space: pre-wrap; word-break: break-all; margin: 20px 0;
        }
        .btn {
            display: inline-block; background: var(--bg-primary); color: var(--text-primary); border: 1px solid var(--border-color); padding: 10px 20px; border-radius: 8px; text-decoration: none;
        }
        .btn:hover { border-color: var(--text-primary); }
        .meta { color: var(--text-secondary); margin-bottom: 20px; }
        a.back { color: var(--accent); text-decoration: none; margin-bottom: 20px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back">← Kembali ke Utama</a>
        <div class="card">
            <h2>Hasil Analisis Forensik</h2>
            <div class="meta">
                <div><strong>Scan ID:</strong> {{ item.scan_id }}</div>
                <div><strong>Target:</strong> {{ item.target_url }}</div>
                <div><strong>Waktu:</strong> {{ item.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</div>
            </div>

            {% if item.verdict == 'JUDOL' %}
                <div class="badge judol">JUDOL ({{ item.confidence|int }}%)</div>
            {% else %}
                <div class="badge aman">AMAN ({{ item.confidence|int }}%)</div>
            {% endif %}

            <h3>Bukti Teks:</h3>
            <div class="evidence">{{ item.evidence_snippet }}</div>

            <a href="/api/scan/{{ item.scan_id }}/pdf" class="btn">Download Laporan PDF</a>
        </div>
    </div>
</body>
</html>
"""

# -----------------------------------------------------------------------------
# MIDDLEWARE & RATE LIMITING
# -----------------------------------------------------------------------------
rate_limit_store = {}

@app.on_request
async def attach_request_id(request: Request):
    request.ctx.request_id = str(uuid.uuid4())

@app.on_response
async def apply_security_headers(request: Request, response):
    if response:
        response.headers["X-Request-ID"] = request.ctx.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

# Periodic rate limit cleanup
async def cleanup_rate_limits():
    while True:
        await asyncio.sleep(600)
        now = datetime.now().timestamp()
        for ip in list(rate_limit_store.keys()):
            rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < 60]
            if not rate_limit_store[ip]:
                del rate_limit_store[ip]

@app.before_server_start
async def start_background_tasks(app, loop):
    app.add_task(cleanup_rate_limits())

def check_rate_limit(ip: str):
    now = datetime.now().timestamp()
    if ip not in rate_limit_store:
        rate_limit_store[ip] = []

    # Clean old ones inline for this IP
    rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < 60]

    if len(rate_limit_store[ip]) >= 10:
        return False
    rate_limit_store[ip].append(now)
    return True

# -----------------------------------------------------------------------------
# ERROR HANDLERS
# -----------------------------------------------------------------------------
@app.exception(SanicException)
async def handle_sanic_exception(request, exception):
    status_code = getattr(exception, "status_code", 500)
    return response.json({"error": str(exception)}, status=status_code)

@app.exception(Exception)
async def handle_generic_exception(request, exception):
    req_id = getattr(request.ctx, "request_id", "unknown")
    logger.critical(f"Unhandled Exception [Req: {req_id}]: {str(exception)}", exc_info=True)
    return response.json({"error": "An internal server error occurred."}, status=500)

@app.exception(NotFound)
async def handle_not_found(request, exception):
    if "application/json" in request.headers.get("accept", ""):
        return response.json({"error": "Resource not found."}, status=404)
    return response.html("<h1>404 Not Found</h1>", status=404)

# -----------------------------------------------------------------------------
# ROUTES
# -----------------------------------------------------------------------------
@app.get("/")
async def index_page(request: Request):
    async with get_db_session() as session:
        try:
            result = await session.execute(
                select(ScanLog).where(ScanLog.scan_status == "completed").order_by(desc(ScanLog.created_at)).limit(20)
            )
            history = result.scalars().all()
        except Exception as e:
            logger.error("Failed to fetch history for index", exc_info=True)
            history = []

    template = jinja_env.from_string(MAIN_PAGE_TEMPLATE)
    html_content = template.render(history=history)
    return response.html(html_content)

@app.post("/api/scan")
async def api_scan(request: Request):
    ip = request.remote_addr or request.ip
    if not check_rate_limit(ip):
        return response.json({"error": "Rate limit exceeded. Please try again later."}, status=429, headers={"Retry-After": "60"})

    req_data = request.json or {}
    raw_url = req_data.get("url", "")

    try:
        valid_url = validate_url(raw_url)
    except ValueError as e:
        return response.json({"error": str(e)}, status=400)

    scan_id = str(uuid.uuid4())

    async with get_db_session() as session:
        log_entry = ScanLog(
            scan_id=scan_id,
            target_url=valid_url,
            scan_status="pending"
        )
        session.add(log_entry)
        await session.commit()

        try:
            log_entry.scan_status = "scanning"
            await session.commit()

            scraped_text = await scrape_url_with_playwright(valid_url)
            log_entry.raw_page_text = scraped_text

            log_entry.scan_status = "analyzing"
            await session.commit()

            analysis = await analyze_text_with_llm(scraped_text)

            log_entry.verdict = analysis.get("verdict")
            log_entry.confidence = float(analysis.get("confidence", 0))
            log_entry.evidence_snippet = analysis.get("evidence")
            log_entry.scan_status = "completed"

            await session.commit()

            return response.json({
                "scan_id": log_entry.scan_id,
                "target_url": log_entry.target_url,
                "verdict": log_entry.verdict,
                "confidence": log_entry.confidence,
                "evidence_snippet": log_entry.evidence_snippet,
                "status": log_entry.scan_status
            })

        except Exception as e:
            logger.error(f"Scan failed for {valid_url}: {str(e)}")
            log_entry.scan_status = "error"
            log_entry.error_message = str(e)
            await session.commit()

            status_code = 502 if "An unexpected error occurred" in str(e) else 500
            return response.json({"error": str(e)}, status=status_code)

def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

@app.get("/api/scan/<scan_id:str>")
async def get_api_scan(request: Request, scan_id: str):
    if not is_valid_uuid(scan_id):
        raise InvalidUsage("Invalid Scan ID format.")
    async with get_db_session() as session:
        result = await session.execute(select(ScanLog).where(ScanLog.scan_id == scan_id))
        scan = result.scalars().first()
        if not scan:
            raise NotFound("Scan ID not found")

        return response.json({
            "scan_id": scan.scan_id,
            "target_url": scan.target_url,
            "verdict": scan.verdict,
            "confidence": scan.confidence,
            "evidence_snippet": scan.evidence_snippet,
            "status": scan.scan_status,
            "error_message": scan.error_message,
            "created_at": scan.created_at.isoformat() if scan.created_at else None
        })

@app.get("/scan/<scan_id:str>")
async def view_scan(request: Request, scan_id: str):
    if not is_valid_uuid(scan_id):
        raise NotFound("Scan ID not found")
    async with get_db_session() as session:
        result = await session.execute(select(ScanLog).where(ScanLog.scan_id == scan_id))
        scan = result.scalars().first()
        if not scan:
            raise NotFound("Scan ID not found")

        template = jinja_env.from_string(RESULT_PAGE_TEMPLATE)
        html_content = template.render(item=scan)
        return response.html(html_content)

@app.get("/api/scan/<scan_id:str>/pdf")
async def get_pdf(request: Request, scan_id: str):
    if not is_valid_uuid(scan_id):
        raise InvalidUsage("Invalid Scan ID format.")
    async with get_db_session() as session:
        result = await session.execute(select(ScanLog).where(ScanLog.scan_id == scan_id))
        scan = result.scalars().first()
        if not scan:
            raise NotFound("Scan ID not found")

        if scan.scan_status != "completed":
            return response.json({"error": "Report not complete or failed."}, status=400)

        scan_data = {
            "scan_id": scan.scan_id,
            "target_url": scan.target_url,
            "verdict": scan.verdict,
            "confidence": scan.confidence,
            "evidence_snippet": scan.evidence_snippet,
            "created_at": scan.created_at.strftime('%Y-%m-%d %H:%M:%S') if scan.created_at else "Unknown"
        }

        pdf_bytes = generate_forensic_pdf(scan_data)

        return response.raw(
            pdf_bytes,
            content_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=GambitHunter_Report_{scan_id}.pdf"}
        )

@app.get("/api/history")
async def api_history(request: Request):
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        if page < 1 or per_page < 1 or per_page > 100:
            raise ValueError()
    except ValueError:
        return response.json({"error": "Invalid pagination parameters."}, status=400)

    offset = (page - 1) * per_page

    async with get_db_session() as session:
        count_res = await session.execute(select(func.count(ScanLog.id)))
        total_count = count_res.scalar_one()

        result = await session.execute(
            select(ScanLog).order_by(desc(ScanLog.created_at)).offset(offset).limit(per_page)
        )
        logs = result.scalars().all()

        return response.json({
            "items": [{
                "scan_id": log.scan_id,
                "target_url": log.target_url,
                "verdict": log.verdict,
                "status": log.scan_status,
                "created_at": log.created_at.isoformat() if log.created_at else None
            } for log in logs],
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page,
            "has_next": (offset + per_page) < total_count,
            "has_prev": page > 1
        })

@app.get("/health")
async def health_check(request: Request):
    try:
        async with engine.connect() as conn:
            await conn.execute(select(1))
        return response.json({"status": "healthy", "database": "connected", "timestamp": datetime.now(timezone.utc).isoformat()})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return response.json({"status": "unhealthy", "database": "disconnected", "error": str(e)}, status=503)

# -----------------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    debug = sanic_env == "development"
    auto_reload = debug
    workers = int(os.getenv("APP_WORKERS", "1"))

    logger.info(f"Starting GambitHunter on {host}:{port} with {workers} workers. Debug: {debug}")

    app.run(
        host=host,
        port=port,
        debug=debug,
        auto_reload=auto_reload,
        workers=workers,
        access_log=debug
    )
