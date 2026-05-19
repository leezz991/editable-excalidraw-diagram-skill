#!/usr/bin/env node
import { readFile, writeFile } from "node:fs/promises";
import { deflateSync } from "node:zlib";
import { createRequire } from "node:module";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    const value = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : true;
    args[key] = value;
  }
  return args;
}

function concatBuffers(...bufs) {
  let total = 4;
  for (const b of bufs) total += 4 + b.length;
  const out = new Uint8Array(total);
  const dv = new DataView(out.buffer);
  dv.setUint32(0, 1);
  let off = 4;
  for (const b of bufs) {
    dv.setUint32(off, b.length);
    off += 4;
    out.set(b, off);
    off += b.length;
  }
  return out;
}

async function uploadToExcalidraw(json) {
  const te = new TextEncoder();
  const innerPayload = concatBuffers(te.encode(JSON.stringify({})), te.encode(json));
  const compressed = deflateSync(Buffer.from(innerPayload));
  const key = await globalThis.crypto.subtle.generateKey({ name: "AES-GCM", length: 128 }, true, ["encrypt"]);
  const iv = globalThis.crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await globalThis.crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, compressed);
  const meta = te.encode(JSON.stringify({ version: 2, compression: "pako@1", encryption: "AES-GCM" }));
  const payload = Buffer.from(concatBuffers(meta, iv, new Uint8Array(encrypted)));
  const res = await fetch("https://json.excalidraw.com/api/v2/post/", { method: "POST", body: payload });
  if (!res.ok) throw new Error(`Upload failed: ${res.status} ${res.statusText}`);
  const { id } = await res.json();
  const jwk = await globalThis.crypto.subtle.exportKey("jwk", key);
  return `https://excalidraw.com/#json=${id},${jwk.k}`;
}

async function callMcp(elementsJson, url) {
  let Client;
  let StreamableHTTPClientTransport;
  try {
    ({ Client } = await import("@modelcontextprotocol/sdk/client/index.js"));
    ({ StreamableHTTPClientTransport } = await import("@modelcontextprotocol/sdk/client/streamableHttp.js"));
  } catch (error) {
    try {
      const requireFromCwd = createRequire(join(process.cwd(), "package.json"));
      const clientPath = requireFromCwd.resolve("@modelcontextprotocol/sdk/client/index.js");
      const transportPath = requireFromCwd.resolve("@modelcontextprotocol/sdk/client/streamableHttp.js");
      ({ Client } = await import(pathToFileURL(clientPath).href));
      ({ StreamableHTTPClientTransport } = await import(pathToFileURL(transportPath).href));
    } catch (cwdError) {
      throw new Error(`Missing @modelcontextprotocol/sdk. Run: npm install @modelcontextprotocol/sdk\n${error.message}\n${cwdError.message}`);
    }
  }

  const client = new Client({ name: "editable-excalidraw-diagram", version: "1.0.0" });
  await client.connect(new StreamableHTTPClientTransport(new URL(url)));
  try {
    return await client.callTool({
      name: "create_view",
      arguments: { elements: elementsJson },
    });
  } finally {
    await client.close();
  }
}

function checkpointFrom(result) {
  if (result?.structuredContent?.checkpointId) return result.structuredContent.checkpointId;
  const text = result?.content?.map((item) => item.text ?? "").join("\n") ?? "";
  return text.match(/Checkpoint id: "([^"]+)"/)?.[1] ?? "";
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.out) throw new Error("Required: --out <output-prefix>");
  if (!args.excalidraw && !args["mcp-elements"]) {
    throw new Error("Required: --excalidraw <file.excalidraw> and/or --mcp-elements <file.json>");
  }

  const out = String(args.out);
  const mcpUrl = String(args.url ?? "https://mcp.excalidraw.com");
  const summary = {};

  if (args.excalidraw) {
    const excalidrawJson = await readFile(String(args.excalidraw), "utf8");
    const shareUrl = await uploadToExcalidraw(excalidrawJson);
    await writeFile(`${out}.url.txt`, `${shareUrl}\n`, "utf8");
    summary.shareUrl = shareUrl;
  }

  if (args["mcp-elements"]) {
    const elementsJson = await readFile(String(args["mcp-elements"]), "utf8");
    const result = await callMcp(elementsJson, mcpUrl);
    await writeFile(`${out}.mcp-result.json`, JSON.stringify(result, null, 2), "utf8");
    summary.checkpoint = checkpointFrom(result);
    summary.mcpResult = `${out}.mcp-result.json`;
  }

  console.log(JSON.stringify(summary, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
