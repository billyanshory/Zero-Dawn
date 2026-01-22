from flask import Flask, render_template_string, request, jsonify
import json
import os
import math

app = Flask(__name__)

# --- EMBEDDED FRONTEND ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Denah Rumah | Windows 11 Acrylic Style</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* --- CSS VARIABLES & RESET --- */
        :root {
            --bg-color: #202020; /* Dark background like blueprint/dark mode */
            --grid-major: rgba(255, 255, 255, 0.1);
            --grid-fine: rgba(255, 255, 255, 0.03);
            --accent-color: #60cdff; /* Windows 11 Blue */
            --text-color: #ffffff;
            --glass-bg: rgba(32, 32, 32, 0.6);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            --blur-amount: 20px;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; user-select: none; }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
        }

        /* --- LAYOUT --- */
        #app-container {
            position: relative;
            width: 100%;
            height: 100%;
        }

        canvas {
            display: block;
            width: 100%;
            height: 100%;
            cursor: crosshair;
        }

        /* --- ACRYLIC UI COMPONENTS --- */
        .acrylic-panel {
            position: absolute;
            background: var(--glass-bg);
            backdrop-filter: blur(var(--blur-amount)) saturate(150%);
            -webkit-backdrop-filter: blur(var(--blur-amount)) saturate(150%);
            border: 1px solid var(--glass-border);
            box-shadow: var(--glass-shadow);
            border-radius: 8px;
            padding: 10px;
            z-index: 10;
            transition: all 0.3s ease;
        }

        /* Header */
        .top-bar {
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 8px 24px;
            border-radius: 50px;
        }
        .top-bar h1 {
            font-size: 1rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Toolbar */
        .toolbar {
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
            padding: 10px;
        }

        .tool-btn {
            background: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.7);
            padding: 10px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1.2rem;
            transition: all 0.2s;
            position: relative;
        }
        .tool-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
        }
        .tool-btn.active {
            background: rgba(96, 205, 255, 0.2);
            color: var(--accent-color);
        }
        .tool-btn::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 120%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            color: #fff;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s;
        }
        .tool-btn:hover::after {
            opacity: 1;
        }

        /* Info Panel */
        .info-panel {
            top: 10px;
            right: 10px;
            width: 250px;
            font-size: 0.9rem;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            color: rgba(255, 255, 255, 0.8);
        }
        .info-value {
            font-weight: 600;
            color: var(--accent-color);
        }

        /* Help Modal */
        #help-modal {
            display: none;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 400px;
            padding: 20px;
            z-index: 100;
        }
        #help-modal h2 { margin-bottom: 15px; font-weight: 600; color: var(--accent-color); }
        #help-modal ul { list-style: none; padding-left: 0; }
        #help-modal li { margin-bottom: 8px; font-size: 0.9rem; display: flex; justify-content: space-between; }
        .key { background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; font-family: monospace; }
        .close-btn {
            margin-top: 15px;
            width: 100%;
            padding: 8px;
            background: var(--accent-color);
            border: none;
            border-radius: 4px;
            color: #000;
            font-weight: 600;
            cursor: pointer;
        }

        /* Input for measurement */
        #measure-input {
            position: absolute;
            display: none;
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--accent-color);
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-family: monospace;
            z-index: 20;
            pointer-events: none; /* Let clicks pass through if needed, but input needs focus */
        }

    </style>
</head>
<body>

<div id="app-container">
    <canvas id="floorplanCanvas"></canvas>

    <!-- Top Bar -->
    <div class="acrylic-panel top-bar">
        <h1><i class="fas fa-drafting-compass"></i> Website Denah Rumah</h1>
    </div>

    <!-- Info Panel -->
    <div class="acrylic-panel info-panel">
        <div class="info-row"><span>Mode</span><span class="info-value" id="mode-display">SELECT</span></div>
        <div class="info-row"><span>Zoom</span><span class="info-value" id="zoom-display">100%</span></div>
        <div class="info-row"><span>Segments</span><span class="info-value" id="seg-count">0</span></div>
        <div class="info-row" style="margin-top:10px; font-size:0.8em; color:rgba(255,255,255,0.5);">Press H for Help</div>
    </div>

    <!-- Toolbar -->
    <div class="acrylic-panel toolbar">
        <button class="tool-btn active" id="btn-select" data-tooltip="Select (V)"><i class="fas fa-mouse-pointer"></i></button>
        <button class="tool-btn" id="btn-line" data-tooltip="Draw Wall (L)"><i class="fas fa-pen-nib"></i></button>
        <button class="tool-btn" id="btn-delete" data-tooltip="Delete Selected (Del)"><i class="fas fa-trash"></i></button>
        <button class="tool-btn" id="btn-clear" data-tooltip="Clear All (C)"><i class="fas fa-eraser"></i></button>
        <button class="tool-btn" id="btn-help" data-tooltip="Help (H)"><i class="fas fa-question-circle"></i></button>
    </div>

    <!-- Measure Input (Hidden overlay) -->
    <div id="measure-input"></div>

    <!-- Help Modal -->
    <div class="acrylic-panel" id="help-modal">
        <h2>Controls</h2>
        <ul>
            <li><span>Pan</span> <span class="key">Middle Drag / Space+Drag</span></li>
            <li><span>Zoom</span> <span class="key">Wheel</span></li>
            <li><span>Select</span> <span class="key">Left Click</span></li>
            <li><span>Draw Line</span> <span class="key">Left Click + Click</span></li>
            <li><span>Finish Line</span> <span class="key">Right Click / Esc</span></li>
            <li><span>Delete</span> <span class="key">Del / Backspace</span></li>
            <li><span>Snap Toggle</span> <span class="key">G</span></li>
        </ul>
        <button class="close-btn" onclick="document.getElementById('help-modal').style.display='none'">Got it</button>
    </div>
