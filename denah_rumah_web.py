from flask import Flask, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Website Denah Rumah - Modern Blur Akrilik</title>
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@300;400;600&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

    <style>
        :root {
            --glass-bg: rgba(20, 20, 30, 0.65);
            --glass-border: rgba(255, 255, 255, 0.1);
            --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            --accent-color: #60cdff;
            --text-primary: #ffffff;
            --text-secondary: #aaaaaa;
            --font-family: 'Segoe UI', sans-serif;
        }

        body {
            margin: 0;
            overflow: hidden;
            background-color: #1e1e1e;
            color: var(--text-primary);
            font-family: var(--font-family);
            user-select: none;
        }

        #app-container {
            position: relative;
            width: 100vw;
            height: 100vh;
        }

        canvas {
            display: block;
            outline: none;
        }

        /* Glassmorphism Utilities */
        .glass-panel {
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            box-shadow: var(--glass-shadow);
            color: var(--text-primary);
            transition: all 0.3s ease;
        }

        /* HUD Overlay */
        #hud {
            position: absolute;
            top: 20px;
            left: 20px;
            padding: 15px;
            pointer-events: none; /* Let clicks pass through */
            max-width: 400px;
        }

        #hud h1 {
            margin: 0 0 10px 0;
            font-size: 1.2rem;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        #hud p {
            margin: 4px 0;
            font-size: 0.9rem;
            color: var(--text-secondary);
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }

        /* Toolbar */
        #toolbar {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            pointer-events: auto;
        }

        .tool-btn {
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            cursor: pointer;
            background: rgba(40, 40, 50, 0.5);
        }

        .tool-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: scale(1.05);
        }

        .tool-btn.active {
            background: var(--accent-color);
            color: #000;
            box-shadow: 0 0 15px var(--accent-color);
        }

        /* Bottom Controls */
        #bottom-bar {
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 15px;
            pointer-events: auto;
        }

        .control-pill {
            padding: 8px 16px;
            font-size: 0.9rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .control-pill:hover {
            background: rgba(255,255,255,0.15);
        }

        /* Input overlay for typing measurements */
        #measure-input {
            position: absolute;
            display: none;
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid var(--accent-color);
            color: white;
            font-family: monospace;
            font-size: 1rem;
            pointer-events: none;
            transform: translate(20px, -20px);
        }

        /* Help Modal */
        #help-modal {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 500px;
            max-width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            padding: 30px;
            display: none;
            z-index: 1000;
        }

        #help-modal.visible {
            display: block;
            animation: fadeIn 0.3s forwards;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translate(-50%, -45%); }
            to { opacity: 1; transform: translate(-50%, -50%); }
        }

        .key-badge {
            display: inline-block;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 4px;
            padding: 2px 6px;
            font-family: monospace;
            font-size: 0.85rem;
            margin-right: 5px;
            color: var(--accent-color);
        }

        h2 { margin-top: 0; color: var(--accent-color); }
        .help-item { margin-bottom: 8px; display: flex; align-items: center; }

        /* Context Menu (Mobile/Touch Friendly) logic could be added here */

        /* Toast Notification */
        #toast {
            position: absolute;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        }

        /* Scrollbar aesthetics */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.4); }

    </style>
