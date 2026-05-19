# Excalidraw Notes

## Output Model

The hybrid editable file uses:

- `rectangle` elements for structural boxes, cards, title bars, frames, and dashed groups.
- `arrow` elements for connectors and flow arrows.
- `text` elements for editable labels and descriptions.
- `image` elements only for complex icons, pictograms, illustrations, badges, and decorative graphics.

Do not use one full background image unless the user explicitly asks for the legacy cleaned-background workflow.

## Text Sizing

For Chinese diagrams, keep text element `width` and `height` equal to the intended layout text box. Do not auto-shrink text bounds from estimated glyph width. Excalidraw font metrics can differ from local previews, and narrow bounds can clip Chinese text.

Recommended text settings:

- `autoResize: false`
- `lineHeight: 1.25`
- `textAlign: "center"` for most diagram labels
- `verticalAlign: "middle"` for box labels

## Image Files

Every image asset is embedded in the `.excalidraw` `files` map as a data URL.

Image elements use:

- `type: "image"`
- `fileId`
- `status: "saved"`
- `scale: [1, 1]`

Use `crop` when reusing a clean region from the source image. Use `source` when inserting a clean transparent PNG created separately.

## MCP Caveat

The Excalidraw MCP `create_view` accepts an elements JSON string and is useful for preview/checkpoint creation. The full `.excalidraw` file remains the authoritative deliverable because it embeds the image assets in `files`.

For MCP preview, pass `<prefix>.mcp-elements.json`. For full visual verification, open the uploaded Excalidraw URL or import the local `.excalidraw` file.