</div>

<script>
/**
 * Modern ES2025 JavaScript Logic for Floor Plan Drawing
 * "Blur Akrilik" Design Principles
 */

// Constants
const PIXELS_PER_METER = 100;
const GRID_FINE = 25; // 0.25m
const GRID_MAJOR = 100; // 1m
const SNAP_RADIUS = 15;

class FloorPlanApp {
    constructor() {
        this.canvas = document.getElementById('floorplanCanvas');
        this.ctx = this.canvas.getContext('2d');

        // State
        this.segments = []; // {id, start: {x, y}, end: {x, y}, length, height}
        this.nextId = 1;
        this.camera = { x: 0, y: 0, zoom: 1.0 };
        this.mode = 'select'; // select, line
        this.selectedIds = new Set();
        this.snapEnabled = true;

        // Interaction State
        this.isDragging = false;
        this.lastMouse = { x: 0, y: 0 };
        this.dragStart = { x: 0, y: 0 };
        this.currentLineStart = null; // When drawing
        this.mouseWorld = { x: 0, y: 0 };

        // Setup
        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.bindEvents();
        this.bindToolbar();

        // Loop
        requestAnimationFrame(() => this.loop());

        // Center camera
        this.camera.x = this.canvas.width / 2;
        this.camera.y = this.canvas.height / 2;
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    bindEvents() {
        // Mouse Events
        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this.onWheel(e), { passive: false });
        this.canvas.addEventListener('contextmenu', (e) => { e.preventDefault(); this.cancelAction(); });

        // Keyboard
        window.addEventListener('keydown', (e) => this.onKeyDown(e));
    }

    bindToolbar() {
        const setMode = (mode, btnId) => {
            this.mode = mode;
            this.cancelAction(); // Reset current drawing state
            document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
            if(btnId) document.getElementById(btnId).classList.add('active');
            document.getElementById('mode-display').innerText = mode.toUpperCase();
        };

        document.getElementById('btn-select').onclick = () => setMode('select', 'btn-select');
        document.getElementById('btn-line').onclick = () => setMode('line', 'btn-line');

        document.getElementById('btn-delete').onclick = () => this.deleteSelected();
        document.getElementById('btn-clear').onclick = () => {
            if(confirm('Clear all?')) {
                this.segments = [];
                this.selectedIds.clear();
            }
        };
        document.getElementById('btn-help').onclick = () => {
            document.getElementById('help-modal').style.display = 'block';
        };
    }

    // --- Transforms ---
    screenToWorld(sx, sy) {
        return {
            x: (sx - this.camera.x) / this.camera.zoom,
            y: (sy - this.camera.y) / this.camera.zoom
        };
    }

    worldToScreen(wx, wy) {
        return {
            x: wx * this.camera.zoom + this.camera.x,
            y: wy * this.camera.zoom + this.camera.y
        };
    }

    getSnappedPoint(wx, wy) {
        if (!this.snapEnabled) return { x: wx, y: wy };

        // 1. Snap to existing points (Magnet)
        let bestDist = SNAP_RADIUS / this.camera.zoom;
        let bestPoint = null;

        const points = [];
        this.segments.forEach(s => { points.push(s.start); points.push(s.end); });

        for (let p of points) {
            const dx = p.x - wx;
            const dy = p.y - wy;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < bestDist) {
                bestDist = dist;
                bestPoint = { ...p };
            }
        }
        if (bestPoint) return bestPoint;

