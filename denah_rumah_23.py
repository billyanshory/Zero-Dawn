# Floor Plan Drawer
# Quick start:
# pip install pygame pymunk
# optional: pip install reportlab python-docx
# python floorplan_drawer.py
import math
import datetime
import os
import zlib
import zipfile
from dataclasses import dataclass
from typing import List, Optional, Tuple, Set, Dict
import pygame
import pymunk
from enum import Enum
import sys

# Constants for scaling
PIXELS_PER_METER = 100
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 800
GRID_FINE_SPACING = int(0.25 * PIXELS_PER_METER)  # 25 px
GRID_MAJOR_SPACING = int(1.0 * PIXELS_PER_METER)  # 100 px
GRID_FINE_ALPHA = 40
GRID_MAJOR_ALPHA = 70
SNAP_HEIGHT = GRID_FINE_SPACING
# Magnet snapping radii (screen space pixels)
MAGNET_LOCK_RADIUS_PX = 12
MAGNET_RELEASE_RADIUS_PX = 16
MAGNET_HOVER_RADIUS_PX = 24
# Extrude selection thresholds
HOVER_DIST_PX = 10
SELECT_DIST_PX = 12
# New constants for measure input
MAX_LINE_LEN_M = 200.0
MAX_HEIGHT_M = 50.0
STEP_FINE_M = 0.05
STEP_COARSE_M = 0.5
# Size tool constants
SIZE_OFFSET_STEP = 2.0  # base step in screen px
SIZE_OVERSHOOT_PX = 12

class MeasureMode(Enum):
    LEN = 1
    HGT = 2

@dataclass
class LineSegment:
    id: int
    start: pygame.Vector3
    end: pygame.Vector3
    length_m: float
    shape: Optional[pymunk.Segment]

@dataclass
class WallFace:
    a: pygame.Vector3
    b: pygame.Vector3
    height: float

@dataclass
class Theme:
    bg: Tuple[int, int, int]
    grid_fine: Tuple[int, int, int, int]
    grid_major: Tuple[int, int, int, int]
    line_color: Tuple[int, int, int]
    text_primary: Tuple[int, int, int]
    text_muted: Tuple[int, int, int]
    text_shadow: Tuple[int, int, int]
    hover_glow: Tuple[int, int, int, int]
    button_bg: Tuple[int, int, int]
    button_bg_active: Tuple[int, int, int]
    button_bg_hover: Tuple[int, int, int]
    button_border: Tuple[int, int, int]
    tooltip_bg: Tuple[int, int, int, int]
    tooltip_text: Tuple[int, int, int]
    dialog_bg: Tuple[int, int, int, int]
    dialog_border: Tuple[int, int, int]
    dialog_shadow: Tuple[int, int, int, int]
    magnet_color: Tuple[int, int, int, int]

class ExportManager:
    A4_W, A4_H = 2480, 3508
    def __init__(self) -> None:
        self.has_pdf = False
        self.has_docx = False
        try:
            from reportlab.pdfgen import canvas  # type: ignore
            from reportlab.lib.pagesizes import A4  # type: ignore
            self.has_pdf = True
        except Exception:
            self.has_pdf = False
        try:
            from docx import Document  # type: ignore
            from docx.shared import Mm  # type: ignore
            self.has_docx = True
        except Exception:
            self.has_docx = False
    def save_png(self, surf: pygame.Surface, path: str) -> None:
        pygame.image.save(surf, path)
    def save_pdf(self, surf: pygame.Surface, path: str) -> None:
        if self.has_pdf:
            from reportlab.pdfgen import canvas  # type: ignore
            from reportlab.lib.pagesizes import A4  # type: ignore
            tmp = path + '.png'
            pygame.image.save(surf, tmp)
            c = canvas.Canvas(path, pagesize=A4)
            c.drawImage(tmp, 0, 0, width=A4[0], height=A4[1])
            c.showPage()
            c.save()
            os.remove(tmp)
        else:
            self.save_pdf_fallback(surf, path)
    def save_pdf_fallback(self, surf: pygame.Surface, path: str) -> None:
        width, height = surf.get_size()
        raw = pygame.image.tostring(surf, 'RGB')
        data = zlib.compress(raw)
        ratio = min(595 / width, 842 / height)
        dx = (595 - width * ratio) / 2
        dy = (842 - height * ratio) / 2
        objs: List[bytes] = []
        xref: List[int] = []
        def add(obj: bytes) -> None:
            xref.append(sum(len(o) for o in objs))
            objs.append(obj)
        add(b'%PDF-1.3\n')
        add(b'1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n')
        add(b'2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n')
        add(b'3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources<< /XObject<</Im0 4 0 R>> >> /Contents 5 0 R >>endobj\n')
        add(f'4 0 obj<< /Type /XObject /Subtype /Image /Width {width} /Height {height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length {len(data)} >>stream\n'.encode())
        add(data)
        add(b'\nendstream\nendobj\n')
        content = f'q {ratio} 0 0 {ratio} {dx} {dy} cm /Im0 Do Q'.encode()
        add(f'5 0 obj<< /Length {len(content)} >>stream\n'.encode())
        add(content)
        add(b'\nendstream\nendobj\n')
        xref_pos = sum(len(o) for o in objs)
        xref_table = ['xref\n0 {}\n0000000000 65535 f \n'.format(len(objs) + 1)]
        offset = 0
        for o in objs:
            xref_table.append(f'{offset:010d} 00000 n \n')
            offset += len(o)
        trailer = f'trailer<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF'
        with open(path, 'wb') as f:
            for o in objs:
                f.write(o)
            f.write(''.join(xref_table).encode())
            f.write(trailer.encode())
    def save_docx(self, surf: pygame.Surface, path: str) -> None:
        tmp = path + '.png'
        pygame.image.save(surf, tmp)
        if self.has_docx:
            from docx import Document  # type: ignore
            from docx.shared import Mm  # type: ignore
            doc = Document()
            section = doc.sections[0]
            section.page_width = Mm(210)
            section.page_height = Mm(297)
            margin = Mm(10)
            section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = margin
            doc.add_picture(tmp, width=Mm(190))
            doc.save(path)
        else:
            self.save_docx_fallback(surf, tmp, path)
        os.remove(tmp)
    def save_docx_fallback(self, surf: pygame.Surface, img_path: str, docx_path: str) -> None:
        width_mm = 210
        height_mm = 297
        margin = 10
        with open(img_path, 'rb') as f:
            img_bytes = f.read()
        rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                ' <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\n'
                '</Relationships>')
        doc_rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                    ' <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>\n'
                    '</Relationships>')
        content_types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                         '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                         '<Default Extension="xml" ContentType="application/xml"/>'
                         '<Default Extension="png" ContentType="image/png"/>'
                         '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                         '</Types>')
        width_emu = int((width_mm - 2 * margin) / 25.4 * 914400)
        height_emu = int(width_emu * surf.get_height() / surf.get_width())
        document = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
                    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                    '<w:body><w:p><w:r><w:drawing>'
                    '<wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
                    f'<wp:extent cx="{width_emu}" cy="{height_emu}"/><wp:docPr id="1" name="Picture 1"/>'
                    '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                    '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                    '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                    '<pic:nvPicPr><pic:cNvPr id="0" name="Picture 1"/><pic:cNvPicPr/></pic:nvPicPr>'
                    '<pic:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                    '<pic:spPr><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
                    '</pic:pic></a:graphicData></a:graphic></wp:inline>'
                    '</w:drawing></w:r></w:p>'
                    f'<w:sectPr><w:pgSz w="{int(width_mm/25.4*1440)}" h="{int(height_mm/25.4*1440)}"/>'
                    f'<w:pgMar top="{int(margin/25.4*1440)}" bottom="{int(margin/25.4*1440)}" '
                    f'left="{int(margin/25.4*1440)}" right="{int(margin/25.4*1440)}"/></w:sectPr>'
                    '</w:body></w:document>')
        with zipfile.ZipFile(docx_path, 'w') as z:
            z.writestr('[Content_Types].xml', content_types)
            z.writestr('_rels/.rels', rels)
            z.writestr('word/_rels/document.xml.rels', doc_rels)
            z.writestr('word/document.xml', document)
            z.writestr('word/media/image1.png', img_bytes)
