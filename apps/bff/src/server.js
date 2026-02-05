import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";

const app = express();
app.use(express.json({ limit: "2mb" }));

const AI_CORE_URL = process.env.AI_CORE_URL || "http://localhost:8000";

app.get("/health", (_, res) => res.json({ ok: true, aiCore: AI_CORE_URL }));

app.use(
  "/api",
  createProxyMiddleware({
    target: AI_CORE_URL,
    changeOrigin: true,
    pathRewrite: { "^/api": "" }, // /api/chat -> /chat
  })
);

app.listen(3000, () => console.log("BFF listening on :3000"));
