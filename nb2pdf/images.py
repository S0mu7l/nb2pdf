"""Tall-image handling: detect stitched panels and slice for PDF layout.
长图处理：按常见分辨率识别无缝拼接段，切片后完整显示。"""
from __future__ import annotations

import base64
import io
import os
import re

# Skip slicing below this height / 高度低于此值不切片
SPLIT_IMAGE_MIN_HEIGHT = 3000
# Fallback strip height when stitch pattern is unknown / 无法识别拼接规律时的回退切片高度
FALLBACK_STRIP_HEIGHT = 2200
# Common single-frame heights (1080p / 2K / 4K), priority order / 常见单帧高度，按优先级排列
COMMON_PANEL_HEIGHTS = (1440, 2160, 1080, 1920, 1280, 720)
# Allowed panel count range / 允许的拼接张数范围
MIN_PANEL_COUNT = 2
MAX_PANEL_COUNT = 30

_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_SRC_RE = re.compile(r"""src=["']([^"']+)["']""", re.IGNORECASE)

# Seamless stack: zero gap between strips / 无缝拼接栈：条间零间距
_STACK_STYLE = "display:block;overflow:visible;line-height:0;font-size:0;margin:0 auto 8px;"
_STRIP_STYLE = (
    "display:block;width:100%;max-width:100%;height:auto;margin:0;padding:0;"
    "border:0;vertical-align:top;"
    "page-break-inside:avoid;break-inside:avoid-page;"
)
_SINGLE_STYLE = (
    "display:block;width:100%;max-width:100%;height:auto;"
    "page-break-inside:avoid;break-inside:avoid-page;margin:0 auto 8px;"
)


def detect_panel_height(width: int, height: int) -> int | None:
    """
    Detect how many equal-height panels form a tall stitched image.
    检测长图由多少张等高分辨率图片拼接而成。

    Prefer 16:9 frame height (e.g. 2560×1440), then common heights that divide total height.
    优先匹配与宽度成 16:9 的单帧高度，再尝试 1080 / 1440 / 2160 等常见高度能否整除总高度。

    Example: 2560×10080 → 10080/1440=7 → returns 1440 (7× 2K panels).
    例：2560×10080 → 10080/1440=7 → 返回 1440（7 张 2K 图无缝拼接）
    """
    if height < SPLIT_IMAGE_MIN_HEIGHT:
        return None

    ideal_16_9 = width * 9 // 16
    candidates: list[tuple[int, int]] = []

    check_heights: list[int] = []
    if ideal_16_9 > 0:
        check_heights.append(ideal_16_9)
    for h in COMMON_PANEL_HEIGHTS:
        if h not in check_heights:
            check_heights.append(h)

    for panel_h in check_heights:
        if panel_h <= 0 or height % panel_h != 0:
            continue
        count = height // panel_h
        if MIN_PANEL_COUNT <= count <= MAX_PANEL_COUNT:
            candidates.append((panel_h, count))

    if not candidates:
        return None

    def rank(item: tuple[int, int]) -> tuple[int, int, int]:
        panel_h, count = item
        # Lower rank wins: 16:9 match, prefer 1440/2160/1080, fewer panels
        # 越小越优先：匹配 16:9、偏好 1440/2160/1080、张数越少越好
        priority = {1440: 0, 2160: 1, 1080: 2, 1920: 3, 1280: 4, 720: 5}
        ideal_bonus = 0 if panel_h == ideal_16_9 else 1
        res_bonus = priority.get(panel_h, 9)
        return (ideal_bonus, res_bonus, count)

    candidates.sort(key=rank)
    return candidates[0][0]


def _pil_to_data_url(im) -> str:
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _normalize_image(im):
    from PIL import Image

    if im.mode in ("RGBA", "P"):
        rgba = im.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        return Image.alpha_composite(bg, rgba).convert("RGB")
    if im.mode != "RGB":
        return im.convert("RGB")
    return im


def _split_pil_image(im) -> list[str]:
    im = _normalize_image(im)
    width, height = im.size

    if height <= SPLIT_IMAGE_MIN_HEIGHT:
        return [_pil_to_data_url(im)]

    panel_h = detect_panel_height(width, height)
    if panel_h:
        panel_count = height // panel_h
        return [
            _pil_to_data_url(im.crop((0, i * panel_h, width, (i + 1) * panel_h)))
            for i in range(panel_count)
        ]

    # Unknown stitch pattern: fixed-height fallback strips
    # 无法识别拼接规律：按固定高度回退切片
    urls: list[str] = []
    y = 0
    while y < height:
        strip_h = min(FALLBACK_STRIP_HEIGHT, height - y)
        urls.append(_pil_to_data_url(im.crop((0, y, width, y + strip_h))))
        y += strip_h
    return urls


def _split_image_file(path: str) -> list[str]:
    from PIL import Image

    with Image.open(path) as im:
        return _split_pil_image(im)


def _split_data_url(data_url: str) -> list[str]:
    from PIL import Image

    if "," not in data_url:
        return [data_url]
    b64 = data_url.split(",", 1)[1]
    data = base64.b64decode(b64)
    with Image.open(io.BytesIO(data)) as im:
        return _split_pil_image(im)


def _strip_img_tag(urls: list[str], alt: str = "", panel_h: int | None = None) -> str:
    alt_attr = f' alt="{alt}"' if alt else ""
    panel_attr = f' data-nb2pdf-panel-h="{panel_h}"' if panel_h else ""

    if len(urls) == 1:
        return (
            f'<img src="{urls[0]}"{alt_attr} class="nb2pdf-img" '
            f'style="{_SINGLE_STYLE}"/>'
        )

    parts = [
        f'<div class="nb2pdf-img-stack"{panel_attr} style="{_STACK_STYLE}">'
    ]
    for i, url in enumerate(urls):
        parts.append(
            f'<img src="{url}"{alt_attr} class="nb2pdf-img nb2pdf-strip" '
            f'data-nb2pdf-panel-index="{i + 1}" style="{_STRIP_STYLE}"/>'
        )
    parts.append("</div>")
    return "\n".join(parts)


def embed_local_images(html: str, base_dir: str) -> str:
    """Embed local images; slice tall stitched images by panel height.
    内嵌本地图片；识别无缝拼接长图并按单帧高度切片。"""
    base_dir = os.path.abspath(base_dir)

    def replace_img_tag(match: re.Match) -> str:
        tag = match.group(0)
        src_m = _SRC_RE.search(tag)
        if not src_m:
            return tag

        src = src_m.group(1)
        alt_m = re.search(r"""alt=["']([^"']*)["']""", tag, re.IGNORECASE)
        alt = alt_m.group(1) if alt_m else ""

        try:
            from PIL import Image

            if src.startswith("data:"):
                if "," not in src:
                    return tag
                data = base64.b64decode(src.split(",", 1)[1])
                im = Image.open(io.BytesIO(data))
            elif src.startswith(("http://", "https://", "file:")):
                return tag
            else:
                path = os.path.normpath(os.path.join(base_dir, src.replace("/", os.sep)))
                if not os.path.isfile(path):
                    return tag
                im = Image.open(path)

            with im:
                w, h = im.size
                panel_h = detect_panel_height(w, h)
                urls = _split_pil_image(im)
        except Exception:
            return tag

        return _strip_img_tag(urls, alt, panel_h)

    return _IMG_TAG_RE.sub(replace_img_tag, html)
