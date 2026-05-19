# Workflow

## 1. Inspect the Image

Open the source image at original resolution. Split the content into four editable categories:

- `rectangles`: visible cards, text boxes, grouping frames, title bars, section frames, dashed boxes.
- `arrows`: flow arrows, connectors, dashed arrows, simple guide lines.
- `texts`: all readable labels, titles, subtitles, descriptions, legends, button text.
- `assets`: icons, pictograms, badges, illustrations, scene thumbnails, complex decorative graphics.

Do not rebuild icons from many Excalidraw lines. Use image assets for those.

## 2. Build Hybrid Layout JSON

Create a layout JSON next to the output. Use source-image pixel coordinates.

For structural shapes:

- Match the visible box and arrow positions closely.
- Use native Excalidraw rectangles and arrows for anything the user may want to move, resize, recolor, or reconnect.
- Keep section frames and grouping boxes editable.

For text:

- Use exact text, with explicit `\n` line breaks when the source stacks Chinese lines.
- Give each text element the full intended text area. Do not shrink width to estimated text width.
- Use slightly generous text boxes for Chinese labels because Excalidraw and local preview fonts can differ.
- Use a text audit file to verify transcription.

For assets:

- Crop icons and illustrations from the source only when the crop is clean.
- If a crop includes nearby border lines, underlines, text shadows, halos, or background patches, create or provide a clean transparent PNG and reference it with `source`.
- Use `transparent: { "mode": "corner", "tolerance": 36 }` for simple flat-background crops.

## 3. Generate Excalidraw

Run:

```powershell
python "<skill>/scripts/build_hybrid_excalidraw.py" --image "<image>" --layout "<layout.json>" --out "<output-prefix>"
```

The script writes:

- `<prefix>.excalidraw`
- `<prefix>.assets/`
- `<prefix>.mcp-elements.json`
- `<prefix>.text-audit.md`

## 4. Call Excalidraw MCP

Run:

```powershell
node "<skill>/scripts/call_excalidraw_mcp.mjs" --excalidraw "<prefix>.excalidraw" --mcp-elements "<prefix>.mcp-elements.json" --out "<prefix>"
```

The script writes:

- `<prefix>.mcp-result.json`
- `<prefix>.url.txt`

## 5. Verify

Open the Excalidraw URL or import the `.excalidraw` file.

Check:

- Structural boxes, arrows, and connector lines are editable Excalidraw elements.
- Icons and illustrations are image elements, not line-fragment reconstructions.
- Text can be selected and edited.
- No text is clipped. If text is clipped, enlarge the layout text box or reduce font size.
- Small icons have clean transparent backgrounds and visually blend into cards or text boxes.
- The audit file text matches the source image.

## Fallbacks

- If a crop is dirty, use a clean transparent PNG through the `source` asset field.
- If local OCR is unavailable, use Codex visual reading and a manual audit list.
- If the user explicitly wants "one image background plus editable text", use the legacy `build_editable_excalidraw.py` workflow instead of the hybrid workflow.
