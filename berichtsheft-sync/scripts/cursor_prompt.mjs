#!/usr/bin/env node
/**
 * Local Cursor agent one-shot — stdin = prompt, stdout = JSON result.
 * Requires: npm install (@cursor/sdk in project root)
 */
import { Agent } from "@cursor/sdk";

const apiKey = process.env.CURSOR_API_KEY;
const cwd = process.env.CURSOR_AGENT_CWD || process.cwd();
const modelId = process.env.CURSOR_AGENT_MODEL || "composer-2.5";

async function main() {
  if (!apiKey) {
    console.log(JSON.stringify({ ok: false, error: "CURSOR_API_KEY missing" }));
    process.exit(1);
  }
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  const prompt = Buffer.concat(chunks).toString("utf8").trim();
  if (!prompt) {
    console.log(JSON.stringify({ ok: false, error: "empty prompt" }));
    process.exit(1);
  }
  try {
    const result = await Agent.prompt(prompt, {
      apiKey,
      model: { id: modelId },
      local: { cwd },
    });
    console.log(
      JSON.stringify({
        ok: result.status === "completed",
        status: result.status,
        result: result.result || "",
        agent_id: result.agentId || null,
      })
    );
  } catch (e) {
    console.log(JSON.stringify({ ok: false, error: String(e.message || e) }));
    process.exit(1);
  }
}

main();
