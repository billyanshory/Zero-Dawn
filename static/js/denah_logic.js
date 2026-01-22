
/* Floor Plan Drawer - Web Logic (ES2025) */

// Constants
const PIXELS_PER_METER = 100;
const GRID_FINE_SPACING = 0.25 * PIXELS_PER_METER; // 25 px
const GRID_MAJOR_SPACING = 1.0 * PIXELS_PER_METER; // 100 px
const SNAP_HEIGHT = GRID_FINE_SPACING;
const MAGNET_LOCK_RADIUS_PX = 12;
const MAGNET_RELEASE_RADIUS_PX = 16;
const MAGNET_HOVER_RADIUS_PX = 24;
const HOVER_DIST_PX = 10;
const SELECT_DIST_PX = 12;
const MAX_LINE_LEN_M = 200.0;
const MAX_HEIGHT_M = 50.0;
const STEP_FINE_M = 0.05;
const STEP_COARSE_M = 0.5;
const SIZE_OFFSET_STEP = 2.0;
const SIZE_OVERSHOOT_PX = 12;

// Enums
const MeasureMode = {
    LEN: 1,
    HGT: 2
};

// Vector3 Helper
class Vector3 {
    constructor(x, y, z) {
        this.x = x || 0;
        this.y = y || 0;
        this.z = z || 0;
    }
    copy() { return new Vector3(this.x, this.y, this.z); }
    add(v) { return new Vector3(this.x + v.x, this.y + v.y, this.z + v.z); }
    sub(v) { return new Vector3(this.x - v.x, this.y - v.y, this.z - v.z); }
    mul(s) { return new Vector3(this.x * s, this.y * s, this.z * s); }
    div(s) { return new Vector3(this.x / s, this.y / s, this.z / s); }
    distanceTo(v) {
        return Math.sqrt((this.x - v.x) ** 2 + (this.y - v.y) ** 2 + (this.z - v.z) ** 2);
    }
    length() { return Math.sqrt(this.x ** 2 + this.y ** 2 + this.z ** 2); }
    lengthSq() { return this.x ** 2 + this.y ** 2 + this.z ** 2; }
    normalize() {
        const len = this.length();
        return len > 0 ? this.div(len) : new Vector3(0, 0, 0);
    }
    dot(v) { return this.x * v.x + this.y * v.y + this.z * v.z; }
}

// Vector2 Helper
class Vector2 {
    constructor(x, y) {
        this.x = x || 0;
        this.y = y || 0;
    }
    distanceTo(v) { return Math.sqrt((this.x - v.x) ** 2 + (this.y - v.y) ** 2); }
    sub(v) { return new Vector2(this.x - v.x, this.y - v.y); }
    add(v) { return new Vector2(this.x + v.x, this.y + v.y); }
    mul(s) { return new Vector2(this.x * s, this.y * s); }
    length() { return Math.sqrt(this.x ** 2 + this.y ** 2); }
    lengthSq() { return this.x ** 2 + this.y ** 2; }
    dot(v) { return this.x * v.x + this.y * v.y; }
}

// Data Structures
class LineSegment {
    constructor(id, start, end, length_m) {
        this.id = id;
        this.start = start; // Vector3
        this.end = end;     // Vector3
        this.length_m = length_m;
    }
}

class WallFace {
    constructor(a, b, height) {
        this.a = a; // Vector3 (bottom)
        this.b = b; // Vector3 (bottom)
        this.height = height;
    }
}

// Themes
const THEMES = {
    blueprint: {
        bg: '#0a2240',
        grid_fine: 'rgba(255, 255, 255, 0.15)',
        grid_major: 'rgba(255, 255, 255, 0.3)',
        line_color: '#ffffff',
        text_primary: '#ffffff',
        text_muted: '#969696',
        text_shadow: '#000000',
        hover_glow: 'rgba(255, 255, 255, 0.6)',
        magnet_color: 'rgba(255, 255, 255, 1.0)'
    },
    white: {
        bg: '#f5f5f5',
        grid_fine: 'rgba(0, 0, 0, 0.15)',
        grid_major: 'rgba(0, 0, 0, 0.3)',
        line_color: '#000000',
        text_primary: '#000000',
        text_muted: '#646464',
        text_shadow: '#ffffff',
        hover_glow: 'rgba(0, 0, 0, 0.6)',
        magnet_color: 'rgba(0, 0, 0, 1.0)'
    },
    pink: {
        bg: '#f8d7df',
        grid_fine: 'rgba(170, 130, 150, 0.15)',
        grid_major: 'rgba(140, 100, 120, 0.3)',
        line_color: '#f8fafc',
        text_primary: '#462d41',
        text_muted: '#826478',
        text_shadow: '#fff0f5',
        hover_glow: 'rgba(248, 250, 252, 0.6)',
        magnet_color: 'rgba(248, 250, 252, 1.0)'
    }
};

