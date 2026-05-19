#!/usr/bin/env python3
"""Build an editable Excalidraw file from a diagram image and text layout JSON.

The script keeps all non-text visuals as one cleaned background image and adds
editable transparent text containers on top.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import time
import uuid
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def clamp_box(x: float, y: float, w: float, h: float, max_w: int, max_h: int) -> tuple[int, int, int, int]:
    x1 = max(0, int(round(x)))
    y1 = max(0, int(round(y)))
    x2 = min(max_w, int(round(x + w)))
    y2 = min(max_h, int(round(y + h)))
    return x1, y1, max(x1, x2), max(y1, y2)


def erase_text_regions(image: Image.Image, layout: dict[str, Any]) -> Image.Image:
    cleaned = image.convert("RGBA")
    draw = ImageDraw.Draw(cleaned)
    defaults = layout.get("defaults", {})
    default_fill = defaults.get("eraseFill", "#ffffff")

    for box in layout.get("text_boxes", []):
        erase = box.get("erase", {})
        if erase is False or erase.get("enabled") is False:
            continue

        fill = erase.get("fill", box.get("eraseFill", default_fill))
        padding = float(erase.get("padding", box.get("erasePadding", 0)))
        ex = float(erase.get("x", box["x"])) - padding
        ey = float(erase.get("y", box["y"])) - padding
        ew = float(erase.get("width", box["width"])) + padding * 2
        eh = float(erase.get("height", box["height"])) + padding * 2
        x1, y1, x2, y2 = clamp_box(ex, ey, ew, eh, cleaned.width, cleaned.height)
        radius = int(erase.get("radius", 0))
        if radius > 0:
            draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)
        else:
            draw.rectangle([x1, y1, x2, y2], fill=fill)
    return cleaned


def data_url(path: Path) -> tuple[str, str]:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return mime, f"data:{mime};base64,{encoded}"


def text_dimensions(text: str, font_size: float, width: float, height: float) -> tuple[float, float, int]:
    lines = str(text).split("\n") or [""]
    line_height = 1.25
    estimated_width = min(width, max(1, max(len(line) for line in lines) * font_size * 0.58))
    estimated_height = min(height, max(font_size * line_height, len(lines) * font_size * line_height))
    baseline = int(round(estimated_height * 0.78))
    return estimated_width, estimated_height, baseline


def make_text_pair(box: dict[str, Any], defaults: dict[str, Any], index: int) -> list[dict[str, Any]]:
    raw_id = str(box.get("id") or f"text_{index + 1}")
    safe = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in raw_id)[:48]
    container_id = f"{safe}_container"
    text_id = f"{safe}_text"

    x = float(box["x"])
    y = float(box["y"])
    w = float(box["width"])
    h = float(box["height"])
    value = str(box.get("text", ""))
    font_size = float(box.get("fontSize", defaults.get("fontSize", 28)))
    font_family = int(box.get("fontFamily", defaults.get("fontFamily", 1)))
    text_color = box.get("textColor", defaults.get("textColor", "#111111"))
    text_align = box.get("textAlign", defaults.get("textAlign", "center"))
    vertical_align = box.get("verticalAlign", defaults.get("verticalAlign", "middle"))
    text_w, text_h, baseline = text_dimensions(value, font_size, w, h)

    container = {
        "id": container_id,
        "type": "rectangle",
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "angle": 0,
        "strokeColor": "transparent",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 3},
        "seed": 1000 + index * 2,
        "version": 1,
        "versionNonce": 2000 + index * 2,
        "isDeleted": False,
        "boundElements": [{"type": "text", "id": text_id}],
        "updated": 1,
        "link": None,
        "locked": False,
    }
    text_el = {
        "id": text_id,
        "type": "text",
        "x": x + (w - text_w) / 2 if text_align == "center" else x,
        "y": y + (h - text_h) / 2 if vertical_align == "middle" else y,
        "width": text_w,
        "height": text_h,
        "angle": 0,
        "strokeColor": text_color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": 1001 + index * 2,
        "version": 1,
        "versionNonce": 2001 + index * 2,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
        "text": value,
        "fontSize": font_size,
        "fontFamily": font_family,
        "textAlign": text_align,
        "verticalAlign": vertical_align,
        "containerId": container_id,
        "originalText": value,
        "autoResize": False,
        "lineHeight": 1.25,
        "baseline": baseline,
    }
    return [container, text_el]


def make_image_element(cleaned_path: Path, image_cfg: dict[str, Any], canvas_w: int, canvas_h: int) -> tuple[dict[str, Any], dict[str, Any]]:
    mime, url = data_url(cleaned_path)
    file_id = uuid.uuid4().hex
    x = float(image_cfg.get("x", 0))
    y = float(image_cfg.get("y", 0))
    w = float(image_cfg.get("width", canvas_w))
    h = float(image_cfg.get("height", canvas_h))
    image_element = {
        "id": "cleaned_background_image",
        "type": "image",
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "angle": 0,
        "strokeColor": "transparent",
        "backgroundColor": "transparent",
        "fillStyle": "hachure",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": 999,
        "version": 1,
        "versionNonce": 1999,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
        "fileId": file_id,
        "scale": [1, 1],
        "status": "saved",
    }
    file_entry = {
        "mimeType": mime,
        "id": file_id,
        "dataURL": url,
        "created": int(time.time() * 1000),
        "lastRetrieved": int(time.time() * 1000),
    }
    return image_element, file_entry


def build_excalidraw(cleaned_path: Path, layout: dict[str, Any], source_size: tuple[int, int]) -> dict[str, Any]:
    canvas = layout.get("canvas", {})
    canvas_w = int(canvas.get("width", source_size[0]))
    canvas_h = int(canvas.get("height", source_size[1]))
    image_element, file_entry = make_image_element(cleaned_path, layout.get("image", {}), canvas_w, canvas_h)

    elements = [image_element]
    defaults = layout.get("defaults", {})
    for index, box in enumerate(layout.get("text_boxes", [])):
        elements.extend(make_text_pair(box, defaults, index))

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": canvas.get("background", "#ffffff"),
        },
        "files": {file_entry["id"]: file_entry},
    }


def build_mcp_elements(layout: dict[str, Any], source_size: tuple[int, int]) -> list[dict[str, Any]]:
    canvas = layout.get("canvas", {})
    width = int(canvas.get("width", source_size[0]))
    height = int(canvas.get("height", source_size[1]))
    camera_w = max(400, min(1600, width))
    camera_h = int(camera_w * 3 / 4)
    if camera_h < height and camera_w < 1600:
        camera_w = 1600
        camera_h = 1200
    elements: list[dict[str, Any]] = [{"type": "cameraUpdate", "width": camera_w, "height": camera_h, "x": 0, "y": 0}]
    elements.append({
        "type": "rectangle",
        "id": "mcp_background_note",
        "x": 0,
        "y": 0,
        "width": width,
        "height": height,
        "strokeColor": "#d0d7de",
        "backgroundColor": "#ffffff",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "roughness": 0,
    })
    defaults = layout.get("defaults", {})
    for index, box in enumerate(layout.get("text_boxes", [])):
        for el in make_text_pair(box, defaults, index):
            if el["type"] == "rectangle":
                el = {
                    "type": "rectangle",
                    "id": el["id"],
                    "x": el["x"],
                    "y": el["y"],
                    "width": el["width"],
                    "height": el["height"],
                    "strokeColor": "#d0d7de",
                    "backgroundColor": "transparent",
                    "strokeWidth": 1,
                    "strokeStyle": "dashed",
                    "roughness": 0,
                }
            else:
                el = {
                    "type": "text",
                    "id": el["id"],
                    "x": el["x"],
                    "y": el["y"],
                    "width": el["width"],
                    "height": el["height"],
                    "text": el["text"],
                    "fontSize": el["fontSize"],
                    "strokeColor": el["strokeColor"],
                }
            elements.append(el)
    return elements


def write_audit(path: Path, layout: dict[str, Any]) -> None:
    lines = ["# Text Audit", ""]
    for index, box in enumerate(layout.get("text_boxes", []), start=1):
        review = box.get("review", "")
        review_suffix = f"  REVIEW: {review}" if review else ""
        lines.append(f"{index}. `{box.get('id', 'text_' + str(index))}`{review_suffix}")
        lines.append("")
        lines.append(str(box.get("text", "")).replace("\n", " / "))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build editable Excalidraw from a diagram image and layout JSON.")
    parser.add_argument("--image", required=True, type=Path, help="Source image path.")
    parser.add_argument("--layout", required=True, type=Path, help="Layout JSON path.")
    parser.add_argument("--out", required=True, type=Path, help="Output prefix without extension.")
    args = parser.parse_args()

    image = Image.open(args.image)
    layout = read_json(args.layout)
    cleaned = erase_text_regions(image, layout)

    out_prefix = args.out
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    cleaned_path = out_prefix.with_suffix(".cleaned.png")
    excalidraw_path = out_prefix.with_suffix(".excalidraw")
    mcp_path = out_prefix.with_suffix(".mcp-elements.json")
    audit_path = out_prefix.with_suffix(".text-audit.md")

    cleaned.save(cleaned_path)
    excalidraw = build_excalidraw(cleaned_path, layout, image.size)
    excalidraw_path.write_text(json.dumps(excalidraw, ensure_ascii=False, indent=2), encoding="utf-8")
    mcp_path.write_text(json.dumps(build_mcp_elements(layout, image.size), ensure_ascii=False), encoding="utf-8")
    write_audit(audit_path, layout)

    print(json.dumps({
        "cleaned": str(cleaned_path),
        "excalidraw": str(excalidraw_path),
        "mcp_elements": str(mcp_path),
        "text_audit": str(audit_path),
        "text_boxes": len(layout.get("text_boxes", [])),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