class CursorMeasureInput:
    def __init__(self, app: 'FloorPlanApp') -> None:
        self.app = app
        self.active = False
        self.mode: Optional[MeasureMode] = None
        self.text = ''
        self.value_m: Optional[float] = None
        self.alpha = 0.0
        self.flash_time = 0
        self.font = self.app.get_font(18)

    def start(self, mode: MeasureMode) -> None:
        self.active = True
        self.mode = mode
        self.text = ''
        self.value_m = None
        self.alpha = 0.0

    def stop(self) -> None:
        self.active = False

    def clear(self) -> None:
        self.text = ''
        self.value_m = None

    def parse(self) -> None:
        if not self.text:
            self.value_m = None
            return
        t = self.text.strip().rstrip('m').strip()
        try:
            v = float(t)
            if self.mode == MeasureMode.LEN:
                if v < 0:
                    raise ValueError
                v = min(v, MAX_LINE_LEN_M)
            else:
                v = max(-MAX_HEIGHT_M, min(v, MAX_HEIGHT_M))
            self.value_m = v
        except ValueError:
            self.value_m = None

    def handle_key(self, event: pygame.event.Event) -> bool:
        unicode = event.unicode
        if event.key in range(pygame.K_0, pygame.K_9 + 1) or event.key in range(pygame.K_KP0, pygame.K_KP9 + 1):
            self.text += unicode
            self.parse()
            return True
        elif event.key == pygame.K_PERIOD or event.key == pygame.K_KP_PERIOD:
            if '.' not in self.text:
                self.text += '.'
            return True
        elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
            if self.mode == MeasureMode.HGT and not self.text.startswith('-'):
                self.text = '-' + self.text
            self.parse()
            return True
        elif event.key == pygame.K_m:
            self.text += 'm'
            self.parse()
            return True
        elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
            if self.text:
                self.text = self.text[:-1]
            self.parse()
            return True
        elif event.key in (pygame.K_UP, pygame.K_DOWN):
            step = STEP_COARSE_M if event.mod & pygame.KMOD_SHIFT else STEP_FINE_M
            if event.key == pygame.K_DOWN:
                step = -step
            if self.value_m is None:
                self.value_m = 0.0
            self.value_m += step
            if self.mode == MeasureMode.LEN:
                self.value_m = max(0.0, min(self.value_m, MAX_LINE_LEN_M))
            else:
                self.value_m = max(-MAX_HEIGHT_M, min(self.value_m, MAX_HEIGHT_M))
            self.text = f"{self.value_m:.2f}"
            return True
        elif event.key == pygame.K_ESCAPE:
            self.clear()
            return True
        return False

    def update(self, dt: float) -> None:
        target = 255.0 if self.active else 0.0
        self.alpha += (target - self.alpha) * min(1.0, 10.0 * dt)

    def draw(self, surface: pygame.Surface, cursor_pos: Tuple[int, int]) -> None:
        if self.alpha < 1:
            return
        theme = self.app.current_theme()
        now = pygame.time.get_ticks()
        if self.text:
            t = self.text
            color = theme.text_primary
            if self.value_m is None:
                color = (255, 100, 100)
        else:
            t = "0.00"
            color = theme.text_muted
        text_surf = self.font.render(t, True, color)
        unit_surf = self.font.render("m", True, theme.text_primary)
        hint_surf = self.font.render("Enter to apply, Esc to clear", True, theme.text_muted)
        mode_str = "LEN" if self.mode == MeasureMode.LEN else "HGT"
        mode_surf = self.font.render(mode_str, True, theme.text_primary)
        pad = 4
        w = max(text_surf.get_width(), hint_surf.get_width()) + pad * 2
        h = text_surf.get_height() + hint_surf.get_height() + pad * 3
        box_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        fill_color = theme.tooltip_bg
        border_color = theme.button_border
        if now - self.flash_time < 200:
            border_color = (255, 0, 0, int(255 * self.alpha / 255))
        pygame.draw.rect(box_surf, fill_color, box_surf.get_rect(), border_radius=4)
        pygame.draw.rect(box_surf, border_color, box_surf.get_rect(), 1, border_radius=4)
        box_surf.blit(text_surf, (pad, pad))
        box_surf.blit(hint_surf, (pad, pad + text_surf.get_height() + pad))
        mode_bg = pygame.Surface((mode_surf.get_width() + 2, mode_surf.get_height() + 2), pygame.SRCALPHA)
        pygame.draw.rect(mode_bg, (80, 80, 80, 180), mode_bg.get_rect(), border_radius=2)
        mode_bg.blit(mode_surf, (1, 1))
        box_surf.blit(mode_bg, (0, 0))
        offset_x = 20
        offset_y = -30
        pos_x = cursor_pos[0] + offset_x
        pos_y = cursor_pos[1] + offset_y
        if pos_x + w > surface.get_width():
            pos_x = cursor_pos[0] - w - offset_x
        if pos_y < 0:
            pos_y = cursor_pos[1] + 20
        if pos_y + h > surface.get_height():
            pos_y = surface.get_height() - h - 10
        surface.blit(box_surf, (pos_x, pos_y))
        unit_x = pos_x + w + 2
        unit_y = pos_y + pad + (text_surf.get_height() - unit_surf.get_height()) // 2
        surface.blit(unit_surf, (unit_x, unit_y))

    def get_value_m(self) -> Optional[float]:
        return self.value_m

    def flash_invalid(self) -> None:
        self.flash_time = pygame.time.get_ticks()

