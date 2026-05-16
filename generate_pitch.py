"""Generate EVALON 3-page hackathon submission PDF."""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import math

W, H = A4  # 595 x 842 pts

# ── Palette ─────────────────────────────────────────────────────────────────
BG        = HexColor("#13141a")
CARD      = HexColor("#1c1d25")
CARD2     = HexColor("#252630")
BORDER    = HexColor("#2d2e3a")
RED       = HexColor("#b1361e")
RED_LIGHT = HexColor("#e87060")
MUTED     = HexColor("#7e8088")
DIM       = HexColor("#5a5c66")
TEXT      = HexColor("#dddfe4")
TEXT2     = HexColor("#9a9ba8")
EMERALD   = HexColor("#34d399")
BLUE      = HexColor("#3b82f6")
PURPLE    = HexColor("#a78bfa")
YELLOW    = HexColor("#fbbf24")


def new_page(c: canvas.Canvas):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def header_bar(c: canvas.Canvas, title: str, subtitle: str, page: int):
    # Top bar
    c.setFillColor(CARD)
    c.rect(0, H - 52, W, 52, fill=1, stroke=0)
    # Red left accent
    c.setFillColor(RED)
    c.rect(0, H - 52, 4, 52, fill=1, stroke=0)
    # Logo wordmark
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(TEXT)
    c.drawString(18, H - 31, "EVAL")
    c.setFillColor(RED)
    c.drawString(57, H - 31, "ON")
    # Page title
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(TEXT)
    c.drawCentredString(W / 2, H - 32, title)
    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    c.drawCentredString(W / 2, H - 44, subtitle)
    # Page number
    c.setFont("Helvetica", 9)
    c.setFillColor(DIM)
    c.drawRightString(W - 16, H - 31, f"{page} / 3")


def footer(c: canvas.Canvas):
    c.setFillColor(CARD)
    c.rect(0, 0, W, 22, fill=1, stroke=0)
    c.setFont("Helvetica", 8)
    c.setFillColor(DIM)
    c.drawCentredString(W / 2, 7, "EVALON — AI-Powered Hackathon Evaluation Engine  |  Built with LangGraph · FastAPI · Next.js · Ollama")


def rounded_rect(c: canvas.Canvas, x, y, w, h, r=6, fill_color=CARD, stroke_color=BORDER, stroke_width=0.5):
    c.setFillColor(fill_color)
    c.setStrokeColor(stroke_color)
    c.setLineWidth(stroke_width)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1)


def label_pill(c: canvas.Canvas, x, y, text, bg=CARD2, fg=TEXT2, w=None):
    c.setFont("Helvetica", 8)
    tw = c.stringWidth(text, "Helvetica", 8)
    pw = (w or tw + 12)
    c.setFillColor(bg)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.4)
    c.roundRect(x, y, pw, 14, 3, fill=1, stroke=1)
    c.setFillColor(fg)
    c.drawCentredString(x + pw / 2, y + 4, text)
    return pw