class App {
    constructor() {
        this.canvas = document.getElementById('app-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.resize();

        // State
        this.themeMode = 'blueprint';
        this.themeSequence = ['blueprint', 'white', 'pink'];

        // Camera
        this.camPos = new Vector2(this.width / 2, this.height / 2);
        this.camZoom = 1.0;
        this.camYaw = 0.0;
        this.camPitchDeg = 90.0;

        // Data
        this.segments = [];
        this.walls = [];
        this.undoStack = [];
        this.redoStack = [];
        this.nextId = 1;

        // Interaction State
        this.startPoint = null; // Vector3
        this.heightMode = false;
        this.extrudeMode = false;
        this.selectMode = false;
        this.sizeMode = false;
        this.snapEnabled = true;
        this.showDimensions = true;

        this.extrudeTargets = [];
        this.extrudeHover = null;
        this.extrudeHeight = 0.0;

        this.selectedIds = new Set();
        this.hoverHit = null;
        this.sizeHoverSeg = null;
        this.sizeEditSeg = null;
        this.dimensionOffsets = {}; // id -> float

        // Magnet
        this.magnetPoint = null;
        this.magnetLocked = false;
        this.magnetAlpha = 0.0;

        // Input
        this.keys = {};
        this.mouse = new Vector2(0, 0);
        this.mouseDownPos = new Vector2(0, 0);
        this.dragging = false;
        this.dragSelect = false;
        this.dragRect = null;
        this.lastPreviewDir = null;

        // Measurement Input
        this.inputActive = false;
        this.inputMode = MeasureMode.LEN;
        this.inputText = '';
        this.inputValueM = null;

        // Bindings
        window.addEventListener('resize', () => this.resize());
        window.addEventListener('keydown', (e) => this.onKeyDown(e));
        window.addEventListener('keyup', (e) => this.onKeyUp(e));
        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this.onWheel(e), { passive: false });
        // Context menu disable for right click
        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());

