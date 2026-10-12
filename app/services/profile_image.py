import io
import os

import cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageOps

from app.services.leveling_math import user_progress
from app.services.achievements import ACHIEVEMENTS

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "achievements")

SCALE = 2

WIDTH = 720 * SCALE
BG_COLOR = (18, 19, 26)
CARD_COLOR = (27, 29, 38)
ACCENT_COLOR = (245, 185, 66)
TEXT_COLOR = (235, 235, 240)
MUTED_COLOR = (150, 152, 165)
BAR_BG_COLOR = (45, 47, 60)
EXP_BLUE = (41, 128, 255)
CELL_EMPTY_COLOR = (38, 41, 54)
BAR_CELLS = 20
BAR_CELL_GAP = 4 * SCALE

AVATAR_SIZE = 110 * SCALE
ICON_SIZE = 72 * SCALE
ICON_COLS = 5
ICON_GAP = 18 * SCALE
ICON_GRID_TOP = 220 * SCALE
MARGIN = 40 * SCALE
LABEL_FONT_SIZE = 11 * SCALE
LABEL_LINE_HEIGHT = 14 * SCALE
LABEL_MAX_LINES = 2
LABEL_GAP = 6 * SCALE
CELL_HEIGHT = ICON_SIZE + LABEL_GAP + LABEL_LINE_HEIGHT * LABEL_MAX_LINES


def _load_font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def _render_icon(icon_path: str, unlocked: bool, size: int = ICON_SIZE) -> Image.Image:
    png_bytes = cairosvg.svg2png(url=icon_path, output_width=size, output_height=size)
    icon = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    if not unlocked:
        icon = ImageOps.grayscale(icon.convert("RGB")).convert("RGBA")
        alpha = icon.split()[-1]
        faded = Image.new("RGBA", icon.size, (0, 0, 0, 0))
        faded.paste(icon, (0, 0))
        r, g, b, a = faded.split()
        a = a.point(lambda p: int(p * 0.45))
        faded = Image.merge("RGBA", (r, g, b, a))
        return faded
    return icon


def _wrap_label(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""

    for i, word in enumerate(words):
        candidate = f"{current} {word}".strip()
        if font.getlength(candidate) <= max_width or not current:
            current = candidate
            continue

        lines.append(current)
        current = word
        if len(lines) == LABEL_MAX_LINES:
            current = " ".join(words[i:])
            break

    if current and len(lines) < LABEL_MAX_LINES:
        lines.append(current)
    elif current:
        lines[-1] = current

    if lines and font.getlength(lines[-1]) > max_width:
        last = lines[-1]
        while last and font.getlength(last + "…") > max_width:
            last = last[:-1]
        lines[-1] = last + "…"

    return lines[:LABEL_MAX_LINES]


def _square_avatar(avatar_bytes: bytes | None, size: int) -> Image.Image:
    if avatar_bytes:
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = ImageOps.fit(avatar, (size, size))
    else:
        avatar = Image.new("RGBA", (size, size), CARD_COLOR)
        draw = ImageDraw.Draw(avatar)
        draw.ellipse([size * 0.2, size * 0.12, size * 0.8, size * 0.6], fill=MUTED_COLOR)
        draw.ellipse([size * 0.1, size * 0.55, size * 0.9, size * 1.1], fill=MUTED_COLOR)
    return avatar


def _draw_battery_exp_bar(img: Image.Image, x: int, y: int, w: int, h: int, fraction: float) -> None:
    fraction = max(0.0, min(1.0, fraction))
    filled_cells = round(BAR_CELLS * fraction)

    cell_w = (w - BAR_CELL_GAP * (BAR_CELLS - 1)) / BAR_CELLS
    draw = ImageDraw.Draw(img)

    for i in range(BAR_CELLS):
        cx = x + i * (cell_w + BAR_CELL_GAP)
        color = EXP_BLUE if i < filled_cells else CELL_EMPTY_COLOR
        draw.rectangle([cx, y, cx + cell_w, y + h], fill=color)


def render_profile_image(
    display_name: str,
    exp: int,
    message_count: int,
    unlocked_keys: set[str],
    avatar_bytes: bytes | None = None,
) -> io.BytesIO:
    progress = user_progress(exp)
    level = progress["level"]
    into_level = progress["from_level"]
    level_span = into_level + progress["to_level"]

    rows = -(-len(ACHIEVEMENTS) // ICON_COLS)
    height = ICON_GRID_TOP + rows * (CELL_HEIGHT + ICON_GAP) + ICON_GAP

    img = Image.new("RGB", (WIDTH, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    avatar = _square_avatar(avatar_bytes, AVATAR_SIZE)
    avatar_pos = (MARGIN, 36 * SCALE)
    img.paste(avatar, avatar_pos)
    outline_w = 3 * SCALE
    draw.rectangle(
        [
            avatar_pos[0] - outline_w // 2, avatar_pos[1] - outline_w // 2,
            avatar_pos[0] + AVATAR_SIZE + outline_w // 2, avatar_pos[1] + AVATAR_SIZE + outline_w // 2,
        ],
        outline=EXP_BLUE, width=outline_w,
    )

    name_font = _load_font(30 * SCALE, bold=True)
    level_font = _load_font(20 * SCALE)
    small_font = _load_font(16 * SCALE)

    text_x = avatar_pos[0] + AVATAR_SIZE + 24 * SCALE
    draw.text((text_x, 46 * SCALE), display_name, font=name_font, fill=TEXT_COLOR)
    draw.text((text_x, 86 * SCALE), f"Level {level}", font=level_font, fill=ACCENT_COLOR)
    draw.text((text_x, 114 * SCALE), f"{message_count} messages", font=small_font, fill=MUTED_COLOR)

    bar_x, bar_y, bar_w, bar_h = MARGIN, 170 * SCALE, WIDTH - 2 * MARGIN, 26 * SCALE
    fraction = (into_level / level_span) if level_span > 0 else 0
    _draw_battery_exp_bar(img, bar_x, bar_y, bar_w, bar_h, fraction)
    draw = ImageDraw.Draw(img)
    draw.text(
        (bar_x + bar_w, bar_y - 24 * SCALE), f"{into_level}/{level_span} EXP",
        font=small_font, fill=MUTED_COLOR, anchor="ra",
    )

    grid_width = ICON_COLS * ICON_SIZE + (ICON_COLS - 1) * ICON_GAP
    grid_x = (WIDTH - grid_width) // 2
    label_font = _load_font(LABEL_FONT_SIZE)

    for idx, achievement in enumerate(ACHIEVEMENTS):
        col = idx % ICON_COLS
        row = idx // ICON_COLS
        unlocked = achievement.key in unlocked_keys
        x = grid_x + col * (ICON_SIZE + ICON_GAP)
        y = ICON_GRID_TOP + row * (CELL_HEIGHT + ICON_GAP)

        icon = _render_icon(achievement.icon_path, unlocked)
        img.paste(icon, (x, y), icon)

        label_lines = _wrap_label(achievement.name, label_font, ICON_SIZE)
        label_color = TEXT_COLOR if unlocked else MUTED_COLOR
        label_y = y + ICON_SIZE + LABEL_GAP
        for line in label_lines:
            draw.text(
                (x + ICON_SIZE / 2, label_y), line,
                font=label_font, fill=label_color, anchor="ma",
            )
            label_y += LABEL_LINE_HEIGHT

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