def arrow_h(c, x1, y, x2, color=MUTED, head=5):
    c.setStrokeColor(color)
    c.setLineWidth(1)
    c.line(x1, y, x2, y)
    c.setFillColor(color)
    p = c.beginPath()
    p.moveTo(x2, y)
    p.lineTo(x2 - head, y + head * 0.55)
    p.lineTo(x2 - head, y - head * 0.55)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def arrow_v(c, x, y1, y2, color=MUTED, head=5):
    c.setStrokeColor(color)
    c.setLineWidth(1)
    c.line(x, y1, x, y2)
    c.setFillColor(color)
    p = c.beginPath()
    p.moveTo(x, y2)
    p.lineTo(x - head * 0.55, y2 + head)
    p.lineTo(x + head * 0.55, y2 + head)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def node_box(c, x, y, w, h, label, sublabel=None, color=CARD, accent=None, r=6):
    rounded_rect(c, x, y, w, h, r, fill_color=color, stroke_color=accent or BORDER)
    if accent:
        c.setFillColor(accent)
        c.roundRect(x, y + h - 3, w, 3, r, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(TEXT)
    if sublabel:
        c.drawCentredString(x + w / 2, y + h / 2 + 3, label)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(TEXT2)
        c.drawCentredString(x + w / 2, y + h / 2 - 7, sublabel)
    else:
        c.drawCentredString(x + w / 2, y + h / 2 - 3, label)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Business Use Case
# ════════════════════════════════════════════════════════════════════════════
def page1(c: canvas.Canvas):
    new_page(c)
    header_bar(c, "Business Use Case", "The Problem & Value Proposition", 1)
    footer(c)

    y = H - 70
    M = 22  # margin

    # ── Problem statement ───────────────────────────────────────────────────
    rounded_rect(c, M, y - 68, W - 2 * M, 68, fill_color=HexColor("#1a0d0b"), stroke_color=HexColor("#5c1a10"))
    c.setFillColor(RED)
    c.rect(M, y - 68, 4, 68, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(RED_LIGHT)
    c.drawString(M + 14, y - 20, "The Problem")
    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT2)
    problems = [
        "Hackathons receive hundreds of submissions — manual review takes weeks and introduces bias.",
        "Judges have inconsistent rubrics; different evaluators score the same project differently.",
        "Participants get no actionable feedback, leaving them unable to learn or improve.",
    ]
    for i, p in enumerate(problems):
        c.setFillColor(RED)
        c.circle(M + 16, y - 36 - i * 13, 2.5, fill=1, stroke=0)
        c.setFillColor(TEXT2)
        c.drawString(M + 24, y - 39 - i * 13, p)
    y -= 82

    # ── Value prop cards (3-column) ─────────────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT)
    c.drawString(M, y - 14, "How EVALON Solves It")
    y -= 26

    props = [
        ("⚡", "10× Faster", "Automated evaluation in\nminutes, not weeks", BLUE),
        ("⚖", "Bias-Free", "Consistent AI rubrics applied\nuniformly to every project", EMERALD),
        ("💬", "Actionable Feedback", "Per-agent reasoning + AI\nmentor for every participant", PURPLE),
    ]
    cw = (W - 2 * M - 10) / 3
    for i, (icon, title, body, accent) in enumerate(props):
        cx = M + i * (cw + 5)
        rounded_rect(c, cx, y - 62, cw, 62, fill_color=CARD, stroke_color=accent)
        c.setFillColor(accent)
        c.rect(cx, y - 3, cw, 3, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(accent)
        c.drawCentredString(cx + cw / 2, y - 24, icon)
        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(TEXT)
        c.drawCentredString(cx + cw / 2, y - 38, title)
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT2)
        for j, line in enumerate(body.split("\n")):
            c.drawCentredString(cx + cw / 2, y - 50 - j * 10, line)
    y -= 78

    # ── Target market ───────────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT)
    c.drawString(M, y - 14, "Target Market & Stakeholders")
    y -= 26

    markets = [
        ("Hackathon Organizers", "Universities, corporates, platforms (MLH, Devpost, HackerEarth)", BLUE),
        ("Participants", "Developers & students who need fair scoring + mentorship feedback", EMERALD),
        ("Judges / Sponsors", "Panelists who need ranked shortlists with evidence-backed reasoning", YELLOW),
        ("EdTech Platforms", "Bootcamps & courses automating project evaluation at scale", PURPLE),
    ]
    rh = 34
    for i, (title, desc, accent) in enumerate(markets):
        rx = M
        ry = y - (i + 1) * (rh + 4)
        rounded_rect(c, rx, ry, W - 2 * M, rh, fill_color=CARD, stroke_color=BORDER)
        c.setFillColor(accent)
        c.roundRect(rx, ry, 4, rh, 2, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(TEXT)
        c.drawString(rx + 14, ry + rh - 14, title)
        c.setFont("Helvetica", 8.5)
        c.setFillColor(TEXT2)
        c.drawString(rx + 14, ry + 8, desc)
    y -= len(markets) * (rh + 4) + 16

    # ── KPIs ────────────────────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT)
    c.drawString(M, y - 14, "Key Metrics & Impact")
    y -= 28

    kpis = [
        ("< 5 min", "Full evaluation\nper submission"),
        ("3 AI agents", "Independent scoring\ndimensions"),
        ("RAG-powered", "Mentor grounded in\nyour actual code"),
        ("100% audit", "Every score has\nevidence + reasoning"),
    ]
    kw = (W - 2 * M - 15) / 4
    for i, (val, label) in enumerate(kpis):
        kx = M + i * (kw + 5)
        ky = y - 52
        rounded_rect(c, kx, ky, kw, 52, fill_color=CARD2, stroke_color=BORDER)
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(RED)
        c.drawCentredString(kx + kw / 2, ky + 32, val)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(TEXT2)
        for j, line in enumerate(label.split("\n")):
            c.drawCentredString(kx + kw / 2, ky + 18 - j * 10, line)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Agent Architecture
# ════════════════════════════════════════════════════════════════════════════
def page2(c: canvas.Canvas):
    new_page(c)
    header_bar(c, "Agent Architecture", "Multi-Agent Evaluation Engine powered by LangGraph", 2)
    footer(c)

    M = 22
    y = H - 68

    # ── LangGraph pipeline diagram ──────────────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT)
    c.drawString(M, y - 14, "LangGraph Evaluation Pipeline")
    y -= 28

    # Pipeline nodes (horizontal flow in two rows)
    pipe_y = y - 42
    nw, nh = 82, 38

    nodes = [
        ("Clone\nNode", "git clone + size\nvalidation", RED),
        ("Analyze\nNode", "AST scan · lang\ndetect · metrics", BLUE),
        ("Evaluate\nNode", "3 AI agents run\nin parallel", PURPLE),
        ("Score\nNode", "weighted avg +\ngrade A–F", EMERALD),
    ]

    # Background lane
    lane_x = M
    lane_w = W - 2 * M
    rounded_rect(c, lane_x, pipe_y - 8, lane_w, nh + 16, fill_color=HexColor("#16171e"), stroke_color=BORDER)

    spacing = (lane_w - len(nodes) * nw) / (len(nodes) + 1)
    node_xs = [lane_x + spacing + i * (nw + spacing) for i in range(len(nodes))]

    for i, (title, sub, accent) in enumerate(nodes):
        nx = node_xs[i]
        node_box(c, nx, pipe_y, nw, nh, title.replace("\n", " "),
                 sub.replace("\n", " "), color=CARD, accent=accent)
        # number badge
        c.setFillColor(accent)
        c.circle(nx + 10, pipe_y + nh - 9, 7, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(white)
        c.drawCentredString(nx + 10, pipe_y + nh - 12, str(i + 1))

    # Draw arrows between nodes
    for i in range(len(nodes) - 1):
        x1 = node_xs[i] + nw
        x2 = node_xs[i + 1]
        ay = pipe_y + nh / 2
        arrow_h(c, x1 + 2, ay, x2 - 2, color=MUTED)

    # Labels under each node
    c.setFont("Helvetica", 7.5)
    for i, (_, sub, _) in enumerate(nodes):
        nx = node_xs[i]
        for j, line in enumerate(sub.split("\n")):
            c.setFillColor(TEXT2)
            c.drawCentredString(nx + nw / 2, pipe_y - 12 - j * 9, line)

    # Conditional routing note
    c.setFont("Helvetica", 7.5)
    c.setFillColor(DIM)
    c.drawCentredString(W / 2, pipe_y - 32,
        "↺  Conditional edges — failed nodes route to 'failed' terminal; each node updates submission.status in real-time")

    y = pipe_y - 52

    # ── Three AI agents detail ──────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT)
    c.drawString(M, y - 14, "AI Scoring Agents  (run in parallel inside Evaluate Node)")
    y -= 26

    agents = [
        {
            "name": "Repo Understanding",
            "model": "qwen2.5:7b  (reasoning)",
            "accent": BLUE,
            "icon": "{}",
            "weight": "40%",
            "criteria": ["README completeness", "Project structure clarity",
                         "Dependency management", "Code organisation"],
            "output": "score 0–10 + evidence list",
        },
        {
            "name": "Code Quality",
            "model": "qwen2.5-coder:7b  (code)",
            "accent": EMERALD,
            "icon": "</>",
            "weight": "35%",
            "criteria": ["Naming conventions", "Modularity & DRY",
                         "Error handling", "Test coverage"],
            "output": "score 0–10 + inline reasoning",
        },
        {
            "name": "Innovation",
            "model": "qwen2.5:7b  (reasoning)",
            "accent": PURPLE,
            "icon": "✦",
            "weight": "25%",
            "criteria": ["Problem novelty", "Technical ambition",
                         "Practical applicability", "Theme alignment"],
            "output": "score 0–10 + comparative notes",
        },
    ]

    ah = 120
    aw = (W - 2 * M - 10) / 3
    for i, ag in enumerate(agents):
        ax = M + i * (aw + 5)
        ay = y - ah
        rounded_rect(c, ax, ay, aw, ah, fill_color=CARD, stroke_color=ag["accent"])
        # top accent bar
        c.setFillColor(ag["accent"])
        c.roundRect(ax, ay + ah - 4, aw, 4, 3, fill=1, stroke=0)
        # icon circle
        c.setFillColor(HexColor("#1e1f28"))
        c.circle(ax + 20, ay + ah - 20, 12, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(ag["accent"])
        c.drawCentredString(ax + 20, ay + ah - 24, ag["icon"])
        # title
        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(TEXT)
        c.drawString(ax + 36, ay + ah - 15, ag["name"])
        # model tag
        c.setFont("Helvetica", 7)
        c.setFillColor(MUTED)
        c.drawString(ax + 36, ay + ah - 26, ag["model"])
        # weight pill
        label_pill(c, ax + aw - 32, ay + ah - 30, ag["weight"], bg=CARD2, fg=ag["accent"], w=28)
        # divider
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.line(ax + 8, ay + ah - 34, ax + aw - 8, ay + ah - 34)
        # criteria
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(MUTED)
        c.drawString(ax + 10, ay + ah - 44, "Criteria:")
        c.setFont("Helvetica", 7.5)
        c.setFillColor(TEXT2)
        for j, cr in enumerate(ag["criteria"]):
            c.setFillColor(ag["accent"])
            c.circle(ax + 14, ay + ah - 57 - j * 11, 2, fill=1, stroke=0)
            c.setFillColor(TEXT2)
            c.drawString(ax + 20, ay + ah - 60 - j * 11, cr)
        # output
        c.setStrokeColor(BORDER)
        c.line(ax + 8, ay + 20, ax + aw - 8, ay + 20)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(ag["accent"])
        c.drawString(ax + 10, ay + 8, "→  " + ag["output"])

    y = y - ah - 16

    # ── RAG + Embedding layer ───────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT)
    c.drawString(M, y - 14, "RAG Layer — AI Mentor Context Engine")
    y -= 26

    rag_nodes = [
        ("Code\nChunker", "splits files\ninto 1500-char\nchunks", CARD2),
        ("nomic-embed-text\nEmbedding Model", "768-dim vectors\nper chunk\n(Ollama)", CARD2),
        ("pgvector\nPostgreSQL", "cosine similarity\nvector search\nindex", CARD2),
        ("MentorBot\nRetriever", "top-k relevant\nchunks injected\ninto prompt", CARD2),
        ("qwen2.5:7b\nChat Model", "context-aware\nanswers grounded\nin your code", CARD2),
    ]

    rw, rh2 = 88, 52
    total_w = len(rag_nodes) * rw + (len(rag_nodes) - 1) * 10
    start_x = (W - total_w) / 2

    for i, (title, sub, bg) in enumerate(rag_nodes):
        rx = start_x + i * (rw + 10)
        ry = y - rh2
        accent = [BLUE, HexColor("#0ea5e9"), HexColor("#10b981"), RED, PURPLE][i]
        rounded_rect(c, rx, ry, rw, rh2, fill_color=bg, stroke_color=accent)
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(accent)
        for j, line in enumerate(title.split("\n")):
            c.drawCentredString(rx + rw / 2, ry + rh2 - 12 - j * 10, line)
        c.setFont("Helvetica", 7)
        c.setFillColor(TEXT2)
        for j, line in enumerate(sub.split("\n")):
            c.drawCentredString(rx + rw / 2, ry + rh2 - 32 - j * 9, line)
        if i < len(rag_nodes) - 1:
            arrow_h(c, rx + rw + 2, ry + rh2 / 2, rx + rw + 8, color=DIM)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Overall Workflow
# ════════════════════════════════════════════════════════════════════════════
def page3(c: canvas.Canvas):
    new_page(c)
    header_bar(c, "Overall System Workflow", "End-to-End Architecture & Data Flow", 3)
    footer(c)

    M = 22
    y = H - 68

    # ── System architecture (3 swim-lanes) ─────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT)
    c.drawString(M, y - 14, "System Architecture — Three-Layer Design")
    y -= 26

    lanes = [
        ("Frontend\n(Next.js 14)", BLUE, [
            "Auth (JWT)",
            "Hackathon Browser",
            "Submit Repo URL",
            "Live Progress (SSE)",
            "Score Dashboard",
            "AI Mentor Chat",
        ]),
        ("Backend API\n(FastAPI + arq)", EMERALD, [
            "REST endpoints /v1/...",
            "JWT auth + refresh",
            "Job queue (Redis/arq)",
            "SSE evaluation stream",
            "Chat session manager",
            "Admin control panel",
        ]),
        ("AI Engine\n(LangGraph + Ollama)", PURPLE, [
            "Clone → Analyze → Evaluate",
            "3 parallel scoring agents",
            "pgvector embeddings",
            "RAG retrieval pipeline",
            "Score aggregation",
            "Rankings computation",
        ]),
    ]

    lw = (W - 2 * M - 10) / 3
    lh = 130
    ly = y - lh

    for i, (title, accent, items) in enumerate(lanes):
        lx = M + i * (lw + 5)
        rounded_rect(c, lx, ly, lw, lh, fill_color=CARD, stroke_color=accent)
        # header
        c.setFillColor(accent)
        c.roundRect(lx, ly + lh - 26, lw, 26, 4, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(white)
        for j, line in enumerate(title.split("\n")):
            c.drawCentredString(lx + lw / 2, ly + lh - 13 - j * 11, line)
        # items
        c.setFont("Helvetica", 8)
        for j, item in enumerate(items):
            c.setFillColor(accent)
            c.circle(lx + 12, ly + lh - 40 - j * 16, 2.5, fill=1, stroke=0)
            c.setFillColor(TEXT2)
            c.drawString(lx + 20, ly + lh - 43 - j * 16, item)

    # Bidirectional arrows between lanes
    for i in range(len(lanes) - 1):
        ax = M + (i + 1) * (lw + 5) - 5
        ay = ly + lh / 2
        c.setStrokeColor(MUTED)
        c.setLineWidth(1)
        c.line(ax - 2, ay, ax + 7, ay)
        # double arrowhead
        for dx, direction in [(-2, -1), (7, 1)]:
            p = c.beginPath()
            p.moveTo(ax + dx, ay)
            p.lineTo(ax + dx - direction * 5, ay + 4)
            p.lineTo(ax + dx - direction * 5, ay - 4)
            p.close()
            c.setFillColor(MUTED)
            c.drawPath(p, fill=1, stroke=0)

    y = ly - 18

    # ── Infrastructure stack ────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT)
    c.drawString(M, y - 14, "Infrastructure & Technology Stack")
    y -= 26

    stack_rows = [
        ("Containerisation", [("Docker Compose", BLUE), ("7 services", DIM), ("Health checks", DIM), ("Named volumes", DIM)]),
        ("Databases",        [("PostgreSQL 16 + pgvector", EMERALD), ("Redis 7 (job queue + cache)", EMERALD)]),
        ("AI / ML",         [("Ollama (local LLM runtime)", PURPLE), ("qwen2.5-coder:7b", PURPLE), ("qwen2.5:7b", PURPLE), ("nomic-embed-text", PURPLE)]),
        ("Observability",   [("Structured logs (structlog)", YELLOW), ("SSE real-time events", YELLOW), ("Evaluation audit trail", YELLOW)]),
    ]

    rh3 = 26
    for i, (section, pills) in enumerate(stack_rows):
        ry = y - (i + 1) * (rh3 + 4)
        rounded_rect(c, M, ry, W - 2 * M, rh3, fill_color=CARD, stroke_color=BORDER)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(MUTED)
        c.drawString(M + 10, ry + 9, section)
        px = M + 110
        for text, clr in pills:
            pw = label_pill(c, px, ry + 6, text, bg=CARD2, fg=clr)
            px += pw + 5

    y = y - len(stack_rows) * (rh3 + 4) - 16

    # ── End-to-end user journey ─────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT)
    c.drawString(M, y - 14, "End-to-End User Journey")
    y -= 26

    steps = [
        ("1", "Register\n& Login", BLUE),
        ("2", "Browse\nHackathon", BLUE),
        ("3", "Submit\nRepo URL", RED),
        ("4", "Pipeline\nRuns", PURPLE),
        ("5", "View\nResults", EMERALD),
        ("6", "Chat with\nMentor", YELLOW),
    ]

    sw = (W - 2 * M) / len(steps)
    sh = 54
    sy = y - sh

    for i, (num, label, accent) in enumerate(steps):
        sx = M + i * sw
        # connector line
        if i < len(steps) - 1:
            c.setStrokeColor(BORDER)
            c.setLineWidth(1)
            c.setDash(3, 3)
            c.line(sx + sw * 0.7, sy + sh / 2, sx + sw, sy + sh / 2)
            c.setDash()

        # circle badge
        cx2 = sx + sw / 2
        cy2 = sy + sh / 2
        c.setFillColor(accent)
        c.circle(cx2, cy2 + 8, 12, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(white)
        c.drawCentredString(cx2, cy2 + 4, num)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(TEXT2)
        for j, line in enumerate(label.split("\n")):
            c.drawCentredString(cx2, cy2 - 8 - j * 10, line)

    y = sy - 16

    # ── Security & scalability ──────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT)
    c.drawString(M, y - 14, "Security & Scalability Highlights")
    y -= 24

    points = [
        ("JWT + Refresh Tokens", "24-hour access tokens with 7-day refresh; auto-rotation on expiry.", BLUE),
        ("Role-Based Access",    "Separate participant / admin roles; ownership checks on every resource.", EMERALD),
        ("Async Worker Queue",   "arq (asyncio-native Redis queue) decouples API from long-running LLM jobs.", PURPLE),
        ("Horizontal Scale",    "Workers are stateless — add replicas by scaling the worker service in Compose.", YELLOW),
    ]

    ph = 26
    for i, (title, desc, accent) in enumerate(points):
        py2 = y - (i + 1) * (ph + 3)
        rounded_rect(c, M, py2, W - 2 * M, ph, fill_color=CARD, stroke_color=BORDER)
        c.setFillColor(accent)
        c.roundRect(M, py2, 4, ph, 2, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(TEXT)
        c.drawString(M + 14, py2 + ph - 12, title)
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT2)
        c.drawString(M + 14, py2 + 6, desc)


# ── Main ─────────────────────────────────────────────────────────────────────
output_path = "/Users/arunishrajput/Downloads/Anvil/EVALON_Submission.pdf"
c = canvas.Canvas(output_path, pagesize=A4)
c.setTitle("EVALON — AI-Powered Hackathon Evaluation Engine")
c.setAuthor("EVALON Team")
c.setSubject("Hackathon Submission — Agent Architecture, Business Use Case, System Workflow")

page1(c)
c.showPage()
page2(c)
c.showPage()
page3(c)
c.showPage()

c.save()
print(f"PDF saved to: {output_path}")