        // 2. Snap to Grid
        const snapSize = GRID_FINE;
        return {
            x: Math.round(wx / snapSize) * snapSize,
            y: Math.round(wy / snapSize) * snapSize
        };
    }

    // --- Input Handling ---
    onMouseDown(e) {
        if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
            // Middle click or Shift+Click -> Pan
            this.isDragging = true;
            this.dragStart = { x: e.clientX, y: e.clientY };
            return;
        }

        const world = this.screenToWorld(e.clientX, e.clientY);
        const snapped = this.getSnappedPoint(world.x, world.y);

        if (this.mode === 'line') {
            if (e.button === 0) {
                if (!this.currentLineStart) {
                    this.currentLineStart = snapped;
                } else {
                    // Finish segment
                    this.addSegment(this.currentLineStart, snapped);
                    this.currentLineStart = snapped; // Chain drawing
                }
            }
        } else if (this.mode === 'select') {
            if (e.button === 0) {
                this.handleSelection(world);
            }
        }
    }

    onMouseMove(e) {
        this.lastMouse = { x: e.clientX, y: e.clientY };
        this.mouseWorld = this.screenToWorld(e.clientX, e.clientY);

        if (this.isDragging) {
            const dx = e.clientX - this.dragStart.x;
            const dy = e.clientY - this.dragStart.y;
            this.camera.x += dx;
            this.camera.y += dy;
            this.dragStart = { x: e.clientX, y: e.clientY };
        }
    }

    onMouseUp(e) {
        if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
            this.isDragging = false;
        }
    }

    onWheel(e) {
        e.preventDefault();
        const zoomFactor = 1.1;
        const direction = e.deltaY > 0 ? -1 : 1;

        const before = this.screenToWorld(e.clientX, e.clientY);

        if (direction > 0) this.camera.zoom *= zoomFactor;
        else this.camera.zoom /= zoomFactor;

        // Clamp zoom
        this.camera.zoom = Math.max(0.1, Math.min(10, this.camera.zoom));

        // Adjust camera pos to keep mouse world pos static
        const after = this.screenToWorld(e.clientX, e.clientY);
        this.camera.x += (after.x - before.x) * this.camera.zoom;
        this.camera.y += (after.y - before.y) * this.camera.zoom;

        document.getElementById('zoom-display').innerText = Math.round(this.camera.zoom * 100) + '%';
    }

    onKeyDown(e) {
        if (e.key === 'Escape') this.cancelAction();
        if (e.key === 'Delete' || e.key === 'Backspace') this.deleteSelected();
        if (e.key.toLowerCase() === 'g') this.snapEnabled = !this.snapEnabled;
        if (e.key.toLowerCase() === 'c') document.getElementById('btn-clear').click();
        if (e.key.toLowerCase() === 'l') document.getElementById('btn-line').click();
        if (e.key.toLowerCase() === 'v') document.getElementById('btn-select').click();
        if (e.key.toLowerCase() === 'h') document.getElementById('btn-help').click();
    }

    cancelAction() {
        this.currentLineStart = null;
        this.isDragging = false;
    }

    // --- Logic ---
    addSegment(p1, p2) {
        if (p1.x === p2.x && p1.y === p2.y) return;
        const length = Math.hypot(p2.x - p1.x, p2.y - p1.y) / PIXELS_PER_METER;
        this.segments.push({
            id: this.nextId++,
            start: { ...p1 },
            end: { ...p2 },
            length: length,
            height: 2.5 // Default wall height in meters
        });
        document.getElementById('seg-count').innerText = this.segments.length;
    }

    deleteSelected() {
        this.segments = this.segments.filter(s => !this.selectedIds.has(s.id));
        this.selectedIds.clear();
        document.getElementById('seg-count').innerText = this.segments.length;
    }

    handleSelection(worldPos) {
        // Simple click selection (distance to line segment)
        const threshold = 10 / this.camera.zoom;
        let hit = null;

        for (let s of this.segments) {
            const dist = this.pointToSegmentDist(worldPos.x, worldPos.y, s.start.x, s.start.y, s.end.x, s.end.y);
            if (dist < threshold) {
                hit = s;
                break; // Select first hit
            }
        }

        if (!hit) {
            this.selectedIds.clear();
        } else {
            if (this.selectedIds.has(hit.id)) {
                this.selectedIds.delete(hit.id);
            } else {
                this.selectedIds.clear(); // Single select for now
                this.selectedIds.add(hit.id);
            }
        }
    }

    pointToSegmentDist(px, py, x1, y1, x2, y2) {
        const A = px - x1;
        const B = py - y1;
        const C = x2 - x1;
        const D = y2 - y1;

        const dot = A * C + B * D;
        const len_sq = C * C + D * D;
        let param = -1;
        if (len_sq !== 0) param = dot / len_sq;

        let xx, yy;

        if (param < 0) {
            xx = x1;
            yy = y1;
        } else if (param > 1) {
            xx = x2;
            yy = y2;
        } else {
            xx = x1 + param * C;
            yy = y1 + param * D;
        }

        const dx = px - xx;
        const dy = py - yy;
        return Math.sqrt(dx * dx + dy * dy);
    }

    // --- Rendering ---
    loop() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Background color handled by CSS, but we need to draw grid on top
        this.drawGrid();

        // Draw Segments
        this.ctx.lineCap = 'round';
        this.segments.forEach(s => this.drawSegment(s));

        // Draw Current Drawing Line
        if (this.mode === 'line' && this.currentLineStart) {
            const snapped = this.getSnappedPoint(this.mouseWorld.x, this.mouseWorld.y);
            this.drawPreviewLine(this.currentLineStart, snapped);
        }

        // Draw HUD/Cursor
        if (this.snapEnabled && this.mode === 'line') {
            const snapped = this.getSnappedPoint(this.mouseWorld.x, this.mouseWorld.y);
            const sc = this.worldToScreen(snapped.x, snapped.y);
            this.ctx.beginPath();
            this.ctx.arc(sc.x, sc.y, 5, 0, Math.PI*2);
            this.ctx.strokeStyle = '#60cdff';
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
        }

        requestAnimationFrame(() => this.loop());
    }

    drawGrid() {
        const zoom = this.camera.zoom;

        // Only draw if not too dense
        if (zoom < 0.1) return;

        // Viewport bounds in world
        const tl = this.screenToWorld(0, 0);
        const br = this.screenToWorld(this.canvas.width, this.canvas.height);

        const drawLines = (step, color, width) => {
            this.ctx.beginPath();
            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = width;

            const startX = Math.floor(tl.x / step) * step;
            const endX = Math.ceil(br.x / step) * step;
            const startY = Math.floor(tl.y / step) * step;
            const endY = Math.ceil(br.y / step) * step;

            for (let x = startX; x <= endX; x += step) {
                const s = this.worldToScreen(x, 0);
                this.ctx.moveTo(s.x, 0);
                this.ctx.lineTo(s.x, this.canvas.height);
            }
            for (let y = startY; y <= endY; y += step) {
                const s = this.worldToScreen(0, y);
                this.ctx.moveTo(0, s.y);
                this.ctx.lineTo(this.canvas.width, s.y);
            }
            this.ctx.stroke();
        };

        drawLines(GRID_FINE, 'rgba(255, 255, 255, 0.05)', 1);
        drawLines(GRID_MAJOR, 'rgba(255, 255, 255, 0.1)', 1); // Major grid
    }

    drawSegment(seg) {
        const start = this.worldToScreen(seg.start.x, seg.start.y);
        const end = this.worldToScreen(seg.end.x, seg.end.y);
        const isSelected = this.selectedIds.has(seg.id);

        // Draw Wall Body (Thickness)
        const wallThickness = 15 * this.camera.zoom; // 15cm scaled
        this.ctx.beginPath();
        this.ctx.moveTo(start.x, start.y);
        this.ctx.lineTo(end.x, end.y);
        this.ctx.strokeStyle = isSelected ? '#ffcc00' : '#ffffff';
        this.ctx.lineWidth = 4 * this.camera.zoom; // Line thickness
        this.ctx.stroke();

        // Draw Dimensions
        const midX = (start.x + end.x) / 2;
        const midY = (start.y + end.y) / 2;

        this.ctx.fillStyle = isSelected ? '#ffcc00' : '#aaaaaa';
        this.ctx.font = `12px sans-serif`;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'bottom';
        this.ctx.fillText(`${seg.length.toFixed(2)}m`, midX, midY - 5);
    }

    drawPreviewLine(p1, p2) {
        const s1 = this.worldToScreen(p1.x, p1.y);
        const s2 = this.worldToScreen(p2.x, p2.y);

        this.ctx.beginPath();
        this.ctx.moveTo(s1.x, s1.y);
        this.ctx.lineTo(s2.x, s2.y);
        this.ctx.strokeStyle = '#60cdff';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        // Live Length
        const dist = Math.hypot(p2.x - p1.x, p2.y - p1.y) / PIXELS_PER_METER;
        const midX = (s1.x + s2.x) / 2;
        const midY = (s1.y + s2.y) / 2;
        this.ctx.fillStyle = '#60cdff';
        this.ctx.fillText(`${dist.toFixed(2)}m`, midX, midY - 10);
    }
}

// Init App
window.onload = () => {
    const app = new FloorPlanApp();
};

</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    # Use environment variables for configuration, default to safe production settings
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, port=port)