class ExitDialog:
    def __init__(self, app: 'FloorPlanApp') -> None:
        self.app = app
        self.rect: pygame.Rect = pygame.Rect(0, 0, 350, 180)  # Larger size
        self.rect.center = (app.width // 2, app.height // 2)
        self.button1_rect = pygame.Rect(0, 0, 140, 40)  # Wider buttons
        self.button2_rect = pygame.Rect(0, 0, 140, 40)
        self.focused = 0  # 0 for "keep moving forward" (cancel), 1 for "i take a rest" (confirm)
        self.font = app.get_font(18)
        self.title_font = app.get_font(20, bold=True)
        self.update_layout()

    def update_layout(self) -> None:
        self.rect.center = (self.app.width // 2, self.app.height // 2)
        self.button1_rect.midbottom = (self.rect.centerx - 80, self.rect.bottom - 20)  # Increased spacing
        self.button2_rect.midbottom = (self.rect.centerx + 80, self.rect.bottom - 20)

    def draw(self, surface: pygame.Surface) -> None:
        theme = self.app.current_theme()
        # Shadow
        shadow_surf = pygame.Surface((self.rect.w + 10, self.rect.h + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, theme.dialog_shadow, shadow_surf.get_rect(), border_radius=8)
        surface.blit(shadow_surf, (self.rect.x + 5, self.rect.y + 5))
        # Dialog bg
        dialog_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(dialog_surf, theme.dialog_bg, dialog_surf.get_rect(), border_radius=8)
        pygame.draw.rect(dialog_surf, theme.dialog_border, dialog_surf.get_rect(), 2, border_radius=8)
        # Title
        title = self.title_font.render("do you wanna to quit?", True, theme.text_primary)
        dialog_surf.blit(title, ((self.rect.w - title.get_width()) // 2, 30))  # Adjusted position for larger dialog
        # Buttons
        labels = ["keep moving forward", "i take a rest"]
        for i, (rect, label) in enumerate([(self.button1_rect, labels[0]), (self.button2_rect, labels[1])]):
            b_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            bg_color = theme.button_bg_active if i == self.focused else theme.button_bg
            pygame.draw.rect(b_surf, bg_color, b_surf.get_rect(), border_radius=4)
            pygame.draw.rect(b_surf, theme.button_border, b_surf.get_rect(), 1, border_radius=4)
            text = self.font.render(label, True, theme.text_primary)
            b_surf.blit(text, ((rect.w - text.get_width()) // 2, (rect.h - text.get_height()) // 2))
            dialog_surf.blit(b_surf, (rect.x - self.rect.x, rect.y - self.rect.y))
        surface.blit(dialog_surf, self.rect.topleft)

    def handle_event(self, event: pygame.event.Event) -> str:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.button1_rect.collidepoint(event.pos):
                    return "cancel"  # keep moving forward
                elif self.button2_rect.collidepoint(event.pos):
                    return "confirm"  # i take a rest
                elif not self.rect.collidepoint(event.pos):
                    return "cancel"  # Click outside cancels
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return "cancel" if self.focused == 0 else "confirm"
            elif event.key == pygame.K_TAB:
                self.focused = 1 - self.focused
            elif event.key == pygame.K_ESCAPE:
                return "cancel"
        return "none"
class FloorPlanApp:
    def __init__(self) -> None:
        pygame.init()
        self.fullscreen = True
        self.windowed_size = (WINDOW_WIDTH, WINDOW_HEIGHT)  # Default windowed size
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Start in fullscreen
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption("Floor Plan Drawer (pygame + pymunk)")
        self.clock = pygame.time.Clock()
        self.font_cache: Dict[Tuple[int, bool], pygame.font.Font] = {}
        # Themes
        self.theme_mode = "blueprint"
        self.themes = {
            "blueprint": Theme(
                bg=(10, 34, 64),
                grid_fine=(255, 255, 255, GRID_FINE_ALPHA),
                grid_major=(255, 255, 255, GRID_MAJOR_ALPHA),
                line_color=(255, 255, 255),
                text_primary=(255, 255, 255),
                text_muted=(150, 150, 150),
                text_shadow=(0, 0, 0),
                hover_glow=(255, 255, 255, 160),
                button_bg=(80, 80, 120),
                button_bg_active=(120, 120, 180),
                button_bg_hover=(100, 100, 160),
                button_border=(255, 255, 255),
                tooltip_bg=(20, 20, 20, 200),
                tooltip_text=(255, 255, 255),
                dialog_bg=(20, 40, 80, 220),
                dialog_border=(255, 255, 255),
                dialog_shadow=(0, 0, 0, 100),
                magnet_color=(255, 255, 255, 255)
            ),
            "white": Theme(
                bg=(245, 245, 245),
                grid_fine=(0, 0, 0, GRID_FINE_ALPHA),
                grid_major=(0, 0, 0, GRID_MAJOR_ALPHA),
                line_color=(0, 0, 0),
                text_primary=(0, 0, 0),
                text_muted=(100, 100, 100),
                text_shadow=(255, 255, 255),
                hover_glow=(0, 0, 0, 160),
                button_bg=(200, 200, 200),
                button_bg_active=(150, 150, 150),
                button_bg_hover=(180, 180, 180),
                button_border=(0, 0, 0),
                tooltip_bg=(255, 255, 255, 200),
                tooltip_text=(0, 0, 0),
                dialog_bg=(220, 220, 220, 220),
                dialog_border=(0, 0, 0),
                dialog_shadow=(0, 0, 0, 100),
                magnet_color=(0, 0, 0, 255)
            ),
            "pink": Theme(
                bg=(248, 215, 223),
                grid_fine=(170, 130, 150, GRID_FINE_ALPHA),
                grid_major=(140, 100, 120, GRID_MAJOR_ALPHA),
                line_color=(248, 250, 252),
                text_primary=(70, 45, 65),
                text_muted=(130, 100, 120),
                text_shadow=(255, 240, 245),
                hover_glow=(248, 250, 252, 160),
                button_bg=(232, 182, 192),
                button_bg_active=(206, 146, 162),
                button_bg_hover=(219, 164, 177),
                button_border=(248, 250, 252),
                tooltip_bg=(255, 235, 240, 220),
                tooltip_text=(70, 45, 65),
                dialog_bg=(255, 230, 235, 220),
                dialog_border=(248, 250, 252),
                dialog_shadow=(120, 80, 100, 100),
                magnet_color=(248, 250, 252, 255)
            )
        }
        self.theme_sequence = ["blueprint", "white", "pink"]
        # Camera state
        self.cam_pos = pygame.Vector2(self.width / 2, self.height / 2)
        self.cam_zoom = 1.0
        self.cam_yaw = 0.0
        self.cam_pitch_deg = 90.0
        # Application state
        self.segments: List[LineSegment] = []
        self.walls: List[WallFace] = []
        self.undo_stack: List[Tuple[str, object]] = []
        self.redo_stack: List[Tuple[str, object]] = []
        self.start_point: Optional[pygame.Vector3] = None
        self.height_mode = False
        self.extrude_mode = False
        self.extrude_targets: List[LineSegment] = []
        self.extrude_hover: Optional[LineSegment] = None
        self.extrude_height = 0.0
        self.hover_segment: Optional[LineSegment] = None
        self.show_dimensions = True
        self.snap_enabled = True
        self.clear_confirm_time = 0
        self.height_warning_time = 0
        self.running = True
        self.screenshot_request = False
        self.export_request = False
        self.exporter = ExportManager()
        self.toast_message = ""
        self.toast_time = 0
        self.include_hud_in_export = False
        # Magnet snapping state
        self.magnet_point: Optional[pygame.Vector3] = None
        self.magnet_locked = False
        self.magnet_alpha = 0.0
        # Selection state
        self.next_id = 1
        self.selected_ids: Set[int] = set()
        self.select_mode = False
        self.hover_hit: Optional[LineSegment] = None
        self.dragging = False
        self.drag_select = False
        self.drag_start_screen = (0, 0)
        self.drag_current = (0, 0)
        self.drag_rect = pygame.Rect(0, 0, 0, 0)
        self.cursor_phase = 0.0
        self.hover_alpha = 0.0
        # Size tool state
        self.size_mode = False
        self.size_hover_seg: Optional[LineSegment] = None
        self.size_edit_seg: Optional[LineSegment] = None
        self.size_drag_start: Tuple[int, int] = (0, 0)
        self.size_drag_offset_start = 0.0
        self.dimension_offsets: Dict[int, float] = {}  # seg.id -> signed screen px offset
        # Help panel
        self.show_help = False
        self.help_rect = pygame.Rect(0, 0, 0, 0)
        self.dt = 0.0
        # Buttons
        self.pitch_buttons: List[Tuple[str, float, pygame.Rect]] = []
        self.control_rect = pygame.Rect(0, 0, 0, 0)
        self.extrude_rect = pygame.Rect(0, 0, 0, 0)
        self.select_rect = pygame.Rect(0, 0, 0, 0)
        self.theme_rect = pygame.Rect(0, 0, 0, 0)
        self.size_rect = pygame.Rect(0, 0, 0, 0)  # New size button
        self.layout_buttons()
        # Pymunk physics space
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        # New measure input
        self.input = CursorMeasureInput(self)
        self.last_preview_dir: Optional[pygame.Vector3] = None
        # Exit dialog
        self.exit_dialog: Optional[ExitDialog] = None

    def current_theme(self) -> Theme:
        return self.themes[self.theme_mode]

    def get_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in self.font_cache:
            for family in ["Helvetica", "Arial", "Liberation Sans", "DejaVu Sans"]:
                font = pygame.font.SysFont(family, size, bold=bold)
                if font:
                    self.font_cache[key] = font
                    break
            else:
                self.font_cache[key] = pygame.font.Font(None, size)
        return self.font_cache[key]
    # --- Transforms -----------------------------------------------------------
    def world_to_screen(self, p: Tuple[float, float, float] | pygame.Vector3) -> tuple[int, int]:
        if isinstance(p, pygame.Vector3):
            x, y, z = p.x, p.y, p.z
        else:
            x, y, z = p
        vx = x - self.cam_pos.x
        vy = y - self.cam_pos.y
        vz = z
        cx = math.cos(self.cam_yaw)
        sx = math.sin(self.cam_yaw)
        rx = vx * cx + vy * sx
        ry = -vx * sx + vy * cx
        rz = vz
        pitch = math.radians(self.cam_pitch_deg - 90.0)
        c = math.cos(pitch)
        s = math.sin(pitch)
        px = rx
        py = ry * c - rz * s
        pz = ry * s + rz * c
        sx = px * self.cam_zoom + self.width * 0.5
        sy = py * self.cam_zoom + self.height * 0.5
        return int(round(sx)), int(round(sy))

    def screen_to_world_ground(self, s: Tuple[int, int]) -> pygame.Vector3:
        px = (s[0] - self.width * 0.5) / self.cam_zoom
        py = (s[1] - self.height * 0.5) / self.cam_zoom
        pitch = math.radians(self.cam_pitch_deg - 90.0)
        c = math.cos(pitch)
        cx = math.cos(self.cam_yaw)
        sx = math.sin(self.cam_yaw)
        if abs(c) < 1e-6:
            ry = 0.0
        else:
            ry = py / c
        rx = px
        vx = rx * cx - ry * sx
        vy = rx * sx + ry * cx
        x = vx + self.cam_pos.x
        y = vy + self.cam_pos.y
        return pygame.Vector3(x, y, 0.0)

    def compute_height(self, base: pygame.Vector3, screen_y: float) -> float:
        pitch = math.radians(self.cam_pitch_deg - 90.0)
        s = math.sin(pitch)
        if abs(s) < 1e-6:
            return 0.0
        c = math.cos(pitch)
        vx = base.x - self.cam_pos.x
        vy = base.y - self.cam_pos.y
        cx = math.cos(self.cam_yaw)
        sx = math.sin(self.cam_yaw)
        rx = vx * cx + vy * sx
        ry = -vx * sx + vy * cx
        py = (screen_y - self.height * 0.5) / self.cam_zoom
        z = (ry * c - py) / s
        return z

    # --- Snapping -------------------------------------------------------------
    def snap_xy(self, v: pygame.Vector3) -> pygame.Vector3:
        if not self.snap_enabled:
            return v
        x = round(v.x / GRID_FINE_SPACING) * GRID_FINE_SPACING
        y = round(v.y / GRID_FINE_SPACING) * GRID_FINE_SPACING
        return pygame.Vector3(x, y, v.z)

    def snap_z(self, z: float) -> float:
        if not self.snap_enabled:
            return z
        return round(z / SNAP_HEIGHT) * SNAP_HEIGHT

    def update_magnet(self, mouse_pos: tuple[int, int]) -> None:
        if not self.snap_enabled or self.extrude_mode:
            self.magnet_point = None
            self.magnet_locked = False
            return
        mouse_v = pygame.Vector2(mouse_pos)
        if self.magnet_locked and self.magnet_point is not None:
            sp = pygame.Vector2(self.world_to_screen(self.magnet_point))
            if mouse_v.distance_to(sp) <= MAGNET_RELEASE_RADIUS_PX:
                return
            self.magnet_locked = False
            self.magnet_point = None
        best_point: Optional[pygame.Vector3] = None
        best_dist = MAGNET_HOVER_RADIUS_PX + 1.0
        for seg in reversed(self.segments):
            for pt in (seg.start, seg.end):
                if abs(pt.z) > 1e-6:
                    continue
                sp = pygame.Vector2(self.world_to_screen(pt))
                dist = mouse_v.distance_to(sp)
                if dist <= MAGNET_HOVER_RADIUS_PX and dist < best_dist:
                    best_dist = dist
                    best_point = pt
        self.magnet_point = best_point
        self.magnet_locked = best_point is not None and best_dist <= MAGNET_LOCK_RADIUS_PX

    def get_snapped_point(self, mouse_pos: tuple[int, int]) -> pygame.Vector3:
        self.update_magnet(mouse_pos)
        ignore_magnet = self.input.active and self.input.mode == MeasureMode.LEN and self.input.text
        world = self.screen_to_world_ground(mouse_pos)
        if self.snap_enabled and self.magnet_point is not None and self.magnet_locked and not ignore_magnet:
            return self.magnet_point
        if self.snap_enabled:
            return self.snap_xy(world)
        return world

    def draw_magnet_indicator(self) -> None:
        theme = self.current_theme()
        target_alpha = 0.0
        if self.magnet_point is not None:
            target_alpha = 180.0 if self.magnet_locked else 100.0
        self.magnet_alpha += (target_alpha - self.magnet_alpha) * min(1.0, 10.0 * self.dt)
        if self.magnet_point is None or self.magnet_alpha <= 1:
            return
        pos = self.world_to_screen(self.magnet_point)
        radius = 8 if self.magnet_locked else 6
        surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        center = (radius + 2, radius + 2)
        color = theme.magnet_color[:3] + (int(self.magnet_alpha),)
        pygame.draw.circle(surf, color, center, radius, 2)
        if self.magnet_locked:
            pygame.draw.circle(surf, color, center, radius // 2, 2)
        self.screen.blit(surf, (pos[0] - radius - 2, pos[1] - radius - 2))
    # --- Segment management ---------------------------------------------------
    def add_segment(self, start: pygame.Vector3, end: pygame.Vector3) -> None:
        length_px = start.distance_to(end)
        if length_px == 0:
            return
        length_m = length_px / PIXELS_PER_METER
        shape: Optional[pymunk.Segment] = None
        if abs(start.z) < 1e-6 and abs(end.z) < 1e-6:
            shape = pymunk.Segment(self.space.static_body, (start.x, start.y), (end.x, end.y), 2)
            shape.friction = 0.5
            self.space.add(shape)
        seg = LineSegment(self.next_id, start, end, length_m, shape)
        self.next_id += 1
        self.segments.append(seg)
        self.undo_stack.append(("line", seg))
        self.redo_stack.clear()

    def add_wall(self, seg: LineSegment, height: float) -> None:
        if abs(height) < 1e-6:
            return
        wall = WallFace(pygame.Vector3(seg.start.x, seg.start.y, 0),
                         pygame.Vector3(seg.end.x, seg.end.y, 0),
                         height)
        self.walls.append(wall)
        self.undo_stack.append(("wall", wall))
        self.redo_stack.clear()

    def delete_selected(self) -> None:
        removed = [seg for seg in self.segments if seg.id in self.selected_ids]
        if not removed:
            return
        for seg in removed:
            if seg.shape is not None:
                self.space.remove(seg.shape)
            self.segments.remove(seg)
            if seg.id in self.dimension_offsets:
                del self.dimension_offsets[seg.id]
        self.undo_stack.append(("delete", removed))
        self.redo_stack.clear()
        self.selected_ids.clear()

    def undo(self) -> None:
        if not self.undo_stack:
            return
        typ, obj = self.undo_stack.pop()
        if typ == "line":
            self.segments.remove(obj)
            if obj.shape is not None:
                self.space.remove(obj.shape)
            if obj.id in self.dimension_offsets:
                del self.dimension_offsets[obj.id]
        elif typ == "wall":
            self.walls.remove(obj)
        elif typ == "delete":
            for seg in obj:
                self.segments.append(seg)
                if seg.shape is not None:
                    self.space.add(seg.shape)
        elif typ == "dim_offset":
            id, old_offset = obj
            current = self.dimension_offsets.get(id, 0.0)
            self.dimension_offsets[id] = old_offset
            self.redo_stack.append(("dim_offset", id, current))
            return
        self.redo_stack.append((typ, obj))
        self.magnet_point = None
        self.magnet_locked = False

    def redo(self) -> None:
        if not self.redo_stack:
            return
        typ, obj = self.redo_stack.pop()
        if typ == "line":
            self.segments.append(obj)
            if obj.shape is not None:
                self.space.add(obj.shape)
        elif typ == "wall":
            self.walls.append(obj)
        elif typ == "delete":
            for seg in obj:
                if seg.shape is not None:
                    self.space.remove(seg.shape)
                self.segments.remove(seg)
                if seg.id in self.dimension_offsets:
                    del self.dimension_offsets[seg.id]
        elif typ == "dim_offset":
            id, old_offset = obj
            current = self.dimension_offsets.get(id, 0.0)
            self.dimension_offsets[id] = old_offset
            self.undo_stack.append(("dim_offset", id, current))
            return
        self.undo_stack.append((typ, obj))
        self.magnet_point = None
        self.magnet_locked = False

    def clear(self) -> None:
        for seg in self.segments:
            if seg.shape is not None:
                self.space.remove(seg.shape)
        self.segments.clear()
        self.walls.clear()
        self.dimension_offsets.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.magnet_point = None
        self.magnet_locked = False
        self.extrude_targets = []
        self.extrude_height = 0.0
        self.selected_ids.clear()
    # --- Display management ---------------------------------------------------
    def toggle_fullscreen(self) -> None:
        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            self.fullscreen = False
        else:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.fullscreen = True
        self.width, self.height = self.screen.get_size()
        self.layout_buttons()
        if self.exit_dialog:
            self.exit_dialog.update_layout()

    def layout_buttons(self) -> None:
        padding = 6
        icon = 16
        hud_lines = 5
        font_height = self.get_font(18).get_height()
        y = hud_lines * (font_height + 2) + 8
        x = 5
        w = icon + padding * 2
        h = icon + padding * 2
        self.control_rect = pygame.Rect(int(x), int(y), w, h)
        x += w + 8
        self.extrude_rect = pygame.Rect(int(x), int(y), w, h)
        x += w + 8
        self.select_rect = pygame.Rect(int(x), int(y), w, h)
        x += w + 8
        self.theme_rect = pygame.Rect(int(x), int(y), w, h)
        x += w + 8
        self.size_rect = pygame.Rect(int(x), int(y), w, h)  # New size button
        labels = [("Front 0°", 0.0), ("ISO 45°", 45.0), ("Top 90°", 90.0)]
        spacing = 12
        font = self.get_font(16)
        text_surfs = [font.render(t, True, (255, 255, 255)) for t, _ in labels]
        heights = [surf.get_height() + padding * 2 for surf in text_surfs]
        h = max(heights)
        widths = [surf.get_width() + padding * 2 for surf in text_surfs]
        total_width = sum(widths) + spacing * (len(labels) - 1)
        x = (self.width - total_width) / 2
        y = self.height - h - 12
        self.pitch_buttons = []
        for (text, value), surf, w in zip(labels, text_surfs, widths):
            rect = pygame.Rect(int(x), int(y), w, h)
            self.pitch_buttons.append((text, value, rect))
            x += w + spacing

    def reset_camera(self) -> None:
        self.cam_pos = pygame.Vector2(self.width / 2, self.height / 2)
        self.cam_zoom = 1.0
        self.cam_yaw = 0.0
        self.cam_pitch_deg = 90.0

    # --- Drawing --------------------------------------------------------------
    def draw_grid(self) -> None:
        theme = self.current_theme()
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        corners = [
            self.screen_to_world_ground((0, 0)),
            self.screen_to_world_ground((self.width, 0)),
            self.screen_to_world_ground((self.width, self.height)),
            self.screen_to_world_ground((0, self.height)),
        ]
        min_x = min(p.x for p in corners)
        max_x = max(p.x for p in corners)
        min_y = min(p.y for p in corners)
        max_y = max(p.y for p in corners)
        start_x = int(math.floor(min_x / GRID_FINE_SPACING) * GRID_FINE_SPACING)
        end_x = int(math.ceil(max_x / GRID_FINE_SPACING) * GRID_FINE_SPACING)
        for x in range(start_x, end_x + GRID_FINE_SPACING, GRID_FINE_SPACING):
            color = theme.grid_major if x % GRID_MAJOR_SPACING == 0 else theme.grid_fine
            s = self.world_to_screen((x, min_y, 0))
            e = self.world_to_screen((x, max_y, 0))
            pygame.draw.line(surface, color, s, e)
        start_y = int(math.floor(min_y / GRID_FINE_SPACING) * GRID_FINE_SPACING)
        end_y = int(math.ceil(max_y / GRID_FINE_SPACING) * GRID_FINE_SPACING)
        for y in range(start_y, end_y + GRID_FINE_SPACING, GRID_FINE_SPACING):
            color = theme.grid_major if y % GRID_MAJOR_SPACING == 0 else theme.grid_fine
            s = self.world_to_screen((min_x, y, 0))
            e = self.world_to_screen((max_x, y, 0))
            pygame.draw.line(surface, color, s, e)
        self.screen.blit(surface, (0, 0))

    def draw_segments(self) -> None:
        theme = self.current_theme()
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for seg in self.segments:
            start = self.world_to_screen(seg.start)
            end = self.world_to_screen(seg.end)
            highlight = False
            if self.extrude_mode:
                if seg in self.extrude_targets or (self.extrude_hover is seg and not self.extrude_targets):
                    highlight = True
            if highlight:
                pygame.draw.line(self.screen, theme.line_color, start, end, 4)
            pygame.draw.aaline(self.screen, theme.line_color, start, end)
            if seg.id in self.selected_ids:
                pygame.draw.line(overlay, theme.hover_glow, start, end, 3)
                pygame.draw.circle(overlay, theme.hover_glow, start, 3)
                pygame.draw.circle(overlay, theme.hover_glow, end, 3)
            if self.select_mode and self.hover_hit is seg and self.hover_alpha > 1 and seg.id not in self.selected_ids:
                pygame.draw.line(overlay, theme.hover_glow, start, end, 3)
        self.screen.blit(overlay, (0, 0))
    def draw_walls(self) -> None:
        if not self.walls:
            return
        theme = self.current_theme()
        fill = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ordered = sorted(self.walls, key=lambda w: self._wall_sort_key(w))
        for wall in ordered:
            a = wall.a
            b = wall.b
            top_a = pygame.Vector3(a.x, a.y, wall.height)
            top_b = pygame.Vector3(b.x, b.y, wall.height)
            pts = [self.world_to_screen(p) for p in [a, b, top_b, top_a]]
            pygame.draw.polygon(fill, (*theme.line_color, 40), pts)
        self.screen.blit(fill, (0, 0))
        for wall in ordered:
            a = wall.a
            b = wall.b
            top_a = pygame.Vector3(a.x, a.y, wall.height)
            top_b = pygame.Vector3(b.x, b.y, wall.height)
            pts = [self.world_to_screen(p) for p in [a, b, top_b, top_a]]
            pygame.draw.aalines(self.screen, theme.line_color, True, pts)

    def _wall_sort_key(self, wall: WallFace) -> float:
        cx = math.cos(self.cam_yaw)
        sx = math.sin(self.cam_yaw)
        ay = -(wall.a.x - self.cam_pos.x) * sx + (wall.a.y - self.cam_pos.y) * cx
        by = -(wall.b.x - self.cam_pos.x) * sx + (wall.b.y - self.cam_pos.y) * cx
        return max(ay, by)

    def draw_extrude_preview(self) -> None:
        theme = self.current_theme()
        if not self.extrude_mode or not self.extrude_targets:
            return
        pitch = math.radians(self.cam_pitch_deg - 90.0)
        s = math.sin(pitch)
        if (v := self.input.get_value_m()) is not None:
            self.extrude_height = v * PIXELS_PER_METER
            if self.snap_enabled:
                self.extrude_height = self.snap_z(self.extrude_height)
        elif abs(s) >= 1e-6:
            mid_seg = self.extrude_targets[0]
            mid = pygame.Vector3((mid_seg.start.x + mid_seg.end.x) / 2,
                                 (mid_seg.start.y + mid_seg.end.y) / 2,
                                 0)
            z = self.compute_height(mid, pygame.mouse.get_pos()[1])
            self.extrude_height = self.snap_z(z) if self.snap_enabled else z
        fill = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for seg in self.extrude_targets:
            a = seg.start
            b = seg.end
            top_a = pygame.Vector3(a.x, a.y, self.extrude_height)
            top_b = pygame.Vector3(b.x, b.y, self.extrude_height)
            pts = [self.world_to_screen(p) for p in [a, b, top_b, top_a]]
            pygame.draw.polygon(fill, (*theme.line_color, 40), pts)
            pygame.draw.aalines(fill, theme.line_color, True, pts)
        self.screen.blit(fill, (0, 0))
        if self.show_dimensions:
            mid = ((pts[0][0] + pts[2][0]) // 2, (pts[0][1] + pts[2][1]) // 2)
            self.draw_label(f"h={self.extrude_height/PIXELS_PER_METER:.2f} m", (mid[0] + 10, mid[1]))
    def draw_preview(self) -> None:
        theme = self.current_theme()
        if self.extrude_mode or self.start_point is None:
            return
        mouse_pos = pygame.mouse.get_pos()
        if self.height_mode:
            if (v := self.input.get_value_m()) is not None:
                z = v * PIXELS_PER_METER
                if self.snap_enabled:
                    z = self.snap_z(z)
            else:
                z = self.compute_height(self.start_point, mouse_pos[1])
                if self.snap_enabled:
                    z = self.snap_z(z)
            end = pygame.Vector3(self.start_point.x, self.start_point.y, z)
            start_s = self.world_to_screen(self.start_point)
            end_s = self.world_to_screen(end)
            pygame.draw.aaline(self.screen, theme.line_color, start_s, end_s)
            if self.show_dimensions:
                mid = ((start_s[0] + end_s[0]) // 2, (start_s[1] + end_s[1]) // 2)
                self.draw_label(f"h={z/PIXELS_PER_METER:.2f} m", (mid[0] + 10, mid[1]))
        else:
            current = self.get_snapped_point(mouse_pos)
            dir_v = current - self.start_point
            if dir_v.length_squared() < 1e-6:
                if self.last_preview_dir is not None:
                    dir_v = self.last_preview_dir
                else:
                    dir_v = pygame.Vector3(1, 0, 0)
            else:
                dir_v = dir_v.normalize()
                self.last_preview_dir = dir_v.copy()
            if (v := self.input.get_value_m()) is not None:
                len_px = v * PIXELS_PER_METER
                end = self.start_point + dir_v * len_px
                if self.snap_enabled:
                    end = self.snap_xy(end)
                length_m = len_px / PIXELS_PER_METER
            else:
                end = current
                length_m = self.start_point.distance_to(end) / PIXELS_PER_METER
            start_s = self.world_to_screen(self.start_point)
            end_s = self.world_to_screen(end)
            pygame.draw.aaline(self.screen, theme.line_color, start_s, end_s)
            if self.show_dimensions:
                mid = ((start_s[0] + end_s[0]) // 2, (start_s[1] + end_s[1]) // 2)
                dx, dy = end_s[0] - start_s[0], end_s[1] - start_s[1]
                offset = (0, -10) if abs(dx) > abs(dy) else (10, 0)
                pos = (mid[0] + offset[0], mid[1] + offset[1])
                self.draw_label(f"{length_m:.2f} m", pos)

    def draw_dimensions(self) -> None:
        theme = self.current_theme()
        font = self.get_font(16)
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)  # For glows
        for seg in self.segments:
            start_s = pygame.Vector2(self.world_to_screen(seg.start))
            end_s = pygame.Vector2(self.world_to_screen(seg.end))
            mid = ((start_s.x + end_s.x) / 2, (start_s.y + end_s.y) / 2)
            screen_dir = end_s - start_s
            len_screen = screen_dir.length()
            if len_screen < 1e-3:
                continue
            unit_dir = screen_dir / len_screen
            # Left perpendicular: rotate 90 deg CCW
            unit_perp = pygame.Vector2(-unit_dir.y, unit_dir.x)
            offset = self.dimension_offsets.get(seg.id, 0.0)
            label_pos = (mid[0] + unit_perp.x * offset, mid[1] + unit_perp.y * offset)
            if abs(seg.start.x - seg.end.x) < 1e-3 and abs(seg.start.y - seg.end.y) < 1e-3:
                height = (seg.end.z - seg.start.z) / PIXELS_PER_METER
                text = f"h={height:.2f} m"
            else:
                text = f"{seg.length_m:.2f} m"
            if offset != 0:
                # Draw helper line
                helper_start = start_s + unit_perp * offset - unit_dir * SIZE_OVERSHOOT_PX
                helper_end = end_s + unit_perp * offset + unit_dir * SIZE_OVERSHOOT_PX
                helper_color = (*theme.line_color, 128)
                pygame.draw.aaline(self.screen, helper_color, helper_start, helper_end)
                # Extension lines
                ext_start = start_s + unit_perp * offset
                ext_end = end_s + unit_perp * offset
                ext_color = (*theme.line_color, 80)
                pygame.draw.aaline(self.screen, ext_color, start_s, ext_start)
                pygame.draw.aaline(self.screen, ext_color, end_s, ext_end)
            # Draw label
            surf = font.render(text, True, theme.text_primary)
            shadow = font.render(text, True, theme.text_shadow)
            x = label_pos[0] - surf.get_width() / 2
            y = label_pos[1] - surf.get_height() / 2
            self.screen.blit(shadow, (x + 1, y + 1))
            self.screen.blit(surf, (x, y))
            # If hovered in size mode, add glow
            if self.size_mode and self.size_hover_seg == seg:
                glow_pos = (int(label_pos[0]), int(label_pos[1]))
                pygame.draw.circle(overlay, theme.hover_glow, glow_pos, 15)
        self.screen.blit(overlay, (0, 0))
    def draw_label(self, text: str, pos: tuple[int, int]) -> None:
        theme = self.current_theme()
        font = self.get_font(16)
        surf = font.render(text, True, theme.text_primary)
        shadow = font.render(text, True, theme.text_shadow)
        x = pos[0] - surf.get_width() / 2
        y = pos[1] - surf.get_height() / 2
        self.screen.blit(shadow, (x + 1, y + 1))
        self.screen.blit(surf, (x, y))

    def draw_tooltip(self, text: str, rect: pygame.Rect) -> None:
        theme = self.current_theme()
        font = self.get_font(14)
        surf = font.render(text, True, theme.tooltip_text)
        shadow = font.render(text, True, theme.text_shadow)
        x = rect.x + (rect.w - surf.get_width()) / 2
        y = rect.bottom + 4
        if y + surf.get_height() > self.height:
            y = rect.y - surf.get_height() - 4
        self.screen.blit(shadow, (x + 1, y + 1))
        self.screen.blit(surf, (x, y))

    def draw_tool_button(self, name: str, rect: pygame.Rect, active: bool) -> None:
        theme = self.current_theme()
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        color = theme.button_bg
        if active:
            color = theme.button_bg_active
        elif hover:
            color = theme.button_bg_hover
        pygame.draw.rect(self.screen, color, rect, border_radius=4)
        pygame.draw.rect(self.screen, theme.button_border, rect, 1, border_radius=4)
        ix = rect.centerx
        iy = rect.centery
        line_color = theme.line_color
        if name == "control":
            pygame.draw.rect(self.screen, line_color, (ix - 8, iy - 6, 16, 12), 1, border_radius=2)
            pygame.draw.rect(self.screen, line_color, (ix - 6, iy - 4, 4, 4), 1, border_radius=1)
            pygame.draw.rect(self.screen, line_color, (ix + 2, iy - 4, 4, 4), 1, border_radius=1)
        elif name == "extrude":
            pygame.draw.line(self.screen, line_color, (ix - 6, iy + 4), (ix + 6, iy - 2), 1)
            pygame.draw.line(self.screen, line_color, (ix + 6, iy - 2), (ix + 6, iy + 6), 1)
            pygame.draw.line(self.screen, line_color, (ix - 6, iy + 4), (ix - 6, iy + 12), 1)
            pygame.draw.line(self.screen, line_color, (ix - 6, iy + 12), (ix + 6, iy + 6), 1)
        elif name == "select":
            pygame.draw.polygon(self.screen, line_color,
                                [(ix - 6, iy - 6), (ix + 4, iy), (ix, iy + 2),
                                 (ix + 6, iy + 12), (ix + 2, iy + 14),
                                 (ix - 4, iy + 4), (ix - 6, iy + 6)])
            pygame.draw.circle(self.screen, line_color, (ix + 4, iy), 2)
        elif name == "theme":
            colors = [self.themes[name].bg for name in self.theme_sequence[:3]]
            stripe_width = 16 // len(colors)
            x0 = ix - 8
            for i, bg_color in enumerate(colors):
                width = stripe_width if i < len(colors) - 1 else 16 - stripe_width * (len(colors) - 1)
                pygame.draw.rect(self.screen, bg_color, (x0, iy - 8, width, 16))
                x0 += width
            pygame.draw.rect(self.screen, line_color, (ix - 8, iy - 8, 16, 16), 1)
        elif name == "size":
            pygame.draw.line(self.screen, line_color, (ix - 6, iy), (ix + 6, iy))
            pygame.draw.line(self.screen, line_color, (ix - 6, iy - 2), (ix - 6, iy + 2))
            pygame.draw.line(self.screen, line_color, (ix + 6, iy - 2), (ix + 6, iy + 2))
        if hover:
            self.draw_tooltip(name, rect)

    def draw_tool_buttons(self) -> None:
        self.draw_tool_button("control", self.control_rect, self.show_help)
        self.draw_tool_button("extrude", self.extrude_rect, self.extrude_mode)
        self.draw_tool_button("select", self.select_rect, self.select_mode)
        self.draw_tool_button("theme", self.theme_rect, False)
        self.draw_tool_button("size", self.size_rect, self.size_mode)
    def draw_buttons(self) -> None:
        theme = self.current_theme()
        mouse = pygame.mouse.get_pos()
        font = self.get_font(16)
        for text, value, rect in self.pitch_buttons:
            active = abs(self.cam_pitch_deg - value) < 1e-3
            hover = rect.collidepoint(mouse)
            color = theme.button_bg
            if active:
                color = theme.button_bg_active
            elif hover:
                color = theme.button_bg_hover
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            pygame.draw.rect(self.screen, theme.button_border, rect, 1, border_radius=4)
            surf = font.render(text, True, theme.text_primary)
            self.screen.blit(surf, (rect.x + (rect.w - surf.get_width()) / 2,
                                    rect.y + (rect.h - surf.get_height()) / 2))

    def draw_lasso(self) -> None:
        theme = self.current_theme()
        if not (self.select_mode and self.drag_select):
            return
        rect = self.drag_rect
        surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (*theme.hover_glow[:3], 60), surf.get_rect(), border_radius=4)
        pygame.draw.rect(surf, (*theme.hover_glow[:3], 150), surf.get_rect(), 1, border_radius=4)
        self.screen.blit(surf, (rect.x, rect.y))

    def draw_select_cursor(self) -> None:
        theme = self.current_theme()
        if not self.select_mode:
            return
        self.cursor_phase = (self.cursor_phase + self.dt * 3.0) % (2 * math.pi)
        alpha = 150 + 50 * math.sin(self.cursor_phase * 2)
        pos = pygame.mouse.get_pos()
        surf = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*theme.line_color, int(alpha)), (7, 7), 5, 2)
        self.screen.blit(surf, (pos[0] - 7, pos[1] - 7))

    def draw_size_cursor(self) -> None:
        if not self.size_mode:
            return
        theme = self.current_theme()
        pos = pygame.mouse.get_pos()
        pygame.draw.line(self.screen, theme.line_color, (pos[0] - 5, pos[1]), (pos[0] + 5, pos[1]))
        pygame.draw.line(self.screen, theme.line_color, (pos[0] - 5, pos[1] - 2), (pos[0] - 5, pos[1] + 2))
        pygame.draw.line(self.screen, theme.line_color, (pos[0] + 5, pos[1] - 2), (pos[0] + 5, pos[1] + 2))

    def draw_help_panel(self) -> None:
        theme = self.current_theme()
        if not self.show_help:
            return
        lines = [
            "Left click: start/end segment / select / confirm",
            "Right click: cancel current action",
            "M: toggle dimensions",
            "G: snap (grid + magnet)",
            "W/A/S/D: pan",
            "Mouse wheel: zoom",
            "Up/Down: zoom",
            "Left/Right: yaw rotate",
            "Pitch buttons: set 0°/45°/90°",
            "H: Height tool",
            "Extrude button: extrude lines",
            "Select button: select lines",
            "Size button: reposition dimensions",
            "Z/Y: undo/redo",
            "C: clear all",
            "Ctrl+S: screenshot",
            "Ctrl+E: export PNG/PDF/DOCX",
            "R: reset camera",
            "F11: fullscreen",
            "ESC/Q: quit",
        ]
        font = self.get_font(16)
        padding = 8
        texts = [font.render(t, True, theme.text_primary) for t in lines]
        width = max(t.get_width() for t in texts) + padding * 2
        height = len(texts) * (font.get_height() + 4) + padding * 2
        x = self.control_rect.x
        y = self.control_rect.bottom + 20
        self.help_rect = pygame.Rect(x, y, width, height)
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(surf, theme.dialog_bg, surf.get_rect(), border_radius=6)
        pygame.draw.rect(surf, theme.dialog_border, surf.get_rect(), 1, border_radius=6)
        ty = padding
        for t in texts:
            surf.blit(t, (padding, ty))
            ty += font.get_height() + 4
        self.screen.blit(surf, (x, y))
    def draw_hud(self) -> None:
        theme = self.current_theme()
        font = self.get_font(16)
        mouse_world = self.screen_to_world_ground(pygame.mouse.get_pos())
        cursor_z = 0.0
        if self.height_mode and self.start_point is not None:
            cursor_z = self.snap_z(self.compute_height(self.start_point, pygame.mouse.get_pos()[1]))
        mode = 'EXTRUDE' if self.extrude_mode else ('HEIGHT' if self.height_mode else ('SELECT' if self.select_mode else ('SIZE' if self.size_mode else 'XY')))
        extrude_info = '' if not (self.extrude_mode and self.extrude_targets) else f" | Extrude h={self.extrude_height/PIXELS_PER_METER:.2f} m"
        lines = [
            f"Mode: {mode} | Cursor: ({mouse_world.x/PIXELS_PER_METER:.2f}, {mouse_world.y/PIXELS_PER_METER:.2f}, {cursor_z/PIXELS_PER_METER:.2f}) m{extrude_info}",
            f"Segments: {len(self.segments)} | Walls: {len(self.walls)} | SNAP {'ON' if self.snap_enabled else 'OFF'} | MAGNET {'NONE' if self.magnet_point is None else f'{self.magnet_point.x/PIXELS_PER_METER:.2f},{self.magnet_point.y/PIXELS_PER_METER:.2f}'} | DIMS {'ON' if self.show_dimensions else 'OFF'} | FULLSCREEN {'ON' if self.fullscreen else 'OFF'}",
            f"Window: {self.width}x{self.height} | Zoom: {self.cam_zoom:.2f}x | Yaw: {math.degrees(self.cam_yaw):.1f}° | Pitch:{self.cam_pitch_deg:.1f}° | Cam: ({int(self.cam_pos.x)}, {int(self.cam_pos.y)}) | 1 m = 100 px",
        ]
        exp = "PNG"
        exp += " PDF" if self.exporter.has_pdf else " PDF*"
        exp += " DOCX" if self.exporter.has_docx else " DOCX*"
        lines.append(f"Exporters: {exp}")
        if self.input.active:
            typ = "length" if self.input.mode == MeasureMode.LEN else "height (+/-)"
            curr = f" | Current: {self.input.value_m:.2f} m" if self.input.value_m is not None else ""
            lines.append(f"Type {typ} (m) and press Enter{curr}")
        y = 5
        for line in lines:
            surf = font.render(line, True, theme.text_primary)
            shadow = font.render(line, True, theme.text_shadow)
            self.screen.blit(shadow, (6, y + 1))
            self.screen.blit(surf, (5, y))
            y += surf.get_height() + 2
    def update_select_hover(self) -> None:
        if not self.select_mode or self.dragging:
            self.hover_hit = None
            return
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        best = None
        best_dist = HOVER_DIST_PX + 1
        for seg in reversed(self.segments):
            s = pygame.Vector2(self.world_to_screen(seg.start))
            e = pygame.Vector2(self.world_to_screen(seg.end))
            dist = self.point_segment_distance(mouse, s, e)
            if dist <= HOVER_DIST_PX and dist < best_dist:
                best_dist = dist
                best = seg
        self.hover_hit = best
        target = 180 if self.hover_hit else 0
        self.hover_alpha += (target - self.hover_alpha) * min(1.0, 10 * self.dt)

    def lasso_select(self, rect: pygame.Rect) -> List[LineSegment]:
        result = []
        for seg in self.segments:
            s = self.world_to_screen(seg.start)
            e = self.world_to_screen(seg.end)
            if rect.collidepoint(s) or rect.collidepoint(e):
                result.append(seg)
                continue
            if rect.clipline(s, e):
                result.append(seg)
                continue
            mid = ((s[0] + e[0]) // 2, (s[1] + e[1]) // 2)
            if rect.collidepoint(mid):
                result.append(seg)
        return result

    def update_extrude_hover(self) -> None:
        if not self.extrude_mode or self.extrude_targets:
            self.extrude_hover = None
            return
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        best = None
        best_dist = HOVER_DIST_PX + 1
        for seg in reversed(self.segments):
            if abs(seg.start.z) > 1e-6 or abs(seg.end.z) > 1e-6:
                continue
            s = pygame.Vector2(self.world_to_screen(seg.start))
            e = pygame.Vector2(self.world_to_screen(seg.end))
            dist = self.point_segment_distance(mouse, s, e)
            if dist <= HOVER_DIST_PX and dist < best_dist:
                best = seg
                best_dist = dist
        self.extrude_hover = best

    def update_size_hover(self) -> None:
        if not self.size_mode or self.size_edit_seg:
            self.size_hover_seg = None
            return
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        best = None
        best_dist = float('inf')
        for seg in self.segments:
            start_s = pygame.Vector2(self.world_to_screen(seg.start))
            end_s = pygame.Vector2(self.world_to_screen(seg.end))
            mid = ((start_s.x + end_s.x) / 2, (start_s.y + end_s.y) / 2)
            screen_dir = end_s - start_s
            len_screen = screen_dir.length()
            if len_screen < 1e-3:
                continue
            unit_perp = pygame.Vector2(-screen_dir.y / len_screen, screen_dir.x / len_screen)
            offset = self.dimension_offsets.get(seg.id, 0.0)
            label_pos_v = pygame.Vector2(mid) + unit_perp * offset
            dist = mouse.distance_to(label_pos_v)
            if dist < HOVER_DIST_PX * 2 and dist < best_dist:  # Rough hit test
                best_dist = dist
                best = seg
        self.size_hover_seg = best

    @staticmethod
    def point_segment_distance(p: pygame.Vector2, a: pygame.Vector2, b: pygame.Vector2) -> float:
        ab = b - a
        t = 0.0
        if ab.length_squared() > 0:
            t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared()))
        proj = a + ab * t
        return (p - proj).length()
    def draw(self) -> None:
        theme = self.current_theme()
        self.update_magnet(pygame.mouse.get_pos())
        self.update_extrude_hover()
        self.update_select_hover()
        self.update_size_hover()
        self.screen.fill(theme.bg)
        self.draw_grid()
        self.draw_walls()
        self.draw_segments()
        self.draw_extrude_preview()
        self.draw_preview()
        self.draw_magnet_indicator()
        if self.show_dimensions:
            self.draw_dimensions()
        self.draw_lasso()
        self.draw_tool_buttons()
        self.draw_buttons()
        self.draw_select_cursor()
        self.draw_size_cursor()
        self.draw_hud()
        self.draw_help_panel()
        self.input.draw(self.screen, pygame.mouse.get_pos())
        now = pygame.time.get_ticks()
        if self.clear_confirm_time and now - self.clear_confirm_time < 2000:
            self.draw_label("Press C again to clear", (self.width // 2, 30))
        if self.height_warning_time and now - self.height_warning_time < 2000:
            self.draw_label("Height mode needs pitch < 90°", (self.width // 2, 50))
        if self.toast_message and now - self.toast_time < 2000:
            self.draw_label(self.toast_message, (self.width // 2, 70))
        if self.exit_dialog:
            self.exit_dialog.draw(self.screen)
        pygame.display.flip()
    # --- Input ----------------------------------------------------------------
    def handle_mouse_button_down(self, event: pygame.event.Event) -> None:
        if self.exit_dialog:
            result = self.exit_dialog.handle_event(event)
            if result == "confirm":
                self.running = False
            elif result == "cancel":
                self.exit_dialog = None
            return
        if self.show_help:
            if event.button in (1, 3):
                if not self.help_rect.collidepoint(event.pos):
                    self.show_help = False
                return
        if event.button == 1:
            if self.control_rect.collidepoint(event.pos):
                self.show_help = not self.show_help
                return
            if self.extrude_rect.collidepoint(event.pos):
                self.extrude_mode = not self.extrude_mode
                if self.extrude_mode:
                    self.height_mode = False
                    self.start_point = None
                    self.select_mode = False
                    self.size_mode = False
                    if self.selected_ids:
                        self.extrude_targets = [seg for seg in self.segments if seg.id in self.selected_ids and abs(seg.start.z) < 1e-6 and abs(seg.end.z) < 1e-6]
                        self.extrude_height = 0.0
                    else:
                        self.extrude_targets = []
                else:
                    self.extrude_targets = []
                    self.extrude_hover = None
                return
            if self.select_rect.collidepoint(event.pos):
                self.select_mode = not self.select_mode
                if self.select_mode:
                    self.extrude_mode = False
                    self.height_mode = False
                    self.size_mode = False
                    self.start_point = None
                else:
                    self.hover_hit = None
                    self.dragging = False
                    self.drag_select = False
                return
            if self.theme_rect.collidepoint(event.pos):
                current_index = self.theme_sequence.index(self.theme_mode)
                next_index = (current_index + 1) % len(self.theme_sequence)
                self.theme_mode = self.theme_sequence[next_index]
                self.toast_message = f"Theme: {self.theme_mode.replace('_', ' ').title()}"
                self.toast_time = pygame.time.get_ticks()
                return
            if self.size_rect.collidepoint(event.pos):
                self.size_mode = not self.size_mode
                if self.size_mode:
                    self.extrude_mode = False
                    self.height_mode = False
                    self.select_mode = False
                    self.start_point = None
                else:
                    self.size_hover_seg = None
                    self.size_edit_seg = None
                return
            for text, value, rect in self.pitch_buttons:
                if rect.collidepoint(event.pos):
                    self.cam_pitch_deg = value
                    if self.height_mode and self.cam_pitch_deg >= 90:
                        self.height_mode = False
                        self.start_point = None
                    return
            if self.select_mode:
                self.dragging = True
                self.drag_select = False
                self.drag_start_screen = event.pos
                self.drag_current = event.pos
                return
            if self.size_mode:
                if self.size_hover_seg is not None:
                    self.size_edit_seg = self.size_hover_seg
                    self.size_drag_start = event.pos
                    self.size_drag_offset_start = self.dimension_offsets.get(self.size_edit_seg.id, 0.0)
                    self.undo_stack.append(("dim_offset", self.size_edit_seg.id, self.size_drag_offset_start))
                    self.redo_stack.clear()
                return
            if self.extrude_mode:
                if not self.extrude_targets:
                    if self.extrude_hover is not None:
                        self.extrude_targets = [self.extrude_hover]
                        self.extrude_height = 0.0
                else:
                    if abs(self.extrude_height) > 1e-6:
                        for seg in self.extrude_targets:
                            self.add_wall(seg, self.extrude_height)
                    self.extrude_targets = []
                return
            if self.height_mode:
                base = self.get_snapped_point(event.pos)
                if self.start_point is None:
                    self.start_point = base
                else:
                    z = self.snap_z(self.compute_height(self.start_point, event.pos[1]))
                    end = pygame.Vector3(self.start_point.x, self.start_point.y, z)
                    if self.start_point.distance_to(end) > 0:
                        self.add_segment(self.start_point, end)
                    self.start_point = None
            else:
                world = self.get_snapped_point(event.pos)
                if self.start_point is None:
                    self.start_point = world
                else:
                    if self.start_point.distance_to(world) > 0:
                        self.add_segment(self.start_point, world)
                    self.start_point = None
        elif event.button == 3:
            if self.select_mode:
                if self.dragging:
                    self.dragging = False
                    self.drag_select = False
                else:
                    self.selected_ids.clear()
                return
            if self.size_mode and self.size_edit_seg:
                self.dimension_offsets[self.size_edit_seg.id] = self.size_drag_offset_start
                self.size_edit_seg = None
                if self.undo_stack and self.undo_stack[-1][0] == "dim_offset":
                    self.undo_stack.pop()
                return
            if self.extrude_mode and self.extrude_targets:
                self.extrude_targets = []
                self.extrude_height = 0.0
            else:
                self.start_point = None
    def handle_mouse_motion(self, event: pygame.event.Event) -> None:
        if self.exit_dialog:
            self.exit_dialog.handle_event(event)
            return
        if self.select_mode and self.dragging:
            self.drag_current = event.pos
            if not self.drag_select:
                if pygame.Vector2(event.pos).distance_to(self.drag_start_screen) > 4:
                    self.drag_select = True
            if self.drag_select:
                x1, y1 = self.drag_start_screen
                x2, y2 = self.drag_current
                self.drag_rect = pygame.Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            return
        if self.size_mode and self.size_edit_seg and pygame.mouse.get_pressed()[0]:
            mouse = pygame.Vector2(event.pos)
            seg = self.size_edit_seg
            start_s = pygame.Vector2(self.world_to_screen(seg.start))
            end_s = pygame.Vector2(self.world_to_screen(seg.end))
            screen_dir = end_s - start_s
            len_screen = screen_dir.length()
            if len_screen < 1e-3:
                return
            unit_perp = pygame.Vector2(-screen_dir.y / len_screen, screen_dir.x / len_screen)
            drag_delta = mouse - pygame.Vector2(self.size_drag_start)
            offset_delta = drag_delta.dot(unit_perp)
            new_offset = self.size_drag_offset_start + offset_delta
            mod = pygame.key.get_mods()
            step = SIZE_OFFSET_STEP
            if mod & pygame.KMOD_SHIFT:
                step *= 5  # Bigger step
            if mod & pygame.KMOD_CTRL:
                step /= 2  # Finer step
            if self.snap_enabled:
                new_offset = round(new_offset / step) * step
            self.dimension_offsets[seg.id] = new_offset

    def handle_mouse_button_up(self, event: pygame.event.Event) -> None:
        if self.exit_dialog:
            result = self.exit_dialog.handle_event(event)
            if result == "confirm":
                self.running = False
            elif result == "cancel":
                self.exit_dialog = None
            return
        if event.button == 1 and self.select_mode and self.dragging:
            if self.drag_select:
                segs = self.lasso_select(self.drag_rect)
                ids = [s.id for s in segs]
                shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
                if shift:
                    for i in ids:
                        if i in self.selected_ids:
                            self.selected_ids.remove(i)
                        else:
                            self.selected_ids.add(i)
                else:
                    self.selected_ids = set(ids)
            else:
                shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
                if self.hover_hit is not None and self.point_segment_distance(pygame.Vector2(event.pos), pygame.Vector2(self.world_to_screen(self.hover_hit.start)), pygame.Vector2(self.world_to_screen(self.hover_hit.end))) <= SELECT_DIST_PX:
                    if shift:
                        if self.hover_hit.id in self.selected_ids:
                            self.selected_ids.remove(self.hover_hit.id)
                        else:
                            self.selected_ids.add(self.hover_hit.id)
                    else:
                        self.selected_ids = {self.hover_hit.id}
                elif not shift:
                    self.selected_ids.clear()
            self.dragging = False
            self.drag_select = False
        if event.button == 1 and self.size_mode and self.size_edit_seg:
            self.size_edit_seg = None
    def commit_preview(self) -> None:
        value = self.input.get_value_m()
        if value is None:
            self.input.flash_invalid()
            return
        if self.extrude_mode and self.extrude_targets:
            h_px = value * PIXELS_PER_METER
            if self.snap_enabled:
                h_px = self.snap_z(h_px)
            if abs(h_px) > 1e-6:
                for seg in self.extrude_targets:
                    self.add_wall(seg, h_px)
            self.extrude_targets = []
            self.input.stop()
        elif self.height_mode and self.start_point is not None:
            z_px = value * PIXELS_PER_METER
            if self.snap_enabled:
                z_px = self.snap_z(z_px)
            end = pygame.Vector3(self.start_point.x, self.start_point.y, z_px)
            if abs(z_px) > 1e-6:
                self.add_segment(self.start_point, end)
            self.start_point = None
            self.input.stop()
        elif not self.height_mode and not self.extrude_mode and self.start_point is not None:
            mouse_pos = pygame.mouse.get_pos()
            current = self.screen_to_world_ground(mouse_pos)
            dir_v = current - self.start_point
            if dir_v.length_squared() < 1e-6:
                if self.last_preview_dir is not None:
                    dir_v = self.last_preview_dir
                else:
                    dir_v = pygame.Vector3(1, 0, 0)
            else:
                dir_v.normalize_ip()
            len_px = value * PIXELS_PER_METER
            end = self.start_point + dir_v * len_px
            if self.snap_enabled:
                end = self.snap_xy(end)
            if len_px > 0:
                self.add_segment(self.start_point, end)
            self.start_point = None
            self.input.stop()

    def handle_key_down(self, event: pygame.event.Event) -> None:
        if self.exit_dialog:
            result = self.exit_dialog.handle_event(event)
            if result == "confirm":
                self.running = False
            elif result == "cancel":
                self.exit_dialog = None
            return
        if event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
            self.screenshot_request = True
            return
        if event.key == pygame.K_e and (event.mod & pygame.KMOD_CTRL):
            self.export_request = True
            return
        if self.input.active:
            if event.key == pygame.K_RETURN:
                self.commit_preview()
                return
            consumed = self.input.handle_key(event)
            if consumed:
                return
            if event.key in [pygame.K_m, pygame.K_g, pygame.K_z, pygame.K_y, pygame.K_c, pygame.K_s, pygame.K_r, pygame.K_h]:
                return
        elif event.key == pygame.K_m:
            self.show_dimensions = not self.show_dimensions
        elif event.key == pygame.K_g:
            self.snap_enabled = not self.snap_enabled
        elif event.key == pygame.K_z:
            self.undo()
        elif event.key == pygame.K_y:
            self.redo()
        elif event.key == pygame.K_c:
            now = pygame.time.get_ticks()
            if self.clear_confirm_time and now - self.clear_confirm_time < 2000:
                self.clear()
                self.clear_confirm_time = 0
            else:
                self.clear_confirm_time = now
        elif event.key == pygame.K_F11:
            self.toggle_fullscreen()
        elif event.key == pygame.K_r:
            self.reset_camera()
        elif event.key == pygame.K_h:
            if self.cam_pitch_deg >= 90.0:
                self.height_warning_time = pygame.time.get_ticks()
                self.height_mode = False
                self.start_point = None
            else:
                self.height_mode = not self.height_mode
                self.extrude_mode = False
                self.select_mode = False
                self.size_mode = False
                self.start_point = None
        elif event.key == pygame.K_RETURN and self.extrude_mode and self.extrude_targets:
            if abs(self.extrude_height) > 1e-6:
                for seg in self.extrude_targets:
                    self.add_wall(seg, self.extrude_height)
            self.extrude_targets = []
        elif event.key == pygame.K_BACKSPACE and self.select_mode:
            self.delete_selected()
        elif event.key == pygame.K_DELETE and self.size_mode and self.size_edit_seg:
            id = self.size_edit_seg.id
            old_offset = self.dimension_offsets.get(id, 0.0)
            if old_offset != 0.0:
                self.dimension_offsets[id] = 0.0
                if self.undo_stack and self.undo_stack[-1][0] == "dim_offset" and self.undo_stack[-1][1] == id:
                    self.undo_stack.pop()
                self.undo_stack.append(("dim_offset", id, old_offset))
                self.redo_stack.clear()
            self.size_edit_seg = None
        elif event.key in (pygame.K_ESCAPE, pygame.K_q):
            if self.show_help:
                self.show_help = False
            elif self.size_mode:
                if self.size_edit_seg:
                    self.dimension_offsets[self.size_edit_seg.id] = self.size_drag_offset_start
                    self.size_edit_seg = None
                    if self.undo_stack and self.undo_stack[-1][0] == "dim_offset":
                        self.undo_stack.pop()
                else:
                    self.size_mode = False
            elif self.select_mode:
                if self.dragging:
                    self.dragging = False
                    self.drag_select = False
                else:
                    self.selected_ids.clear()
                    self.select_mode = False
            elif self.extrude_mode:
                if self.extrude_targets:
                    self.extrude_targets = []
                    self.extrude_height = 0.0
                else:
                    self.extrude_mode = False
            elif self.start_point is not None:
                self.start_point = None
            else:
                self.exit_dialog = ExitDialog(self)
    def zoom_at_mouse(self, new_zoom: float, mouse_pos: tuple[int, int]) -> None:
        new_zoom = max(0.25, min(8.0, new_zoom))
        if new_zoom == self.cam_zoom:
            return
        before = self.screen_to_world_ground(mouse_pos)
        self.cam_zoom = new_zoom
        after = self.screen_to_world_ground(mouse_pos)
        self.cam_pos += pygame.Vector2(before.x - after.x, before.y - after.y)

    def handle_zoom(self, direction: int, mouse_pos: tuple[int, int]) -> None:
        factor = 1.1
        if direction > 0:
            self.zoom_at_mouse(self.cam_zoom * factor, mouse_pos)
        else:
            self.zoom_at_mouse(self.cam_zoom / factor, mouse_pos)

    def handle_camera_movement(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        speed = 2.0 * PIXELS_PER_METER
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            speed *= 3
        up = pygame.Vector2(0, -1).rotate_rad(self.cam_yaw)
        right = pygame.Vector2(1, 0).rotate_rad(self.cam_yaw)
        if keys[pygame.K_w]:
            self.cam_pos += up * speed * dt
        if keys[pygame.K_s]:
            self.cam_pos -= up * speed * dt
        if keys[pygame.K_d]:
            self.cam_pos += right * speed * dt
        if keys[pygame.K_a]:
            self.cam_pos -= right * speed * dt
        rot_speed = math.radians(60)
        if keys[pygame.K_LEFT]:
            self.cam_yaw += rot_speed * dt
        if keys[pygame.K_RIGHT]:
            self.cam_yaw -= rot_speed * dt
        self.cam_yaw = (self.cam_yaw + math.tau) % math.tau
        zoom_speed = 5
        if keys[pygame.K_UP]:
            factor = 1.1 ** (zoom_speed * dt)
            self.zoom_at_mouse(self.cam_zoom * factor, pygame.mouse.get_pos())
        if keys[pygame.K_DOWN]:
            factor = 1.1 ** (zoom_speed * dt)
            self.zoom_at_mouse(self.cam_zoom / factor, pygame.mouse.get_pos())
    # --- Misc -----------------------------------------------------------------
    def render_clean_surface(self, include_hud: bool) -> pygame.Surface:
        surf = pygame.Surface((self.width, self.height))
        old_screen = self.screen
        old_size_mode = self.size_mode
        old_size_hover = self.size_hover_seg
        self.screen = surf
        self.size_mode = False  # Disable overlays for clean render
        self.size_hover_seg = None
        self.screen.fill(self.current_theme().bg)
        self.draw_grid()
        self.draw_walls()
        self.draw_segments()
        if self.show_dimensions:
            self.draw_dimensions()
        if include_hud:
            self.draw_hud()
        self.size_mode = old_size_mode
        self.size_hover_seg = old_size_hover
        self.screen = old_screen
        return surf

    def save_screenshot(self) -> None:
        filename = datetime.datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        surf = self.render_clean_surface(False)
        pygame.image.save(surf, filename)

    def render_export_surface(self, include_hud: bool) -> pygame.Surface:
        w, h = ExportManager.A4_W, ExportManager.A4_H
        scale = min(w / self.width, h / self.height)
        surf = pygame.Surface((w, h))
        old_screen = self.screen
        old_w, old_h = self.width, self.height
        old_zoom = self.cam_zoom
        old_select = self.select_mode
        old_selected = self.selected_ids
        old_extrude = self.extrude_mode
        old_targets = self.extrude_targets
        old_hover = self.hover_hit
        old_size_mode = self.size_mode
        old_size_hover = self.size_hover_seg
        self.screen = surf
        self.width, self.height = w, h
        self.cam_zoom *= scale
        self.font_cache.clear()
        self.select_mode = False
        self.selected_ids = set()
        self.extrude_mode = False
        self.extrude_targets = []
        self.hover_hit = None
        self.size_mode = False
        self.size_hover_seg = None
        self.screen.fill(self.current_theme().bg)
        self.draw_grid()
        self.draw_walls()
        self.draw_segments()
        if self.show_dimensions:
            self.draw_dimensions()
        if include_hud:
            self.draw_hud()
        self.cam_zoom = old_zoom
        self.width, self.height = old_w, old_h
        self.screen = old_screen
        self.select_mode = old_select
        self.selected_ids = old_selected
        self.extrude_mode = old_extrude
        self.extrude_targets = old_targets
        self.hover_hit = old_hover
        self.size_mode = old_size_mode
        self.size_hover_seg = old_size_hover
        self.font_cache.clear()
        return surf

    def export_plan(self) -> None:
        surf = self.render_export_surface(self.include_hud_in_export)
        os.makedirs('exports', exist_ok=True)
        base = datetime.datetime.now().strftime('floorplan_%Y%m%d_%H%M%S')
        png_path = os.path.join('exports', base + '.png')
        pdf_path = os.path.join('exports', base + '.pdf')
        docx_path = os.path.join('exports', base + '.docx')
        self.exporter.save_png(surf, png_path)
        self.exporter.save_pdf(surf, pdf_path)
        self.exporter.save_docx(surf, docx_path)
        self.toast_message = f"Saved: {base}"
        self.toast_time = pygame.time.get_ticks()
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.dt = dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if not self.exit_dialog:
                        self.exit_dialog = ExitDialog(self)
                    continue
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.width, self.height = event.w, event.h
                    self.windowed_size = (self.width, self.height)
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.layout_buttons()
                    if self.exit_dialog:
                        self.exit_dialog.update_layout()
                elif event.type == pygame.MOUSEWHEEL:
                    if self.exit_dialog:
                        continue
                    if self.extrude_mode and self.extrude_targets:
                        self.extrude_height = self.snap_z(self.extrude_height + event.y * SNAP_HEIGHT)
                    else:
                        self.handle_zoom(event.y, pygame.mouse.get_pos())
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in (4, 5):
                        if self.exit_dialog:
                            continue
                        if self.extrude_mode and self.extrude_targets:
                            self.extrude_height = self.snap_z(self.extrude_height + (1 if event.button == 4 else -1) * SNAP_HEIGHT)
                        else:
                            self.handle_zoom(1 if event.button == 4 else -1, event.pos)
                    else:
                        self.handle_mouse_button_down(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handle_mouse_button_up(event)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key_down(event)
            if self.exit_dialog:
                self.draw()
                continue
            self.handle_camera_movement(dt)
            self.space.step(dt)
            if self.start_point is not None and not self.height_mode and not self.extrude_mode and not self.select_mode and not self.size_mode and not self.input.active:
                self.input.start(MeasureMode.LEN)
            elif self.start_point is not None and self.height_mode and not self.input.active:
                self.input.start(MeasureMode.HGT)
            elif self.extrude_mode and self.extrude_targets and not self.input.active:
                self.input.start(MeasureMode.HGT)
            elif self.input.active and (self.start_point is None or self.extrude_mode and not self.extrude_targets):
                self.input.stop()
            self.input.update(dt)
            self.draw()
            if self.screenshot_request:
                self.save_screenshot()
                self.screenshot_request = False
            if self.export_request:
                self.export_plan()
                self.export_request = False
        pygame.quit()
        sys.exit(0)


def main() -> None:
    app = FloorPlanApp()
    app.run()


if __name__ == "__main__":
    main()
