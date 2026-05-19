#!/usr/bin/env python3
"""Build a hybrid editable Excalidraw diagram.

Structural boxes, arrows, and text are Excalidraw elements. Complex icons and
illustrations are cropped from the source image and inserted as image elements.
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

from PIL import Image


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def now_ms() -> int:
    return int(time.time() * 1000)


def data_url(path: Path) -> tuple[str, str]:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return mime, f"data:{mime};base64,{encoded}"


def base(el: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "angle": 0,
        "strokeColor": "#0b3f8c",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": 100000 + index,
        "version": 1,
        "versionNonce": 200000 + index,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
        **el,
    }


def text_metrics(value: str, font_size: float, width: float, height: float) -> tuple[float, float, int]:
    # Keep the layout-provided box size. Excalidraw can otherwise clip CJK text
    # when an estimated glyph width is too narrow.
    return width, height, int(round(height * 0.78))


def make_text(item: dict[str, Any], index: int) -> dict[str, Any]:
    value = str(item.get("text", ""))
    x = float(item["x"])
    y = float(item["y"])
    width = float(item["width"])
    height = float(item["height"])
    font_size = float(item.get("fontSize", 24))
    text_width, text_height, baseline = text_metrics(value, font_size, width, height)
    align = item.get("textAlign", "center")
    valign = item.get("verticalAlign", "middle")
    tx = x
    ty = y
    return base({
        "type": "text",
        "id": item.get("id", f"text_{index}"),
        "x": tx,
        "y": ty,
        "width": text_width,
        "height": text_height,
        "strokeColor": item.get("textColor", "#111111"),
        "text": value,
        "fontSize": font_size,
        "fontFamily": int(item.get("fontFamily", 1)),
        "textAlign": align,
        "verticalAlign": valign,
        "containerId": item.get("containerId"),
        "originalText": value,
        "autoResize": False,
        "lineHeight": 1.25,
        "baseline": baseline,
    }, index)


def make_rect(item: dict[str, Any], index: int) -> dict[str, Any]:
    radius = item.get("radius", 8)
    return base({
        "type": "rectangle",
        "id": item.get("id", f"rect_{index}"),
        "x": float(item["x"]),
        "y": float(item["y"]),
        "width": float(item["width"]),
        "height": float(item["height"]),
        "strokeColor": item.get("strokeColor", "#0b3f8c"),
        "backgroundColor": item.get("backgroundColor", "transparent"),
        "strokeWidth": item.get("strokeWidth", 2),
        "strokeStyle": item.get("strokeStyle", "solid"),
        "roundness": {"type": 3, "value": radius} if radius else None,
    }, index)


def make_arrow(item: dict[str, Any], index: int) -> dict[str, Any]:
    x1 = float(item["x1"])
    y1 = float(item["y1"])
    x2 = float(item["x2"])
    y2 = float(item["y2"])
    return base({
        "type": "arrow",
        "id": item.get("id", f"arrow_{index}"),
        "x": x1,
        "y": y1,
        "width": x2 - x1,
        "height": y2 - y1,
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "strokeColor": item.get("strokeColor", "#0b55c8"),
        "strokeWidth": item.get("strokeWidth", 4),
        "strokeStyle": item.get("strokeStyle", "solid"),
        "startArrowhead": item.get("startArrowhead"),
        "endArrowhead": item.get("endArrowhead", "triangle"),
    }, index)


def make_image_element(item: dict[str, Any], file_id: str, index: int) -> dict[str, Any]:
    return base({
        "type": "image",
        "id": item.get("id", f"asset_{index}"),
        "x": float(item["x"]),
        "y": float(item["y"]),
        "width": float(item["width"]),
        "height": float(item["height"]),
        "strokeColor": "transparent",
        "backgroundColor": "transparent",
        "fileId": file_id,
        "scale": [1, 1],
        "status": "saved",
    }, index)


def apply_corner_transparency(img: Image.Image, tolerance: int) -> Image.Image:
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    corners = [
        pixels[0, 0],
        pixels[rgba.width - 1, 0],
        pixels[0, rgba.height - 1],
        pixels[rgba.width - 1, rgba.height - 1],
    ]
    bg = tuple(sum(c[i] for c in corners) // len(corners) for i in range(3))
    tol_sq = tolerance * tolerance
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            dist_sq = (r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2
            if dist_sq <= tol_sq:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def crop_assets(source: Image.Image, layout: dict[str, Any], asset_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    elements: list[dict[str, Any]] = []
    files: dict[str, Any] = {}
    asset_dir.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(layout.get("assets", []), start=1):
        asset_path = asset_dir / f"{item.get('id', 'asset_' + str(index))}.png"
        if item.get("source"):
            cropped = Image.open(Path(item["source"])).convert("RGBA")
        else:
            crop = item["crop"]
            x = int(crop["x"])
            y = int(crop["y"])
            w = int(crop["width"])
            h = int(crop["height"])
            cropped = source.crop((x, y, x + w, y + h)).convert("RGBA")
        transparent = item.get("transparent")
        if transparent:
            tolerance = int(transparent.get("tolerance", 36))
            mode = transparent.get("mode", "corner")
            if mode == "corner":
                cropped = apply_corner_transparency(cropped, tolerance)
        cropped.save(asset_path)
        mime, url = data_url(asset_path)
        file_id = uuid.uuid4().hex
        files[file_id] = {
            "mimeType": mime,
            "id": file_id,
            "dataURL": url,
            "created": now_ms(),
            "lastRetrieved": now_ms(),
        }
        elements.append(make_image_element(item, file_id, index))
    return elements, files


def build(layout: dict[str, Any], image_path: Path, out_prefix: Path) -> dict[str, Any]:
    source = Image.open(image_path).convert("RGBA")
    canvas = layout.get("canvas", {})
    width = int(canvas.get("width", source.width))
    height = int(canvas.get("height", source.height))
    asset_dir = out_prefix.parent / f"{out_prefix.name}.assets"
    image_elements, files = crop_assets(source, layout, asset_dir)

    elements: list[dict[str, Any]] = []
    idx = 1
    for item in layout.get("rectangles", []):
        elements.append(make_rect(item, idx)); idx += 1
    for item in layout.get("arrows", []):
        elements.append(make_arrow(item, idx)); idx += 1
    elements.extend(image_elements)
    idx += len(image_elements)
    for item in layout.get("texts", []):
        elements.append(make_text(item, idx)); idx += 1

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"gridSize": None, "viewBackgroundColor": canvas.get("background", "#ffffff")},
        "files": files,
        "_assetDir": str(asset_dir),
        "_canvas": {"width": width, "height": height},
    }


def mcp_elements(layout: dict[str, Any], canvas: dict[str, int]) -> list[dict[str, Any]]:
    width = canvas["width"]
    camera_w = 1600 if width > 1200 else 1200
    camera_h = int(camera_w * 3 / 4)
    out: list[dict[str, Any]] = [{"type": "cameraUpdate", "width": camera_w, "height": camera_h, "x": 0, "y": 0}]
    for item in layout.get("rectangles", []):
        out.append({
            "type": "rectangle",
            "id": item.get("id"),
            "x": item["x"], "y": item["y"], "width": item["width"], "height": item["height"],
            "strokeColor": item.get("strokeColor", "#0b3f8c"),
            "backgroundColor": item.get("backgroundColor", "transparent"),
            "strokeWidth": item.get("strokeWidth", 2),
            "strokeStyle": item.get("strokeStyle", "solid"),
            "roughness": 0,
        })
    for item in layout.get("arrows", []):
        out.append({
            "type": "arrow",
            "id": item.get("id"),
            "x": item["x1"], "y": item["y1"], "width": item["x2"] - item["x1"], "height": item["y2"] - item["y1"],
            "points": [[0, 0], [item["x2"] - item["x1"], item["y2"] - item["y1"]]],
            "strokeColor": item.get("strokeColor", "#0b55c8"),
            "strokeWidth": item.get("strokeWidth", 4),
            "endArrowhead": item.get("endArrowhead", "triangle"),
        })
    for item in layout.get("assets", []):
        out.append({
            "type": "rectangle",
            "id": item.get("id"),
            "x": item["x"], "y": item["y"], "width": item["width"], "height": item["height"],
            "strokeColor": "#b0b0b0", "backgroundColor": "#f1f5f9", "strokeStyle": "dashed", "strokeWidth": 1,
            "label": {"text": item.get("label", item.get("id", "image")), "fontSize": 14},
        })
    for item in layout.get("texts", []):
        out.append({
            "type": "text",
            "id": item.get("id"),
            "x": item["x"], "y": item["y"],
            "width": item["width"], "height": item["height"],
            "text": item.get("text", ""),
            "fontSize": item.get("fontSize", 24),
            "strokeColor": item.get("textColor", "#111111"),
        })
    return out


def write_audit(path: Path, layout: dict[str, Any]) -> None:
    lines = ["# Text Audit", ""]
    for i, item in enumerate(layout.get("texts", []), start=1):
        lines.append(f"{i}. `{item.get('id', 'text_' + str(i))}`")
        lines.append("")
        lines.append(str(item.get("text", "")).replace("\n", " / "))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--layout", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    layout = read_json(args.layout)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    data = build(layout, args.image, args.out)
    asset_dir = data.pop("_assetDir")
    canvas = data.pop("_canvas")

    excalidraw_path = args.out.with_suffix(".excalidraw")
    mcp_path = args.out.with_suffix(".mcp-elements.json")
    audit_path = args.out.with_suffix(".text-audit.md")
    excalidraw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    mcp_path.write_text(json.dumps(mcp_elements(layout, canvas), ensure_ascii=False), encoding="utf-8")
    write_audit(audit_path, layout)

    print(json.dumps({
        "excalidraw": str(excalidraw_path),
        "assets": asset_dir,
        "mcp_elements": str(mcp_path),
        "text_audit": str(audit_path),
        "rectangles": len(layout.get("rectangles", [])),
        "arrows": len(layout.get("arrows", [])),
        "assets_count": len(layout.get("assets", [])),
        "texts": len(layout.get("texts", [])),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