        this.setupUI();
        this.loop();
    }

    resize() {
        this.width = window.innerWidth;
        this.height = window.innerHeight;
        this.canvas.width = this.width;
        this.canvas.height = this.height;
    }

    setupUI() {
        document.getElementById('btn-help').onclick = () => document.getElementById('help-modal').style.display = 'flex';
        document.getElementById('close-help').onclick = () => document.getElementById('help-modal').style.display = 'none';

        document.getElementById('btn-extrude').onclick = () => this.toggleMode('extrude');
        document.getElementById('btn-select').onclick = () => this.toggleMode('select');
        document.getElementById('btn-size').onclick = () => this.toggleMode('size');
        document.getElementById('btn-theme').onclick = () => this.toggleTheme();

        document.getElementById('btn-undo').onclick = () => this.undo();
        document.getElementById('btn-redo').onclick = () => this.redo();
        document.getElementById('btn-clear').onclick = () => this.clear();
        document.getElementById('btn-export').onclick = () => this.exportCanvas();

        document.querySelectorAll('.cam-btn').forEach(btn => {
            btn.onclick = () => {
                const pitch = parseFloat(btn.dataset.pitch);
                this.camPitchDeg = pitch;
                if (this.heightMode && this.camPitchDeg >= 90) {
                    this.heightMode = false;
                    this.startPoint = null;
                }
            };
        });
    }

    toggleMode(mode) {
        if (mode === 'extrude') {
            this.extrudeMode = !this.extrudeMode;
            if (this.extrudeMode) {
                this.heightMode = false;
                this.selectMode = false;
                this.sizeMode = false;
                this.startPoint = null;
                if (this.selectedIds.size > 0) {
                    this.extrudeTargets = this.segments.filter(s => this.selectedIds.has(s.id) && Math.abs(s.start.z) < 1e-6 && Math.abs(s.end.z) < 1e-6);
                    this.extrudeHeight = 0.0;
                }
            } else {
                this.extrudeTargets = [];
            }
        } else if (mode === 'select') {
            this.selectMode = !this.selectMode;
            if (this.selectMode) {
                this.extrudeMode = false;
                this.heightMode = false;
                this.sizeMode = false;
                this.startPoint = null;
            } else {
                this.selectedIds.clear();
            }
        } else if (mode === 'size') {
            this.sizeMode = !this.sizeMode;
            if (this.sizeMode) {
                this.extrudeMode = false;
                this.heightMode = false;
                this.selectMode = false;
                this.startPoint = null;
            }
        }
        this.updateButtons();
    }

    toggleTheme() {
        const idx = this.themeSequence.indexOf(this.themeMode);
        this.themeMode = this.themeSequence[(idx + 1) % this.themeSequence.length];
        this.showToast(`Theme: ${this.themeMode}`);
    }

    updateButtons() {
        document.getElementById('btn-extrude').classList.toggle('active', this.extrudeMode);
        document.getElementById('btn-select').classList.toggle('active', this.selectMode);
        document.getElementById('btn-size').classList.toggle('active', this.sizeMode);
    }

    showToast(msg) {
        const t = document.getElementById('toast');
        t.innerText = msg;
        t.classList.add('show');
        setTimeout(() => t.classList.remove('show'), 2000);
    }

    // Math & Projections
    worldToScreen(p) {
        const x = p.x, y = p.y, z = p.z;
        const vx = x - this.camPos.x;
        const vy = y - this.camPos.y;

        const cx = Math.cos(this.camYaw);
        const sx = Math.sin(this.camYaw);

        const rx = vx * cx + vy * sx;
        const ry = -vx * sx + vy * cx;
        const rz = z;

        const pitchRad = (this.camPitchDeg - 90.0) * (Math.PI / 180.0);
        const c = Math.cos(pitchRad);
        const s = Math.sin(pitchRad);

        const px = rx;
        const py = ry * c - rz * s;
        // pz would be ry * s + rz * c

        const sx_screen = px * this.camZoom + this.width * 0.5;
        const sy_screen = py * this.camZoom + this.height * 0.5;

        return new Vector2(sx_screen, sy_screen);
    }

    screenToWorldGround(s) {
        const px = (s.x - this.width * 0.5) / this.camZoom;
        const py = (s.y - this.height * 0.5) / this.camZoom;

        const pitchRad = (this.camPitchDeg - 90.0) * (Math.PI / 180.0);
        const c = Math.cos(pitchRad);
        // If looking mostly top down, we can unproject to z=0

        const cx = Math.cos(this.camYaw);
        const sx = Math.sin(this.camYaw);

        // ry * c - 0 * s = py => ry = py / c
        let ry = 0;
        if (Math.abs(c) > 1e-6) {
            ry = py / c;
        }

        const rx = px;

        // Inverse rotation
        // rx = vx * cx + vy * sx
        // ry = -vx * sx + vy * cx
        // Solve for vx, vy
        // vx = rx * cx - ry * sx
        // vy = rx * sx + ry * cx

        const vx = rx * cx - ry * sx;
        const vy = rx * sx + ry * cx;

        return new Vector3(vx + this.camPos.x, vy + this.camPos.y, 0);
    }

    computeHeight(base, screenY) {
        const pitchRad = (this.camPitchDeg - 90.0) * (Math.PI / 180.0);
        const s = Math.sin(pitchRad);
        if (Math.abs(s) < 1e-6) return 0.0;

        const c = Math.cos(pitchRad);
        const vx = base.x - this.camPos.x;
        const vy = base.y - this.camPos.y;

        const cx = Math.cos(this.camYaw);
        const sx = Math.sin(this.camYaw);

        // const rx = vx * cx + vy * sx;
        const ry = -vx * sx + vy * cx;

        const py = (screenY - this.height * 0.5) / this.camZoom;
        // py = ry * c - z * s
        // z * s = ry * c - py
        // z = (ry * c - py) / s

        return (ry * c - py) / s;
    }

    snapXY(v) {
        if (!this.snapEnabled) return v;
        const x = Math.round(v.x / GRID_FINE_SPACING) * GRID_FINE_SPACING;
        const y = Math.round(v.y / GRID_FINE_SPACING) * GRID_FINE_SPACING;
        return new Vector3(x, y, v.z);
    }

    snapZ(z) {
        if (!this.snapEnabled) return z;
        return Math.round(z / SNAP_HEIGHT) * SNAP_HEIGHT;
    }

    updateMagnet(mousePos) {
        if (!this.snapEnabled || this.extrudeMode) {
            this.magnetPoint = null;
            this.magnetLocked = false;
            return;
        }

        if (this.magnetLocked && this.magnetPoint) {
            const sp = this.worldToScreen(this.magnetPoint);
            if (mousePos.distanceTo(sp) <= MAGNET_RELEASE_RADIUS_PX) return;
            this.magnetLocked = false;
            this.magnetPoint = null;
        }

        let bestPoint = null;
        let bestDist = MAGNET_HOVER_RADIUS_PX + 1;

        // Iterate segments points
        for (const seg of this.segments) {
            for (const pt of [seg.start, seg.end]) {
                if (Math.abs(pt.z) > 1e-6) continue; // Only snap to ground points for simplicity or per logic
                const sp = this.worldToScreen(pt);
                const dist = mousePos.distanceTo(sp);
                if (dist <= MAGNET_HOVER_RADIUS_PX && dist < bestDist) {
                    bestDist = dist;
                    bestPoint = pt;
                }
            }
        }

        this.magnetPoint = bestPoint;
        this.magnetLocked = (bestPoint !== null && bestDist <= MAGNET_LOCK_RADIUS_PX);
    }

    getSnappedPoint(mousePos) {
        this.updateMagnet(mousePos);
        const ignoreMagnet = this.inputActive && this.inputMode === MeasureMode.LEN && this.inputText.length > 0;
        const world = this.screenToWorldGround(mousePos);

        if (this.snapEnabled && this.magnetPoint && this.magnetLocked && !ignoreMagnet) {
            return this.magnetPoint;
        }
        if (this.snapEnabled) {
            return this.snapXY(world);
        }
        return world;
    }

    // Actions
    addSegment(start, end) {
        const lenPx = start.distanceTo(end);
        if (lenPx === 0) return;
        const lenM = lenPx / PIXELS_PER_METER;

        const seg = new LineSegment(this.nextId++, start, end, lenM);
        this.segments.push(seg);
        this.undoStack.push({ type: 'line', obj: seg });
        this.redoStack = [];
    }

    addWall(seg, height) {
        if (Math.abs(height) < 1e-6) return;
        const wall = new WallFace(
            new Vector3(seg.start.x, seg.start.y, 0),
            new Vector3(seg.end.x, seg.end.y, 0),
            height
        );
        this.walls.push(wall);
        this.undoStack.push({ type: 'wall', obj: wall });
        this.redoStack = [];
    }

    deleteSelected() {
        const removed = this.segments.filter(s => this.selectedIds.has(s.id));
        if (removed.length === 0) return;
        this.segments = this.segments.filter(s => !this.selectedIds.has(s.id));
        this.undoStack.push({ type: 'delete', obj: removed });
        this.redoStack = [];
        this.selectedIds.clear();
    }

    undo() {
        if (this.undoStack.length === 0) return;
        const action = this.undoStack.pop();
        if (action.type === 'line') {
            const idx = this.segments.indexOf(action.obj);
            if (idx > -1) this.segments.splice(idx, 1);
        } else if (action.type === 'wall') {
            const idx = this.walls.indexOf(action.obj);
            if (idx > -1) this.walls.splice(idx, 1);
        } else if (action.type === 'delete') {
            for (const seg of action.obj) this.segments.push(seg);
        } else if (action.type === 'dim_offset') {
            const { id, oldOffset } = action.obj;
            const current = this.dimensionOffsets[id] || 0.0;
            this.dimensionOffsets[id] = oldOffset;
            this.redoStack.push({ type: 'dim_offset', obj: { id, oldOffset: current } });
            return;
        }
        this.redoStack.push(action);
    }

    redo() {
        if (this.redoStack.length === 0) return;
        const action = this.redoStack.pop();
        if (action.type === 'line') {
            this.segments.push(action.obj);
        } else if (action.type === 'wall') {
            this.walls.push(action.obj);
        } else if (action.type === 'delete') {
            this.segments = this.segments.filter(s => !action.obj.includes(s));
        } else if (action.type === 'dim_offset') {
            const { id, oldOffset } = action.obj;
            const current = this.dimensionOffsets[id] || 0.0;
            this.dimensionOffsets[id] = oldOffset;
            this.undoStack.push({ type: 'dim_offset', obj: { id, oldOffset: current } });
            return;
        }
        this.undoStack.push(action);
    }

    clear() {
        this.segments = [];
        this.walls = [];
        this.dimensionOffsets = {};
        this.undoStack = [];
        this.redoStack = [];
        this.selectedIds.clear();
        this.magnetPoint = null;
        this.startPoint = null;
    }

    // Drawing
    draw() {
        const theme = THEMES[this.themeMode];
        this.ctx.fillStyle = theme.bg;
        this.ctx.fillRect(0, 0, this.width, this.height);

        this.drawGrid(theme);
        this.drawWalls(theme);
        this.drawSegments(theme);
        this.drawPreview(theme);
        this.drawMagnet(theme);

        if (this.showDimensions) this.drawDimensions(theme);
        if (this.selectMode && this.dragSelect) this.drawLasso(theme);

        this.updateHUD();
    }

    drawGrid(theme) {
        // Simple infinite grid projection approach
        // Project corners to world to find bounds
        const corners = [
            this.screenToWorldGround(new Vector2(0, 0)),
            this.screenToWorldGround(new Vector2(this.width, 0)),
            this.screenToWorldGround(new Vector2(this.width, this.height)),
            this.screenToWorldGround(new Vector2(0, this.height))
        ];

        let minX = Math.min(...corners.map(c => c.x));
        let maxX = Math.max(...corners.map(c => c.x));
        let minY = Math.min(...corners.map(c => c.y));
        let maxY = Math.max(...corners.map(c => c.y));

        // Safety clamp to prevent infinite loop on extreme zooms
        if (maxX - minX > 100000) { minX = -50000; maxX = 50000; }
        if (maxY - minY > 100000) { minY = -50000; maxY = 50000; }

        const startX = Math.floor(minX / GRID_FINE_SPACING) * GRID_FINE_SPACING;
        const endX = Math.ceil(maxX / GRID_FINE_SPACING) * GRID_FINE_SPACING;
        const startY = Math.floor(minY / GRID_FINE_SPACING) * GRID_FINE_SPACING;
        const endY = Math.ceil(maxY / GRID_FINE_SPACING) * GRID_FINE_SPACING;

        this.ctx.lineWidth = 1;

        for (let x = startX; x <= endX; x += GRID_FINE_SPACING) {
            const isMajor = Math.abs(x % GRID_MAJOR_SPACING) < 0.1;
            this.ctx.strokeStyle = isMajor ? theme.grid_major : theme.grid_fine;
            this.ctx.beginPath();
            const s = this.worldToScreen(new Vector3(x, minY, 0));
            const e = this.worldToScreen(new Vector3(x, maxY, 0));
            this.ctx.moveTo(s.x, s.y);
            this.ctx.lineTo(e.x, e.y);
            this.ctx.stroke();
        }
        for (let y = startY; y <= endY; y += GRID_FINE_SPACING) {
            const isMajor = Math.abs(y % GRID_MAJOR_SPACING) < 0.1;
            this.ctx.strokeStyle = isMajor ? theme.grid_major : theme.grid_fine;
            this.ctx.beginPath();
            const s = this.worldToScreen(new Vector3(minX, y, 0));
            const e = this.worldToScreen(new Vector3(maxX, y, 0));
            this.ctx.moveTo(s.x, s.y);
            this.ctx.lineTo(e.x, e.y);
            this.ctx.stroke();
        }
    }

    drawSegments(theme) {
        this.ctx.lineWidth = 1.5;
        this.ctx.strokeStyle = theme.line_color;

        for (const seg of this.segments) {
            const s = this.worldToScreen(seg.start);
            const e = this.worldToScreen(seg.end);

            // Highlight
            let highlight = false;
            if (this.extrudeMode && (this.extrudeTargets.includes(seg) || this.extrudeHover === seg)) highlight = true;
            if (this.selectedIds.has(seg.id)) highlight = true;
            if (this.selectMode && this.hoverHit === seg) highlight = true;

            if (highlight) {
                this.ctx.save();
                this.ctx.strokeStyle = theme.hover_glow;
                this.ctx.lineWidth = 4;
                this.ctx.shadowColor = theme.hover_glow;
                this.ctx.shadowBlur = 10;
                this.ctx.beginPath();
                this.ctx.moveTo(s.x, s.y);
                this.ctx.lineTo(e.x, e.y);
                this.ctx.stroke();
                this.ctx.restore();
            }

            this.ctx.beginPath();
            this.ctx.moveTo(s.x, s.y);
            this.ctx.lineTo(e.x, e.y);
            this.ctx.stroke();
        }
    }

    drawWalls(theme) {
        // Sort walls
        const sorted = [...this.walls].sort((w1, w2) => {
            const cx = Math.cos(this.camYaw);
            const sx = Math.sin(this.camYaw);
            const ay1 = -(w1.a.x - this.camPos.x) * sx + (w1.a.y - this.camPos.y) * cx;
            const ay2 = -(w2.a.x - this.camPos.x) * sx + (w2.a.y - this.camPos.y) * cx;
            return ay1 - ay2; // Simplified depth sort
        });

        this.ctx.fillStyle = theme.line_color + '40'; // Add alpha hex if color is hex, assumes hex
        // Hack for hex alpha
        let fill = theme.line_color;
        if (fill.startsWith('#')) {
            fill = this.hexToRgba(fill, 0.2);
        }

        for (const wall of sorted) {
            const a = wall.a;
            const b = wall.b;
            const topA = new Vector3(a.x, a.y, wall.height);
            const topB = new Vector3(b.x, b.y, wall.height);

            const ps = [this.worldToScreen(a), this.worldToScreen(b), this.worldToScreen(topB), this.worldToScreen(topA)];

            this.ctx.fillStyle = fill;
            this.ctx.strokeStyle = theme.line_color;
            this.ctx.lineWidth = 1;

            this.ctx.beginPath();
            this.ctx.moveTo(ps[0].x, ps[0].y);
            for (let i = 1; i < 4; i++) this.ctx.lineTo(ps[i].x, ps[i].y);
            this.ctx.closePath();
            this.ctx.fill();
            this.ctx.stroke();
        }
    }

    drawPreview(theme) {
        if (this.extrudeMode && this.extrudeTargets.length > 0) {
            // Draw extrude preview
            let h = this.extrudeHeight;
             if (this.inputActive && this.inputValueM !== null) {
                h = this.inputValueM * PIXELS_PER_METER;
                if (this.snapEnabled) h = this.snapZ(h);
            } else if (!this.inputActive) {
                // Dynamic mouse height
                const mouseY = this.mouse.y;
                if (Math.abs(Math.sin((this.camPitchDeg - 90) * Math.PI / 180)) > 1e-6) {
                    const mid = this.extrudeTargets[0].start.add(this.extrudeTargets[0].end).div(2);
                    mid.z = 0;
                    h = this.computeHeight(mid, mouseY);
                    if (this.snapEnabled) h = this.snapZ(h);
                }
            }

            this.ctx.fillStyle = this.hexToRgba(theme.line_color, 0.2);
            this.ctx.strokeStyle = theme.line_color;

            for (const seg of this.extrudeTargets) {
                const a = seg.start;
                const b = seg.end;
                const topA = new Vector3(a.x, a.y, h);
                const topB = new Vector3(b.x, b.y, h);
                const ps = [this.worldToScreen(a), this.worldToScreen(b), this.worldToScreen(topB), this.worldToScreen(topA)];

                this.ctx.beginPath();
                this.ctx.moveTo(ps[0].x, ps[0].y);
                for (let i = 1; i < 4; i++) this.ctx.lineTo(ps[i].x, ps[i].y);
                this.ctx.closePath();
                this.ctx.fill();
                this.ctx.stroke();
            }
            return;
        }

        if (this.startPoint === null) return;

        let end = null;
        if (this.heightMode) {
             let z = 0;
             if (this.inputActive && this.inputValueM !== null) {
                 z = this.inputValueM * PIXELS_PER_METER;
             } else {
                 z = this.computeHeight(this.startPoint, this.mouse.y);
             }
             if (this.snapEnabled) z = this.snapZ(z);
             end = new Vector3(this.startPoint.x, this.startPoint.y, z);
        } else {
             if (this.inputActive && this.inputValueM !== null) {
                 let dir = this.lastPreviewDir || new Vector3(1, 0, 0);
                 const len = this.inputValueM * PIXELS_PER_METER;
                 end = this.startPoint.add(dir.mul(len));
             } else {
                 end = this.getSnappedPoint(this.mouse);
             }
             if (this.snapEnabled && !this.heightMode) end = this.snapXY(end);

             // Update dir
             const dir = end.sub(this.startPoint);
             if (dir.lengthSq() > 1e-6) this.lastPreviewDir = dir.normalize();
        }

        const s = this.worldToScreen(this.startPoint);
        const e = this.worldToScreen(end);

        this.ctx.strokeStyle = theme.line_color;
        this.ctx.beginPath();
        this.ctx.moveTo(s.x, s.y);
        this.ctx.lineTo(e.x, e.y);
        this.ctx.stroke();

        // Label
        const lenM = this.startPoint.distanceTo(end) / PIXELS_PER_METER;
        const mid = s.add(e).mul(0.5);
        this.drawLabel(`${lenM.toFixed(2)} m`, mid, theme);
    }

    drawMagnet(theme) {
        if (!this.magnetPoint || !this.snapEnabled) return;
        const s = this.worldToScreen(this.magnetPoint);
        this.ctx.strokeStyle = theme.magnet_color;
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(s.x, s.y, 6, 0, Math.PI * 2);
        this.ctx.stroke();
        if (this.magnetLocked) {
             this.ctx.beginPath();
             this.ctx.arc(s.x, s.y, 3, 0, Math.PI * 2);
             this.ctx.stroke();
        }
    }

    drawDimensions(theme) {
        this.ctx.font = '14px Inter, sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';

        for (const seg of this.segments) {
            const s = this.worldToScreen(seg.start);
            const e = this.worldToScreen(seg.end);
            const mid = s.add(e).mul(0.5);

            const dir = e.sub(s);
            const len = dir.length();
            if (len < 1) continue;

            const unit = dir.div(len);
            const perp = new Vector2(-unit.y, unit.x);

            const offset = this.dimensionOffsets[seg.id] || 0.0;
            const pos = mid.add(perp.mul(offset));

            let text = `${seg.length_m.toFixed(2)} m`;
            if (Math.abs(seg.start.x - seg.end.x) < 1e-3 && Math.abs(seg.start.y - seg.end.y) < 1e-3) {
                 text = `h=${Math.abs(seg.start.z - seg.end.z) / PIXELS_PER_METER} m`;
            }

            if (offset !== 0) {
                 const hs = s.add(perp.mul(offset)).sub(unit.mul(SIZE_OVERSHOOT_PX));
                 const he = e.add(perp.mul(offset)).add(unit.mul(SIZE_OVERSHOOT_PX));
                 this.ctx.strokeStyle = theme.line_color;
                 this.ctx.globalAlpha = 0.5;
                 this.ctx.beginPath();
                 this.ctx.moveTo(hs.x, hs.y);
                 this.ctx.lineTo(he.x, he.y);
                 this.ctx.stroke();

                 this.ctx.beginPath();
                 this.ctx.moveTo(s.x, s.y);
                 this.ctx.lineTo(s.x + perp.x * offset, s.y + perp.y * offset);
                 this.ctx.moveTo(e.x, e.y);
                 this.ctx.lineTo(e.x + perp.x * offset, e.y + perp.y * offset);
                 this.ctx.stroke();
                 this.ctx.globalAlpha = 1.0;
            }

            if (this.sizeMode && this.sizeHoverSeg === seg) {
                 this.ctx.shadowColor = theme.hover_glow;
                 this.ctx.shadowBlur = 10;
            }
            this.drawLabel(text, pos, theme);
            this.ctx.shadowBlur = 0;
        }
    }

    drawLabel(text, pos, theme) {
        this.ctx.fillStyle = theme.text_shadow;
        this.ctx.fillText(text, pos.x + 1, pos.y + 1);
        this.ctx.fillStyle = theme.text_primary;
        this.ctx.fillText(text, pos.x, pos.y);
    }

    drawLasso(theme) {
        const r = this.dragRect;
        this.ctx.fillStyle = this.hexToRgba(theme.hover_glow, 0.2);
        this.ctx.strokeStyle = theme.hover_glow;
        this.ctx.fillRect(r.x, r.y, r.w, r.h);
        this.ctx.strokeRect(r.x, r.y, r.w, r.h);
    }

    updateHUD() {
        const mouseWorld = this.screenToWorldGround(this.mouse);
        document.getElementById('hud-mode').innerText = `Mode: ${this.extrudeMode ? 'EXTRUDE' : (this.selectMode ? 'SELECT' : (this.sizeMode ? 'SIZE' : 'DRAW'))}`;
        document.getElementById('hud-stats').innerText = `Segments: ${this.segments.length} | Walls: ${this.walls.length}`;
        document.getElementById('hud-cam').innerText = `Zoom: ${this.camZoom.toFixed(2)}x | Yaw: ${(this.camYaw * 180 / Math.PI).toFixed(0)}°`;

        const inputEl = document.getElementById('hud-input');
        if (this.inputActive) {
            inputEl.style.display = 'block';
            document.getElementById('hud-input-value').innerText = this.inputText + ' m';
        } else {
            inputEl.style.display = 'none';
        }
    }

    hexToRgba(hex, alpha) {
        let r = 0, g = 0, b = 0;
        if (hex.length === 4) {
            r = parseInt(hex[1] + hex[1], 16);
            g = parseInt(hex[2] + hex[2], 16);
            b = parseInt(hex[3] + hex[3], 16);
        } else if (hex.length === 7) {
            r = parseInt(hex.substring(1, 3), 16);
            g = parseInt(hex.substring(3, 5), 16);
            b = parseInt(hex.substring(5, 7), 16);
        }
        return `rgba(${r},${g},${b},${alpha})`;
    }

    // Input Handling
    onMouseDown(e) {
        if (e.button === 0) { // Left
            if (this.selectMode) {
                this.dragging = true;
                this.dragSelect = false;
                this.mouseDownPos = new Vector2(e.clientX, e.clientY);
                this.dragRect = { x: e.clientX, y: e.clientY, w: 0, h: 0 };
            } else if (this.sizeMode) {
                if (this.sizeHoverSeg) {
                    this.sizeEditSeg = this.sizeHoverSeg;
                    this.mouseDownPos = new Vector2(e.clientX, e.clientY);
                    const oldOffset = this.dimensionOffsets[this.sizeEditSeg.id] || 0.0;
                    this.sizeDragOffsetStart = oldOffset;
                    this.undoStack.push({ type: 'dim_offset', obj: { id: this.sizeEditSeg.id, oldOffset: oldOffset } });
                    this.redoStack = [];
                }
            } else if (this.extrudeMode) {
                if (this.extrudeTargets.length === 0 && this.extrudeHover) {
                    this.extrudeTargets = [this.extrudeHover];
                    this.extrudeHeight = 0.0;
                } else if (this.extrudeTargets.length > 0) {
                     // Commit
                     if (Math.abs(this.extrudeHeight) > 1e-6) {
                         this.extrudeTargets.forEach(s => this.addWall(s, this.extrudeHeight));
                     }
                     this.extrudeTargets = [];
                }
            } else if (this.heightMode) {
                 const base = this.getSnappedPoint(this.mouse);
                 if (this.startPoint === null) {
                     this.startPoint = base;
                 } else {
                     const z = this.snapZ(this.computeHeight(this.startPoint, this.mouse.y));
                     this.addSegment(this.startPoint, new Vector3(this.startPoint.x, this.startPoint.y, z));
                     this.startPoint = null;
                 }
            } else {
                 const world = this.getSnappedPoint(this.mouse);
                 if (this.startPoint === null) {
                     this.startPoint = world;
                 } else {
                     this.addSegment(this.startPoint, world);
                     this.startPoint = null;
                 }
            }
        } else if (e.button === 2) { // Right
            if (this.startPoint) this.startPoint = null;
            if (this.extrudeTargets.length > 0) this.extrudeTargets = [];
            if (this.selectMode) this.selectedIds.clear();
            if (this.sizeEditSeg) this.sizeEditSeg = null;
        }
    }

    onMouseMove(e) {
        this.mouse = new Vector2(e.clientX, e.clientY);

        if (this.selectMode && this.dragging) {
            const w = e.clientX - this.mouseDownPos.x;
            const h = e.clientY - this.mouseDownPos.y;
            this.dragRect = {
                x: w > 0 ? this.mouseDownPos.x : e.clientX,
                y: h > 0 ? this.mouseDownPos.y : e.clientY,
                w: Math.abs(w), h: Math.abs(h)
            };
            if (Math.abs(w) > 4 || Math.abs(h) > 4) this.dragSelect = true;
        }

        if (this.sizeMode && this.sizeEditSeg && e.buttons === 1) {
             const seg = this.sizeEditSeg;
             const s = this.worldToScreen(seg.start);
             const ePt = this.worldToScreen(seg.end);
             const dir = ePt.sub(s);
             const len = dir.length();
             if (len > 0) {
                 const unitPerp = new Vector2(-dir.y/len, dir.x/len);
                 const dragDelta = this.mouse.sub(this.mouseDownPos);
                 const offsetDelta = dragDelta.dot(unitPerp);
                 let newOffset = this.sizeDragOffsetStart + offsetDelta;
                 if (this.snapEnabled) newOffset = Math.round(newOffset / SIZE_OFFSET_STEP) * SIZE_OFFSET_STEP;
                 this.dimensionOffsets[seg.id] = newOffset;
             }
             return;
        }

        // Hovers
        if (this.selectMode && !this.dragging) {
             let bestDist = SELECT_DIST_PX + 1;
             this.hoverHit = null;
             for (const seg of this.segments) {
                 const s = this.worldToScreen(seg.start);
                 const ePt = this.worldToScreen(seg.end);
                 const dist = this.pointSegmentDistance(this.mouse, s, ePt);
                 if (dist < SELECT_DIST_PX && dist < bestDist) {
                     bestDist = dist;
                     this.hoverHit = seg;
                 }
             }
        }

        if (this.sizeMode && !this.sizeEditSeg) {
             let bestDist = SELECT_DIST_PX * 2;
             this.sizeHoverSeg = null;
             for (const seg of this.segments) {
                 const s = this.worldToScreen(seg.start);
                 const ePt = this.worldToScreen(seg.end);
                 const mid = s.add(ePt).mul(0.5);
                 const dir = ePt.sub(s);
                 const len = dir.length();
                 if (len < 1) continue;
                 const perp = new Vector2(-dir.y/len, dir.x/len);
                 const offset = this.dimensionOffsets[seg.id] || 0.0;
                 const labelPos = mid.add(perp.mul(offset));
                 const dist = this.mouse.distanceTo(labelPos);
                 if (dist < bestDist) {
                     bestDist = dist;
                     this.sizeHoverSeg = seg;
                 }
             }
        }

        if (this.extrudeMode && this.extrudeTargets.length === 0) {
             let bestDist = SELECT_DIST_PX;
             this.extrudeHover = null;
             for (const seg of this.segments) {
                 if (Math.abs(seg.start.z) > 1e-6) continue;
                 const s = this.worldToScreen(seg.start);
                 const ePt = this.worldToScreen(seg.end);
                 const dist = this.pointSegmentDistance(this.mouse, s, ePt);
                 if (dist < bestDist) {
                     bestDist = dist;
                     this.extrudeHover = seg;
                 }
             }
        }
    }

    onMouseUp(e) {
        if (this.selectMode && this.dragging) {
            if (this.dragSelect) {
                // Lasso select
                const r = this.dragRect;
                const shift = e.shiftKey;
                const newSel = [];
                for (const seg of this.segments) {
                    const s = this.worldToScreen(seg.start);
                    const ePt = this.worldToScreen(seg.end);
                    // Check if either point in rect
                    if ((s.x >= r.x && s.x <= r.x + r.w && s.y >= r.y && s.y <= r.y + r.h) ||
                        (ePt.x >= r.x && ePt.x <= r.x + r.w && ePt.y >= r.y && ePt.y <= r.y + r.h)) {
                        newSel.push(seg.id);
                    }
                }

                if (!shift) this.selectedIds.clear();
                newSel.forEach(id => {
                     if (this.selectedIds.has(id)) this.selectedIds.delete(id);
                     else this.selectedIds.add(id);
                });
            } else {
                 // Click select
                 if (this.hoverHit) {
                     const id = this.hoverHit.id;
                     if (e.shiftKey) {
                         if (this.selectedIds.has(id)) this.selectedIds.delete(id);
                         else this.selectedIds.add(id);
                     } else {
                         this.selectedIds.clear();
                         this.selectedIds.add(id);
                     }
                 } else if (!e.shiftKey) {
                     this.selectedIds.clear();
                 }
            }
            this.dragging = false;
            this.dragSelect = false;
        }
        if (this.sizeMode && this.sizeEditSeg) {
            this.sizeEditSeg = null;
        }
    }

    onWheel(e) {
        e.preventDefault();
        const factor = 1.1;
        if (this.extrudeMode && this.extrudeTargets.length > 0) {
            this.extrudeHeight = this.snapZ(this.extrudeHeight + (e.deltaY < 0 ? 1 : -1) * SNAP_HEIGHT);
        } else {
            // Zoom at mouse
            const zoomIn = e.deltaY < 0;
            const newZoom = zoomIn ? this.camZoom * factor : this.camZoom / factor;

            const before = this.screenToWorldGround(this.mouse);
            this.camZoom = Math.max(0.25, Math.min(8.0, newZoom));
            const after = this.screenToWorldGround(this.mouse);

            this.camPos = this.camPos.add(new Vector2(before.x - after.x, before.y - after.y));
        }
    }

    onKeyDown(e) {
        // Camera Panning
        this.keys[e.key] = true;

        // Shortcuts
        if (e.key === 'm') this.showDimensions = !this.showDimensions;
        if (e.key === 'g') this.snapEnabled = !this.snapEnabled;
        if (e.key === 'h') {
             if (this.camPitchDeg >= 90) {
                 this.showToast("Height mode needs pitch < 90°");
             } else {
                 this.heightMode = !this.heightMode;
                 this.extrudeMode = false;
                 this.selectMode = false;
                 this.startPoint = null;
             }
        }
        if (e.key === 'z') this.undo();
        if (e.key === 'y') this.redo();
        if (e.key === 'c') this.clear();
        if (e.key === 'Delete' || e.key === 'Backspace') {
            if (this.selectMode) this.deleteSelected();
        }
        if (e.key === 'Escape') {
             if (this.inputActive) {
                 this.inputActive = false;
                 this.inputText = '';
             } else {
                 if (this.startPoint) this.startPoint = null;
                 this.selectedIds.clear();
                 this.extrudeTargets = [];
             }
        }

        // Input Handling
        if ((e.key >= '0' && e.key <= '9') || e.key === '.' || e.key === '-') {
            this.inputActive = true;
            this.inputText += e.key;
            this.parseInput();
        }
        if (e.key === 'Backspace' && this.inputActive) {
            this.inputText = this.inputText.slice(0, -1);
            if (this.inputText.length === 0) this.inputActive = false;
            this.parseInput();
        }
        if (e.key === 'Enter' && this.inputActive) {
            if (this.inputValueM !== null) {
                // Commit simulated in draw/update loop via state check, but better to trigger here
                // We'll simulate a click commit logic or variable commit
                // Actually, the click handler uses inputValueM if active.
                // We need a commit function
                this.commitInput();
            }
        }
    }

    onKeyUp(e) {
        this.keys[e.key] = false;
    }

    parseInput() {
        const val = parseFloat(this.inputText);
        if (!isNaN(val)) {
            this.inputValueM = val;
        } else {
            this.inputValueM = null;
        }
    }

    commitInput() {
        if (this.inputValueM === null) return;

        if (this.extrudeMode && this.extrudeTargets.length > 0) {
             const h = this.inputValueM * PIXELS_PER_METER; // Already handled snap in getter? No.
             this.extrudeTargets.forEach(s => this.addWall(s, h));
             this.extrudeTargets = [];
        } else if (this.heightMode && this.startPoint) {
             const z = this.inputValueM * PIXELS_PER_METER;
             this.addSegment(this.startPoint, new Vector3(this.startPoint.x, this.startPoint.y, z));
             this.startPoint = null;
        } else if (this.startPoint) {
             const dir = this.lastPreviewDir || new Vector3(1, 0, 0);
             const len = this.inputValueM * PIXELS_PER_METER;
             let end = this.startPoint.add(dir.mul(len));
             if (this.snapEnabled) end = this.snapXY(end);
             this.addSegment(this.startPoint, end);
             this.startPoint = null;
        }

        this.inputActive = false;
        this.inputText = '';
        this.inputValueM = null;
    }

    pointSegmentDistance(p, a, b) {
        const ab = b.sub(a);
        let t = 0.0;
        if (ab.lengthSq() > 0) {
            t = Math.max(0.0, Math.min(1.0, (p.x - a.x) * ab.x + (p.y - a.y) * ab.y) / ab.lengthSq());
        }
        const proj = a.add(ab.mul(t));
        return p.distanceTo(proj);
    }

    updateCamera(dt) {
        const speed = 2.0 * PIXELS_PER_METER * dt;
        const fast = this.keys['Shift'] ? 3.0 : 1.0;

        // Pan relative to yaw
        const cx = Math.cos(this.camYaw);
        const sx = Math.sin(this.camYaw);

        // Up vector in 2D top-down view rotated by yaw
        // In screen space up is -y.
        // We want to move camera pos.
        // W moves camera "forward" (up on screen)

        let dx = 0, dy = 0;

        // W/S moves along camera up vector (rotated yaw)
        if (this.keys['w']) { dy -= 1; }
        if (this.keys['s']) { dy += 1; }
        if (this.keys['a']) { dx -= 1; }
        if (this.keys['d']) { dx += 1; }

        if (dx !== 0 || dy !== 0) {
            // Rotate movement vector by yaw
            const rx = dx * cx - dy * sx;
            const ry = dx * sx + dy * cx;

            this.camPos.x += rx * speed * fast;
            this.camPos.y += ry * speed * fast;
        }

        if (this.keys['ArrowLeft']) this.camYaw += 2 * dt;
        if (this.keys['ArrowRight']) this.camYaw -= 2 * dt;

        // Zoom keys
        if (this.keys['ArrowUp']) {
            this.camZoom *= 1.02;
        }
        if (this.keys['ArrowDown']) {
            this.camZoom /= 1.02;
        }
    }

    loop() {
        this.updateCamera(0.016);
        this.draw();
        requestAnimationFrame(() => this.loop());
    }

    exportCanvas() {
        const link = document.createElement('a');
        link.download = 'floorplan.png';
        link.href = this.canvas.toDataURL();
        link.click();
    }
}

// Start App
window.onload = () => {
    new App();
};
