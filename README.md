# AI 技术路线图转可编辑 Excalidraw Skill

这个 Codex skill 用于把 AI 生成的技术路线图、研究框架图、流程图等图片，快速转换成可继续编辑的 `.excalidraw` 文件。

核心思路是“结构可编辑 + 图标图片化”：

- 文本框、分组框、合并框、标题条、连接线、箭头：用 Excalidraw 原生元素重新生成，方便后续编辑。
- 图标、小图案、场景插画、徽章、装饰符号：作为图片元素插入，不用大量线条硬拼。
- 所有文字：生成 Excalidraw 文本元素，方便直接修改。

## 适用场景

- AI 生成的中文技术路线图。
- 研究框架图、课题技术路线图、数据治理流程图。
- 含少量图标、插画、场景图的汇报型图示。
- 希望后续能编辑框线、箭头和文字，但不需要逐线编辑复杂图标。

## 为什么不是整张图直接当底图

一开始可以把原图擦掉文字后作为底图，再叠加可编辑文字。但这种方式有明显限制：框线、分组框、箭头仍然不能编辑。

实际使用后，更好的方案是混合重建：

- 结构线框和箭头本来就适合用 Excalidraw 表达，应该原生生成。
- 图标和插画细节多，矢量重画成本高且容易失真，应该图片化。
- 文字最常被修改，必须保持可编辑。

## 关键经验

### 1. 中文文本框不要自动缩宽

生成 `.excalidraw` 时，文本元素应该使用布局 JSON 中给定的完整 `width` 和 `height`。不要按字符数量估算一个更窄的宽度，否则 Excalidraw 里容易出现中文显示不全、被裁切的问题。

### 2. 小图标裁切不干净时，用透明 PNG 替换

源图里的小图标经常贴着边线、浅色底或阴影。直接裁切会带出异常底色，放进 Excalidraw 后和背景融合不好。

推荐顺序：

1. 源图裁切干净：使用 `crop`。
2. 背景颜色单一：使用 `transparent` 去掉角落背景色。
3. 仍然有脏边：用干净透明 PNG，并通过 `source` 引用。

### 3. 必须输出文字核对清单

默认不强制依赖 PaddleOCR/EasyOCR。Codex 视觉识别后会输出 `text-audit.md`，用于人工快速核对中文内容。

## 安装

从 GitHub 克隆后，把本目录复制到 Codex skills 目录：

```powershell
git clone https://github.com/leezz991/editable-excalidraw-diagram-skill.git
Copy-Item -Recurse .\editable-excalidraw-diagram-skill "$env:USERPROFILE\.codex\skills\editable-excalidraw-diagram"
```

Python 依赖：

```powershell
pip install pillow
```

如果需要调用 Excalidraw MCP：

```powershell
npm install @modelcontextprotocol/sdk
```

Codex MCP 配置示例：

```toml
[mcp_servers.excalidraw]
url = "https://mcp.excalidraw.com"
transport = "streamable_http"
```

## 使用流程

1. 给 Codex 一张技术路线图图片。
2. 让 Codex 使用 `$editable-excalidraw-diagram`。
3. Codex 视觉识别图片，整理结构框、箭头、文本、图标区域。
4. 生成 layout JSON。
5. 运行混合生成脚本：

```powershell
python "<skill>/scripts/build_hybrid_excalidraw.py" `
  --image "C:\path\diagram.png" `
  --layout "C:\path\layout.json" `
  --out "C:\path\output\diagram"
```

6. 调用 Excalidraw MCP 并生成链接：

```powershell
node "<skill>/scripts/call_excalidraw_mcp.mjs" `
  --excalidraw "C:\path\output\diagram.excalidraw" `
  --mcp-elements "C:\path\output\diagram.mcp-elements.json" `
  --out "C:\path\output\diagram"
```

## 输出文件

- `<prefix>.excalidraw`：最终可编辑文件。
- `<prefix>.assets/`：裁切或生成的图标/插画资产。
- `<prefix>.mcp-elements.json`：给 Excalidraw MCP 预览用的元素 JSON。
- `<prefix>.text-audit.md`：文字核对清单。
- `<prefix>.url.txt`：上传后的 Excalidraw 链接。
- `<prefix>.mcp-result.json`：MCP 返回结果和 checkpoint 信息。

## Layout JSON 简要示例

```json
{
  "canvas": { "width": 1672, "height": 941, "background": "#ffffff" },
  "rectangles": [
    {
      "id": "data_group",
      "x": 258,
      "y": 279,
      "width": 1400,
      "height": 193,
      "strokeColor": "#0b55c8",
      "backgroundColor": "transparent",
      "strokeWidth": 2,
      "radius": 12
    }
  ],
  "arrows": [
    {
      "id": "flow_1",
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
      "height": 64
    },
    {
      "id": "clean_icon",
      "source": "assets/clean-icon.png",
      "crop": { "x": 0, "y": 0, "width": 1, "height": 1 },
      "x": 1300,
      "y": 759,
      "width": 28,
      "height": 28
    }
  ],
  "texts": [
    {
      "id": "title",
      "x": 382,
      "y": 317,
      "width": 190,
      "height": 44,
      "text": "全数据梳理",
      "fontSize": 29,
      "fontFamily": 2,
      "textColor": "#0048b7"
    }
  ]
}
```

## 质量检查

生成后重点检查：

- 框、箭头、分组线是否是 Excalidraw 元素。
- 图标/插画是否是图片元素，而不是大量线段。
- 中文是否完整显示，没有被裁切。
- 小图标是否有异常底色或脏边。
- `text-audit.md` 是否有错字、漏字、错误换行。

## Legacy 模式

如果用户明确要求“整张图作为底图，只让文字可编辑”，可以使用：

```powershell
python "<skill>/scripts/build_editable_excalidraw.py" `
  --image "C:\path\diagram.png" `
  --layout "C:\path\legacy-layout.json" `
  --out "C:\path\output\diagram"
```

默认建议使用 hybrid 模式。
