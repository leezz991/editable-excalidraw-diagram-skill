---
name: editable-excalidraw-diagram
description: >-
  Convert AI-generated technical roadmap, research framework, flowchart, or diagram images into editable Excalidraw files using a hybrid approach that recreates structural boxes, groups, arrows, connectors, and text as editable Excalidraw elements, while inserting complex icons, illustrations, small pictograms, and decorative graphics as cropped image elements instead of rebuilding them from line primitives. Use when the user asks for image-to-Excalidraw conversion, editable .excalidraw output, technical-route/framework diagram replication, "icons should be images", "do not construct icons with lines", editable framework diagrams, or Excalidraw MCP preview/checkpoint generation.
---

# Editable Excalidraw Diagram

## Core Rule

Use a hybrid model:

- Recreate structural diagram elements as Excalidraw shapes: text boxes, group boxes, cards, arrows, connectors, section frames, dashed outlines, and labels.
- Insert complex visual assets as images: icons, pictograms, illustrations, decorative symbols, and scene thumbnails.
- Do not rebuild complex icons from many Excalidraw lines. Crop or recreate them as image elements.
- Text can be separate Excalidraw text or bound text; choose whichever is easiest to edit and aligns well.
- Give every text element the full layout box width and height. Do not shrink text bounds from estimated glyph width; narrow bounds cause Chinese text clipping in Excalidraw.
- If a cropped icon has dirty background, border fragments, or poor blending, replace it with a clean transparent PNG via the asset `source` field.

## Workflow

1. Inspect the source image visually.
2. Create a hybrid layout JSON using `references/layout-spec.md`.
3. Mark complex icons/illustrations in `assets` with crop coordinates from the source image.
4. Mark editable rectangles, frames, arrows, and text in `rectangles`, `arrows`, and `texts`.
5. Run `scripts/build_hybrid_excalidraw.py` to create:
   - editable `.excalidraw`
   - cropped asset PNG files
   - MCP elements JSON
   - text audit file
6. Run `scripts/call_excalidraw_mcp.mjs` to call Excalidraw MCP and optionally upload the `.excalidraw` file to an Excalidraw URL.
7. Report the `.excalidraw` path, asset directory, text audit path, share URL, and MCP checkpoint.

## Commands

Create the editable Excalidraw file with the hybrid workflow:

```powershell
python "<skill>/scripts/build_hybrid_excalidraw.py" `
  --image "C:\path\diagram.png" `
  --layout "C:\path\hybrid-layout.json" `
  --out "C:\path\output\diagram"
```

Legacy cleaned-background workflow, only when the user explicitly wants one background image plus editable text:

```powershell
python "<skill>/scripts/build_editable_excalidraw.py" `
  --image "C:\path\diagram.png" `
  --layout "C:\path\layout.json" `
  --out "C:\path\output\diagram"
```

Call Excalidraw MCP and create a share URL:

```powershell
node "<skill>/scripts/call_excalidraw_mcp.mjs" `
  --excalidraw "C:\path\output\diagram.excalidraw" `
  --mcp-elements "C:\path\output\diagram.mcp-elements.json" `
  --out "C:\path\output\diagram"
```

If the Node script reports that `@modelcontextprotocol/sdk` is missing, install it in the working directory:

```powershell
npm install @modelcontextprotocol/sdk
```

## Layout Guidance

- Coordinates are in source image pixels.
- Use the image's original size as the Excalidraw canvas size.
- Use Excalidraw rectangles for visible boxes and frames.
- Use Excalidraw arrows/lines for connectors.
- Use image assets for small icons, pictograms, illustrations, and complex decorative graphics.
- Prefer a cropped source icon when the icon already looks good; use generated/recreated raster icons only when the source crop is poor.
- For small icons inside text boxes, prefer clean transparent PNGs over source crops when the crop includes box borders, text underlines, halos, or background patches.
- Keep text editable as Excalidraw text. It may be standalone text or bound text.

## Quality Checks

Before finishing, verify:

- Image elements are used only for complex icons, pictograms, scene thumbnails, and illustrations.
- Complex icons/illustrations are image elements, not hand-built from many line segments.
- Text boxes, frames, arrows, and connectors are Excalidraw elements.
- The file contains editable text elements for all text blocks.
- Text elements use generous boxes and no important text is clipped.
- Small icon assets blend with their target background and do not carry unwanted source-image patches.
- The text audit file has no obvious OCR/visual transcription errors.

## References

- `references/layout-spec.md`: layout JSON schema and examples.
- `references/workflow.md`: detailed conversion procedure.
- `references/excalidraw-notes.md`: Excalidraw JSON and MCP notes.
- `references/implementation-cn.md`: Chinese explanation of the hybrid implementation strategy and tradeoffs.
- `README.md`: Chinese open-source usage guide.
