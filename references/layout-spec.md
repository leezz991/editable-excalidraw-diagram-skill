# Hybrid Layout JSON Spec

Use a single JSON object. Coordinates are source-image pixels.

```json
{
  "canvas": { "width": 1672, "height": 941, "background": "#ffffff" },
  "rectangles": [
    {
      "id": "group_1",
      "x": 258,
      "y": 279,
      "width": 1400,
      "height": 193,
      "strokeColor": "#0b55c8",
      "backgroundColor": "transparent",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "radius": 12
    }
  ],
  "arrows": [
    {
      "id": "arrow_1",
      "x1": 620,
      "y1": 376,
      "x2": 660,
      "y2": 376,
      "strokeColor": "#0b55c8",
      "strokeWidth": 5,
      "endArrowhead": "triangle"
    }
  ],
  "assets": [
    {
      "id": "target_icon",
      "crop": { "x": 1298, "y": 356, "width": 64, "height": 64 },
      "x": 1298,
      "y": 356,
      "width": 64,
      "height": 64,
      "label": "target icon"
    },
    {
      "id": "clean_rule_icon",
      "source": "assets/clean-rule-icon.png",
      "crop": { "x": 0, "y": 0, "width": 1, "height": 1 },
      "x": 1300,
      "y": 759,
      "width": 28,
      "height": 28,
      "label": "clean rule icon"
    }
  ],
  "texts": [
    {
      "id": "role_title",
      "x": 1368,
      "y": 317,
      "width": 230,
      "height": 44,
      "text": "数据作用定位",
      "fontSize": 29,
      "fontFamily": 2,
      "textColor": "#0048b7"
    }
  ]
}
```

## Sections

- `canvas`: output canvas size and background color.
- `rectangles`: visible editable boxes, group frames, cards, title bars, dashed frames, and text boxes.
- `arrows`: editable connectors and flow arrows.
- `assets`: cropped image assets for icons, pictograms, illustrations, decorative symbols, and scene thumbnails.
- `texts`: editable Excalidraw text.

## Rectangle Fields

- `id`, `x`, `y`, `width`, `height`: required.
- `strokeColor`, `backgroundColor`, `strokeWidth`: optional visual styling.
- `strokeStyle`: `solid` or `dashed`.
- `radius`: rounded-corner radius intent. Use `0` for sharp boxes.

## Arrow Fields

- `x1`, `y1`, `x2`, `y2`: start and end coordinates.
- `endArrowhead`: usually `triangle`; set `null` for plain lines.
- `strokeStyle`: use `dashed` for dashed connectors.

## Asset Fields

- `crop`: source-image rectangle to crop.
- `source`: optional external PNG/JPEG path. Use it when a cropped icon has a dirty background or a clean generated raster icon blends better. If `source` is present, it takes precedence over `crop`.
- `x`, `y`, `width`, `height`: where to place the cropped asset in Excalidraw.
- `transparent`: optional background-removal hint. Use `{ "mode": "corner", "tolerance": 36 }` for flat-background crops.
- Use assets for complex graphics only: icons, pictograms, illustrations, badges, and small decorative symbols.
- Do not crop full text boxes just to avoid recreating text; text should be editable.

## Text Fields

- `text`: exact editable text. Use `\n` for line breaks.
- `fontSize`, `fontFamily`, `textColor`: visual styling.
- `textAlign` and `verticalAlign` default to `center` and `middle`.

## Practical Rules

- Rebuild structural boxes and connectors as Excalidraw elements.
- Crop icons and illustrations from the source image when they already look good.
- Replace dirty icon crops with clean transparent PNG assets through `source`.
- Do not shrink text element width based on estimated glyph width. Use the full layout box to avoid Chinese clipping.
- Keep text as Excalidraw text, even if that means using separate text elements over boxes.
- Prefer fewer image assets than many tiny icon fragments, but do not make one full-background image unless explicitly requested.