</head>
<body>

    <div id="app-container">
        <canvas id="main-canvas"></canvas>

        <!-- Heads Up Display -->
        <div id="hud" class="glass-panel">
            <h1>Website Denah Rumah</h1>
            <p id="hud-status">Mode: XY | Cursor: 0,0</p>
            <p id="hud-stats">Segs: 0 | Walls: 0 | Snap: ON</p>
            <p id="hud-cam">Zoom: 1.0x | Angle: 0°</p>
        </div>

        <!-- Toolbar -->
        <div id="toolbar">
            <div class="glass-panel tool-btn" id="btn-select" title="Select (S)">
                <i class="fas fa-mouse-pointer"></i>
            </div>
            <div class="glass-panel tool-btn" id="btn-draw" title="Draw Line (L)">
                <i class="fas fa-pen"></i>
            </div>
            <div class="glass-panel tool-btn" id="btn-extrude" title="Extrude Walls (E)">
                <i class="fas fa-cube"></i>
            </div>
            <div class="glass-panel tool-btn" id="btn-height" title="Height Tool (H)">
                <i class="fas fa-ruler-vertical"></i>
            </div>
             <div class="glass-panel tool-btn" id="btn-dimension" title="Adjust Dimensions (M)">
                <i class="fas fa-arrows-alt-h"></i>
            </div>
            <div class="glass-panel tool-btn" id="btn-undo" title="Undo (Z)">
                <i class="fas fa-undo"></i>
            </div>
            <div class="glass-panel tool-btn" id="btn-redo" title="Redo (Y)">
                <i class="fas fa-redo"></i>
            </div>
             <div class="glass-panel tool-btn" id="btn-clear" title="Clear All (C)">
                <i class="fas fa-trash"></i>
            </div>
             <div class="glass-panel tool-btn" id="btn-theme" title="Toggle Theme (T)">
                <i class="fas fa-palette"></i>
            </div>
            <div class="glass-panel tool-btn" id="btn-help" title="Help (?)">
                <i class="fas fa-question"></i>
            </div>
        </div>

        <!-- Bottom Controls (Camera Pitch / Exports) -->
        <div id="bottom-bar">
            <div class="glass-panel control-pill" onclick="app.setPitch(0)">
                <i class="fas fa-eye"></i> Front 0°
            </div>
            <div class="glass-panel control-pill" onclick="app.setPitch(45)">
                <i class="fas fa-cube"></i> ISO 45°
            </div>
            <div class="glass-panel control-pill" onclick="app.setPitch(90)">
                <i class="fas fa-layer-group"></i> Top 90°
            </div>
            <div class="glass-panel control-pill" onclick="app.exportPNG()">
                <i class="fas fa-image"></i> PNG
            </div>
             <div class="glass-panel control-pill" onclick="app.exportPDF()">
                <i class="fas fa-file-pdf"></i> PDF
            </div>
        </div>

        <div id="measure-input"></div>
        <div id="toast">Message</div>

        <!-- Help Modal -->
        <div id="help-modal" class="glass-panel">
            <h2>Controls & Shortcuts</h2>
            <div class="help-item"><span class="key-badge">LMB</span> Draw / Select / Confirm</div>
            <div class="help-item"><span class="key-badge">RMB</span> Cancel Action</div>
            <div class="help-item"><span class="key-badge">W/A/S/D</span> Pan Camera</div>
            <div class="help-item"><span class="key-badge">Scroll</span> Zoom In/Out</div>
            <div class="help-item"><span class="key-badge">Arrows</span> Rotate / Zoom</div>
            <div class="help-item"><span class="key-badge">G</span> Toggle Snap (Grid/Magnet)</div>
            <div class="help-item"><span class="key-badge">M</span> Toggle Dimensions</div>
            <div class="help-item"><span class="key-badge">H</span> Height Tool</div>
            <div class="help-item"><span class="key-badge">E</span> Extrude Tool</div>
            <div class="help-item"><span class="key-badge">Z / Y</span> Undo / Redo</div>
            <div class="help-item"><span class="key-badge">C</span> Clear All</div>
            <div class="help-item"><span class="key-badge">Esc</span> Close / Cancel</div>
            <br>
            <div class="glass-panel control-pill" style="display:inline-flex; width:auto;" onclick="document.getElementById('help-modal').classList.remove('visible')">Close</div>
        </div>
    </div>

    <script type="module">
        /**
         * Denah Rumah Web - Single File Re-implementation
         * Uses HTML5 Canvas + ES2025 Features
         */

        // --- Constants ---
        const PIXELS_PER_METER = 100;
        const GRID_FINE = 0.25 * PIXELS_PER_METER;
        const GRID_MAJOR = 1.0 * PIXELS_PER_METER;
        const SNAP_HEIGHT = GRID_FINE;
        const MAGNET_RADIUS = 16;
        const HOVER_DIST = 12;

        // --- Themes ---
        const THEMES = {
            blueprint: {
                bg: '#0a2240',
                gridFine: 'rgba(255,255,255,0.15)',
                gridMajor: 'rgba(255,255,255,0.3)',
                line: '#ffffff',
                text: '#ffffff',
                highlight: 'rgba(255,255,255,0.5)',
                magnet: 'rgba(255,255,255,0.8)'
            },
            white: {
                bg: '#f5f5f5',
                gridFine: 'rgba(0,0,0,0.1)',
                gridMajor: 'rgba(0,0,0,0.2)',
                line: '#000000',
                text: '#000000',
                highlight: 'rgba(0,0,0,0.5)',
                magnet: 'rgba(0,0,0,0.8)'
            },
            pink: {
                bg: '#f8d7df',
                gridFine: 'rgba(170,130,150,0.2)',
                gridMajor: 'rgba(140,100,120,0.3)',
                line: '#f8fafc',
                text: '#462d41',
                highlight: 'rgba(248,250,252,0.6)',
                magnet: '#ffffff'
            }
        };

        // --- Data Structures ---
        class Vector3 {
            constructor(x, y, z = 0) { this.x = x; this.y = y; this.z = z; }
            add(v) { return new Vector3(this.x + v.x, this.y + v.y, this.z + v.z); }
            sub(v) { return new Vector3(this.x - v.x, this.y - v.y, this.z - v.z); }
            mult(s) { return new Vector3(this.x * s, this.y * s, this.z * s); }
            dist(v) { return Math.sqrt((this.x - v.x)**2 + (this.y - v.y)**2 + (this.z - v.z)**2); }
            len() { return Math.sqrt(this.x**2 + this.y**2 + this.z**2); }
            norm() { const l = this.len(); return l === 0 ? new Vector3(0,0,0) : this.mult(1/l); }
            clone() { return new Vector3(this.x, this.y, this.z); }
        }

        class Segment {
            constructor(id, start, end) {
                this.id = id;
                this.start = start; // Vector3
                this.end = end;     // Vector3
                this.lenM = start.dist(end) / PIXELS_PER_METER;
                this.offset = 0; // Dimension offset
            }
        }

        class Wall {
            constructor(a, b, h) {
                this.a = a; // Vector3 (base)
                this.b = b; // Vector3 (base)
                this.height = h;
            }
        }

        // --- Main Application Class ---
        class App {
            constructor() {
                this.canvas = document.getElementById('main-canvas');
                this.ctx = this.canvas.getContext('2d');
                this.width = window.innerWidth;
                this.height = window.innerHeight;

                // State
                this.segments = [];
                this.walls = [];
                this.nextId = 1;
                this.themeKey = 'blueprint';
                this.theme = THEMES[this.themeKey];

                // Camera
                this.cam = {
                    pos: new Vector3(0, 0, 0), // World center
                    zoom: 1.0,
                    yaw: 0.0,
                    pitch: 90.0
                };
                // Start centered (approx)
                this.cam.pos.x = 0;
                this.cam.pos.y = 0;

                // Interaction
                this.mode = 'draw'; // draw, select, extrude, height, size
                this.snapEnabled = true;
                this.showDimensions = true;
                this.startPoint = null;
                this.magnetPoint = null;
                this.selectedIds = new Set();
                this.hoverSeg = null;
                this.keys = {};

                // Undo/Redo
                this.undoStack = [];
                this.redoStack = [];

                // Input Measurement
                this.inputVal = "";
                this.inputActive = false;

                // Mouse Dragging
                this.isDragging = false;
                this.lastMouse = {x:0, y:0};
                this.dragStart = {x:0, y:0};
                this.selectRect = null;

                // Init
                this.resize();
                window.addEventListener('resize', () => this.resize());
                this.setupInputs();

                // Start Loop
                this.lastTime = performance.now();
                requestAnimationFrame((t) => this.loop(t));

                // UI Bindings
                this.bindUI();
            }

            resize() {
                this.width = window.innerWidth;
                this.height = window.innerHeight;
                this.canvas.width = this.width;
                this.canvas.height = this.height;
            }

            bindUI() {
                const click = (id, fn) => {
                    const el = document.getElementById(id);
                    if(el) el.onclick = (e) => { e.stopPropagation(); fn(); };
                };

                click('btn-draw', () => this.setMode('draw'));
                click('btn-select', () => this.setMode('select'));
                click('btn-extrude', () => this.setMode('extrude'));
                click('btn-height', () => this.setMode('height'));
                click('btn-dimension', () => this.setMode('size'));
                click('btn-undo', () => this.undo());
                click('btn-redo', () => this.redo());
                click('btn-clear', () => this.clearAll());
                click('btn-theme', () => this.cycleTheme());
                click('btn-help', () => {
                    const m = document.getElementById('help-modal');
                    m.classList.toggle('visible');
                });

                // Make App global for inline onclicks
                window.app = this;
            }

            setMode(m) {
                this.mode = m;
                this.startPoint = null;
                this.selectedIds.clear();
                this.updateToolbar();
                this.showToast("Mode: " + m.toUpperCase());
            }

            updateToolbar() {
                document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
                const map = {
                    'draw': 'btn-draw', 'select': 'btn-select', 'extrude': 'btn-extrude',
                    'height': 'btn-height', 'size': 'btn-dimension'
                };
                if(map[this.mode]) document.getElementById(map[this.mode]).classList.add('active');
            }

            cycleTheme() {
                const keys = Object.keys(THEMES);
                const idx = keys.indexOf(this.themeKey);
                this.themeKey = keys[(idx + 1) % keys.length];
                this.theme = THEMES[this.themeKey];
                this.showToast(`Theme: ${this.themeKey.toUpperCase()}`);
            }

            // --- Math & Transforms ---

            worldToScreen(p) { // p is Vector3
                const vx = p.x - this.cam.pos.x;
                const vy = p.y - this.cam.pos.y;
                const vz = p.z; // assuming cam z=0 logic from python

                // Rotate Yaw
                const cyaw = Math.cos(this.cam.yaw);
                const syaw = Math.sin(this.cam.yaw);
                const rx = vx * cyaw + vy * syaw;
                const ry = -vx * syaw + vy * cyaw;
                const rz = vz;

                // Pitch
                const pitchRad = (this.cam.pitch - 90) * Math.PI / 180;
                const c = Math.cos(pitchRad);
                const s = Math.sin(pitchRad);

                // Projection
                const px = rx;
                const py = ry * c - rz * s;
                // pz = ry * s + rz * c (depth)

                const sx = px * this.cam.zoom + this.width * 0.5;
                const sy = py * this.cam.zoom + this.height * 0.5;

                return { x: sx, y: sy };
            }

            screenToWorldGround(sx, sy) {
                // Inverse of worldToScreen assuming z=0
                // (sx - w/2)/zoom = px
                // (sy - h/2)/zoom = py

                const px = (sx - this.width * 0.5) / this.cam.zoom;
                const py = (sy - this.height * 0.5) / this.cam.zoom;

                const pitchRad = (this.cam.pitch - 90) * Math.PI / 180;
                const c = Math.cos(pitchRad);
                // if pitch is -90 (0 deg), c=0, s=-1. py = -rz * -1 = rz? No, z=0
                // py = ry * c - 0 * s => ry = py / c
                // If c is tiny (pitch ~ 90), ry is unstable, but normally pitch <= 90.
                // Wait, Python code: pitch 90 means top down. 90-90=0. c=1, s=0. py = ry.

                let ry = 0;
                if (Math.abs(c) > 1e-6) ry = py / c;

                const rx = px;

                // Inverse Yaw
                const cyaw = Math.cos(this.cam.yaw);
                const syaw = Math.sin(this.cam.yaw);

                // rx = vx*cyaw + vy*syaw
                // ry = -vx*syaw + vy*cyaw
                // Solve for vx, vy:
                // vx = rx*cyaw - ry*syaw
                // vy = rx*syaw + ry*cyaw

                const vx = rx * cyaw - ry * syaw;
                const vy = rx * syaw + ry * cyaw;

                return new Vector3(vx + this.cam.pos.x, vy + this.cam.pos.y, 0);
            }

            computeHeight(base, sy) {
                // Given a base point (world) and a screen Y, find Z
                const pitchRad = (this.cam.pitch - 90) * Math.PI / 180;
                const s = Math.sin(pitchRad);
                if (Math.abs(s) < 1e-6) return 0;

                const c = Math.cos(pitchRad);
                const vx = base.x - this.cam.pos.x;
                const vy = base.y - this.cam.pos.y;
                const cx = Math.cos(this.cam.yaw);
                const sx = Math.sin(this.cam.yaw);

                // const rx = vx * cx + vy * sx;
                const ry = -vx * sx + vy * cx;

                const py = (sy - this.height * 0.5) / this.cam.zoom;

                // py = ry * c - rz * s  => rz = (ry * c - py) / s
                const z = (ry * c - py) / s;
                return z;
            }

            snapXY(v) {
                if (!this.snapEnabled) return v;
                return new Vector3(
                    Math.round(v.x / GRID_FINE) * GRID_FINE,
                    Math.round(v.y / GRID_FINE) * GRID_FINE,
                    v.z
                );
            }

            snapZ(z) {
                if (!this.snapEnabled) return z;
                return Math.round(z / SNAP_HEIGHT) * SNAP_HEIGHT;
            }

            // --- Drawing Logic ---

            loop(now) {
                const dt = (now - this.lastTime) / 1000;
                this.lastTime = now;

                this.update(dt);
                this.draw();

                requestAnimationFrame((t) => this.loop(t));
            }

            update(dt) {
                // Camera controls
                const speed = (this.keys['Shift'] ? 600 : 200) * PIXELS_PER_METER * dt * 0.01; // Scale factor
                const rotSpeed = 2.0 * dt;

                // Pan relative to yaw
                const up = new Vector3(-Math.sin(this.cam.yaw), Math.cos(this.cam.yaw));
                const right = new Vector3(Math.cos(this.cam.yaw), Math.sin(this.cam.yaw));

                if (this.keys['w']) this.cam.pos = this.cam.pos.add(up.mult(speed));
                if (this.keys['s']) this.cam.pos = this.cam.pos.sub(up.mult(speed));
                if (this.keys['d']) this.cam.pos = this.cam.pos.add(right.mult(speed));
                if (this.keys['a']) this.cam.pos = this.cam.pos.sub(right.mult(speed));

                if (this.keys['ArrowLeft']) this.cam.yaw += rotSpeed;
                if (this.keys['ArrowRight']) this.cam.yaw -= rotSpeed;
                if (this.keys['ArrowUp']) this.cam.zoom *= 1.02;
                if (this.keys['ArrowDown']) this.cam.zoom /= 1.02;

                // Update HUD info
                const mouseWorld = this.screenToWorldGround(this.lastMouse.x, this.lastMouse.y);
                document.getElementById('hud-status').innerText = `Mode: ${this.mode.toUpperCase()} | Pos: ${(mouseWorld.x/PIXELS_PER_METER).toFixed(2)}, ${(mouseWorld.y/PIXELS_PER_METER).toFixed(2)} m`;
                document.getElementById('hud-stats').innerText = `Segs: ${this.segments.length} | Walls: ${this.walls.length} | Snap: ${this.snapEnabled?'ON':'OFF'}`;
                document.getElementById('hud-cam').innerText = `Zoom: ${this.cam.zoom.toFixed(2)}x | Pitch: ${this.cam.pitch}°`;

                // Magnet Logic
                this.updateMagnet();
            }

            updateMagnet() {
                this.magnetPoint = null;
                if (!this.snapEnabled || this.mode === 'extrude') return;

                // Find closest endpoint
                let bestDist = MAGNET_RADIUS;
                let bestPt = null;

                for(let s of this.segments) {
                    for(let pt of [s.start, s.end]) {
                        if(Math.abs(pt.z) > 0.1) continue; // Only snap to ground points
                        const scr = this.worldToScreen(pt);
                        const d = Math.hypot(scr.x - this.lastMouse.x, scr.y - this.lastMouse.y);
                        if(d < bestDist) {
                            bestDist = d;
                            bestPt = pt;
                        }
                    }
                }
                this.magnetPoint = bestPt;
            }

            getSnappedPoint(mx, my) {
                if (this.snapEnabled && this.magnetPoint) return this.magnetPoint;
                const w = this.screenToWorldGround(mx, my);
                return this.snapXY(w);
            }

            draw() {
                const ctx = this.ctx;
                ctx.fillStyle = this.theme.bg;
                ctx.fillRect(0, 0, this.width, this.height);

                // Grid
                this.drawGrid(ctx);

                // Walls (Sorted by depth roughly)
                // Painter's algorithm sort
                const sortedWalls = [...this.walls].sort((a, b) => {
                    // Simple sort by average Y relative to cam
                    // Rotated Y check is better
                    return 0; // Skip complex sorting for MVP, transparency handles it mostly or draw order
                });
                // Actually need proper projection sort.
                // Reusing python Logic: max(ay, by)

                const getSortY = (pt) => {
                    const vx = pt.x - this.cam.pos.x;
                    const vy = pt.y - this.cam.pos.y;
                    const cx = Math.cos(this.cam.yaw);
                    const sx = Math.sin(this.cam.yaw);
                    return -vx * sx + vy * cx;
                };

                sortedWalls.sort((a, b) => {
                    const ay = Math.max(getSortY(a.a), getSortY(a.b));
                    const by = Math.max(getSortY(b.a), getSortY(b.b));
                    return ay - by;
                });

                for (let w of sortedWalls) {
                    this.drawWall(ctx, w);
                }

                // Segments
                for (let s of this.segments) {
                    this.drawSegment(ctx, s);
                }

                // Preview
                if (this.startPoint) {
                    const startScr = this.worldToScreen(this.startPoint);
                    let endScr;
                    let valM = parseFloat(this.inputVal);

                    if (this.mode === 'height') {
                        let z = isNaN(valM) ? this.computeHeight(this.startPoint, this.lastMouse.y) : valM * PIXELS_PER_METER;
                        if(this.snapEnabled) z = this.snapZ(z);
                        const end = new Vector3(this.startPoint.x, this.startPoint.y, z);
                        endScr = this.worldToScreen(end);
                        this.drawLabel(ctx, `h=${(z/PIXELS_PER_METER).toFixed(2)}m`, endScr.x + 10, endScr.y);
                    } else {
                        // Length mode
                        const curr = this.getSnappedPoint(this.lastMouse.x, this.lastMouse.y);
                        let end = curr;
                        if (!isNaN(valM)) {
                            // Direction vector
                            let dir = curr.sub(this.startPoint).norm();
                            if (dir.len() === 0) dir = new Vector3(1,0,0);
                            end = this.startPoint.add(dir.mult(valM * PIXELS_PER_METER));
                        }
                        endScr = this.worldToScreen(end);

                        const len = this.startPoint.dist(end) / PIXELS_PER_METER;
                        const mid = {x: (startScr.x + endScr.x)/2, y: (startScr.y + endScr.y)/2 };
                        if (this.showDimensions) this.drawLabel(ctx, `${len.toFixed(2)}m`, mid.x, mid.y - 15);
                    }

                    ctx.strokeStyle = this.theme.line;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(startScr.x, startScr.y);
                    ctx.lineTo(endScr.x, endScr.y);
                    ctx.stroke();
                }

                // Selection Box
                if (this.mode === 'select' && this.isDragging && this.selectRect) {
                    ctx.fillStyle = 'rgba(96, 205, 255, 0.2)';
                    ctx.strokeStyle = '#60cdff';
                    ctx.fillRect(this.selectRect.x, this.selectRect.y, this.selectRect.w, this.selectRect.h);
                    ctx.strokeRect(this.selectRect.x, this.selectRect.y, this.selectRect.w, this.selectRect.h);
                }

                // Magnet Indicator
                if (this.magnetPoint) {
                    const scr = this.worldToScreen(this.magnetPoint);
                    ctx.strokeStyle = this.theme.magnet;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.arc(scr.x, scr.y, 8, 0, Math.PI*2);
                    ctx.stroke();
                }

                // Select Hover / Highlight
                if (this.mode === 'select' && !this.isDragging) {
                    this.updateHover();
                    if (this.hoverSeg) {
                        this.drawSegmentHighlight(ctx, this.hoverSeg, 'rgba(255, 255, 255, 0.4)');
                    }
                }
            }

            drawGrid(ctx) {
                // Approximate visible area
                // Just drawing a big enough grid around camera pos for now
                const range = this.width / this.cam.zoom + 500;
                const startX = Math.floor((this.cam.pos.x - range)/GRID_FINE)*GRID_FINE;
                const endX = Math.ceil((this.cam.pos.x + range)/GRID_FINE)*GRID_FINE;
                const startY = Math.floor((this.cam.pos.y - range)/GRID_FINE)*GRID_FINE;
                const endY = Math.ceil((this.cam.pos.y + range)/GRID_FINE)*GRID_FINE;

                ctx.lineWidth = 1;

                // X Lines
                for(let x=startX; x<=endX; x+=GRID_FINE) {
                    const isMajor = Math.abs(x % GRID_MAJOR) < 1;
                    ctx.strokeStyle = isMajor ? this.theme.gridMajor : this.theme.gridFine;
                    const p1 = this.worldToScreen(new Vector3(x, startY, 0));
                    const p2 = this.worldToScreen(new Vector3(x, endY, 0));
                    ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
                }
                // Y Lines
                for(let y=startY; y<=endY; y+=GRID_FINE) {
                    const isMajor = Math.abs(y % GRID_MAJOR) < 1;
                    ctx.strokeStyle = isMajor ? this.theme.gridMajor : this.theme.gridFine;
                    const p1 = this.worldToScreen(new Vector3(startX, y, 0));
                    const p2 = this.worldToScreen(new Vector3(endX, y, 0));
                    ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
                }
            }

            drawSegment(ctx, s) {
                const p1 = this.worldToScreen(s.start);
                const p2 = this.worldToScreen(s.end);

                const isSelected = this.selectedIds.has(s.id);
                ctx.strokeStyle = isSelected ? '#60cdff' : this.theme.line;
                ctx.lineWidth = isSelected ? 3 : 2;

                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();

                // Dims
                if (this.showDimensions && !isSelected) {
                    // Logic to draw dimension text slightly offset
                    const mx = (p1.x + p2.x)/2;
                    const my = (p1.y + p2.y)/2;

                    if (Math.abs(s.start.z - s.end.z) > 1) {
                         // Height line
                         const h = Math.abs(s.start.z - s.end.z) / PIXELS_PER_METER;
                         this.drawLabel(ctx, `h=${h.toFixed(2)}`, mx + 10, my);
                    } else {
                         this.drawLabel(ctx, `${s.lenM.toFixed(2)}`, mx, my - 10);
                    }
                }
            }

            drawSegmentHighlight(ctx, s, color) {
                const p1 = this.worldToScreen(s.start);
                const p2 = this.worldToScreen(s.end);
                ctx.strokeStyle = color;
                ctx.lineWidth = 4;
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }

            drawWall(ctx, w) {
                const h = w.height;
                const p1 = this.worldToScreen(w.a);
                const p2 = this.worldToScreen(w.b);
                const p3 = this.worldToScreen(new Vector3(w.b.x, w.b.y, h));
                const p4 = this.worldToScreen(new Vector3(w.a.x, w.a.y, h));

                ctx.fillStyle = this.theme.highlight;
                ctx.strokeStyle = this.theme.line;
                ctx.lineWidth = 1;

                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.lineTo(p3.x, p3.y);
                ctx.lineTo(p4.x, p4.y);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
            }

            drawLabel(ctx, text, x, y) {
                ctx.fillStyle = this.theme.text;
                ctx.font = '12px sans-serif';
                ctx.strokeStyle = this.theme.bg;
                ctx.lineWidth = 2;
                ctx.strokeText(text, x, y);
                ctx.fillText(text, x, y);
            }

            // --- Input Handling ---

            setupInputs() {
                // Keyboard
                window.addEventListener('keydown', (e) => {
                    this.keys[e.key] = true;
                    if (this.inputActive && e.key === 'Enter') {
                        // Confirm input
                        return; // Handled by mode logic
                    }
                    if (!this.inputActive) {
                        // Shortcuts
                        if (e.key === 'm') { this.showDimensions = !this.showDimensions; }
                        else if (e.key === 'g') { this.snapEnabled = !this.snapEnabled; }
                        else if (e.key === 'z') { this.undo(); }
                        else if (e.key === 'y') { this.redo(); }
                        else if (e.key === 'c') { this.clearAll(); }
                        else if (e.key === 'h') { this.setMode('height'); }
                        else if (e.key === 'Escape') { this.setMode('select'); this.startPoint = null; this.inputVal=""; }
                        else if (e.key >= '0' && e.key <= '9') {
                             // Start typing input
                             this.inputVal += e.key;
                             this.updateInputUI();
                        }
                    } else {
                        if (e.key === 'Backspace') {
                            this.inputVal = this.inputVal.slice(0, -1);
                            this.updateInputUI();
                        } else if ((e.key >= '0' && e.key <= '9') || e.key === '.') {
                            this.inputVal += e.key;
                            this.updateInputUI();
                        }
                    }
                });

                window.addEventListener('keyup', (e) => {
                    this.keys[e.key] = false;
                });

                // Mouse
                this.canvas.addEventListener('mousedown', (e) => {
                    if (e.button === 0) { // Left
                        if (this.mode === 'select') {
                            this.isDragging = true;
                            this.dragStart = {x: e.clientX, y: e.clientY};
                            this.selectRect = {x: e.clientX, y: e.clientY, w:0, h:0};

                            // Check click select
                            this.updateHover();
                            if(this.hoverSeg) {
                                if(e.shiftKey) {
                                    if(this.selectedIds.has(this.hoverSeg.id)) this.selectedIds.delete(this.hoverSeg.id);
                                    else this.selectedIds.add(this.hoverSeg.id);
                                } else {
                                    this.selectedIds.clear();
                                    this.selectedIds.add(this.hoverSeg.id);
                                }
                            } else if (!e.shiftKey) {
                                // Clear if clicking empty space
                                // But wait, dragging starts here.
                            }
                        } else if (this.mode === 'draw' || this.mode === 'height') {
                             const pt = this.getSnappedPoint(e.clientX, e.clientY);
                             if (!this.startPoint) {
                                 this.startPoint = pt;
                             } else {
                                 // Finish segment
                                 // Check input val
                                 let end = pt;
                                 let val = parseFloat(this.inputVal);
                                 if (!isNaN(val)) {
                                     // Directional
                                     // ... handled in finish
                                 }
                                 this.finishSegment(pt);
                             }
                        } else if (this.mode === 'extrude') {
                             // Select line to extrude or finish extrude
                             // Logic: If selection exists, extrude it. Else select.
                        }
                    }
                });

                this.canvas.addEventListener('mousemove', (e) => {
                    this.lastMouse = {x: e.clientX, y: e.clientY};
                    if (this.isDragging && this.mode === 'select') {
                        const w = e.clientX - this.dragStart.x;
                        const h = e.clientY - this.dragStart.y;
                        this.selectRect = {x: this.dragStart.x, y: this.dragStart.y, w, h};
                    }
                });

                this.canvas.addEventListener('mouseup', (e) => {
                    if (e.button === 0) {
                        if (this.isDragging && this.mode === 'select') {
                            // Lasso select logic
                            // If rect is small, treat as click (handled in mousedown partially)
                            if (Math.abs(this.selectRect.w) > 5 || Math.abs(this.selectRect.h) > 5) {
                                // Find segments inside rect
                                // Simplified: check midpoint
                                // Proper: line intersection with rect
                                // TODO: Implement lasso
                                // For now, just reset
                            } else {
                                 if(!this.hoverSeg && !e.shiftKey) this.selectedIds.clear();
                            }
                            this.isDragging = false;
                            this.selectRect = null;
                        }
                    }
                });

                this.canvas.addEventListener('wheel', (e) => {
                     const factor = e.deltaY > 0 ? 0.9 : 1.1;
                     this.cam.zoom *= factor;
                });
            }

            updateInputUI() {
                const el = document.getElementById('measure-input');
                if (this.inputVal.length > 0) {
                    el.style.display = 'block';
                    el.innerText = this.inputVal + ' m';
                    this.inputActive = true;
                } else {
                    el.style.display = 'none';
                    this.inputActive = false;
                }
            }

            finishSegment(endPt) {
                // If input val exists, use it
                let finalEnd = endPt;
                let val = parseFloat(this.inputVal);

                if (!isNaN(val)) {
                     if (this.mode === 'height') {
                         finalEnd = new Vector3(this.startPoint.x, this.startPoint.y, val * PIXELS_PER_METER);
                     } else {
                         let dir = endPt.sub(this.startPoint).norm();
                         if (dir.len() === 0) dir = new Vector3(1,0,0);
                         finalEnd = this.startPoint.add(dir.mult(val * PIXELS_PER_METER));
                     }
                }

                if (this.mode === 'height') {
                    // Force height logic if manual
                    if (isNaN(val)) {
                        const z = this.computeHeight(this.startPoint, this.lastMouse.y);
                        let finalZ = this.snapEnabled ? this.snapZ(z) : z;
                        finalEnd = new Vector3(this.startPoint.x, this.startPoint.y, finalZ);
                    }
                }

                if (this.startPoint.dist(finalEnd) > 0.1) {
                    const seg = new Segment(this.nextId++, this.startPoint, finalEnd);
                    this.segments.push(seg);
                    this.undoStack.push({type: 'add', obj: seg});
                    this.redoStack = [];
                }

                this.startPoint = null;
                this.inputVal = "";
                this.updateInputUI();
            }

            updateHover() {
                this.hoverSeg = null;
                let bestD = HOVER_DIST;
                const m = {x: this.lastMouse.x, y: this.lastMouse.y};

                for(let s of this.segments) {
                    const p1 = this.worldToScreen(s.start);
                    const p2 = this.worldToScreen(s.end);

                    // Dist point to line segment
                    const l2 = (p1.x-p2.x)**2 + (p1.y-p2.y)**2;
                    if (l2 == 0) continue;
                    let t = ((m.x-p1.x)*(p2.x-p1.x) + (m.y-p1.y)*(p2.y-p1.y)) / l2;
                    t = Math.max(0, Math.min(1, t));
                    const px = p1.x + t * (p2.x - p1.x);
                    const py = p1.y + t * (p2.y - p1.y);
                    const d = Math.sqrt((m.x-px)**2 + (m.y-py)**2);

                    if (d < bestD) {
                        bestD = d;
                        this.hoverSeg = s;
                    }
                }
            }

            undo() {
                if (this.undoStack.length === 0) return;
                const act = this.undoStack.pop();
                if (act.type === 'add') {
                    this.segments = this.segments.filter(s => s.id !== act.obj.id);
                    this.redoStack.push(act);
                }
            }

            redo() {
                 if (this.redoStack.length === 0) return;
                 const act = this.redoStack.pop();
                 if (act.type === 'add') {
                     this.segments.push(act.obj);
                     this.undoStack.push(act);
                 }
            }

            clearAll() {
                this.segments = [];
                this.walls = [];
                this.startPoint = null;
                this.undoStack = [];
                this.redoStack = [];
                this.nextId = 1;
            }

            setPitch(deg) {
                this.cam.pitch = deg;
            }

            showToast(msg) {
                const t = document.getElementById('toast');
                t.innerText = msg;
                t.style.opacity = 1;
                setTimeout(() => t.style.opacity = 0, 2000);
            }

            exportPNG() {
                const link = document.createElement('a');
                link.download = 'denah_rumah.png';
                link.href = this.canvas.toDataURL();
                link.click();
            }

            async exportPDF() {
                const { jsPDF } = window.jspdf;
                const doc = new jsPDF('l', 'mm', 'a4');
                const imgData = this.canvas.toDataURL('image/png');
                const width = doc.internal.pageSize.getWidth();
                const height = doc.internal.pageSize.getHeight();
                doc.addImage(imgData, 'PNG', 0, 0, width, height);
                doc.save('denah_rumah.pdf');
            }
        }

        // --- Start ---
        window.onload = () => {
            new App();
        };

    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
