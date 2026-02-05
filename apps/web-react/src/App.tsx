import React, { useState } from "react";
import { postJSON } from "./lib/api";

type Citation = { doc_title: string; page?: number; file_path?: string; score: number };
type ChatResp = { trace_id: string; doc_group: string; answer: string; citations: Citation[] };

export default function App() {
  const [q, setQ] = useState("");
  const [chat, setChat] = useState<ChatResp | null>(null);
  const [scenario, setScenario] = useState("");
  const [report, setReport] = useState<any>(null);

  return (
    <div style={{ maxWidth: 980, margin: "40px auto", fontFamily: "system-ui" }}>
      <h2>KPMG AI PoC (Copilot + Agent + Analytics)</h2>

      <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8 }}>
        <h3>Copilot Chat (RAG)</h3>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            style={{ flex: 1, padding: 10 }}
            placeholder="질문을 입력하세요 (기본 doc_group=guide, 라우팅 자동)"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button
            onClick={async () => {
              const resp = await postJSON<ChatResp>("/chat", { user_id: "demo", question: q, top_k: 8 });
              setChat(resp);
            }}
          >
            Ask
          </button>
        </div>

        {chat && (
          <>
            <p><b>doc_group:</b> {chat.doc_group} / <b>trace_id:</b> {chat.trace_id}</p>
            <pre style={{ whiteSpace: "pre-wrap" }}>{chat.answer}</pre>
            <h4>근거(Citations)</h4>
            <ul>
              {chat.citations.map((c, i) => (
                <li key={i}>
                  {c.doc_title} (p.{c.page ?? "?"}) score={c.score.toFixed(3)}
                </li>
              ))}
            </ul>

            <button
              onClick={async () => {
                await postJSON("/feedback", { trace_id: chat.trace_id, user_id: "demo", rating: 1, comment: "good" });
                alert("feedback sent");
              }}
            >
              👍 Feedback
            </button>
          </>
        )}
      </section>

      <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8, marginTop: 16 }}>
        <h3>Agent: 조사 → 요약 → 보고서(JSON)</h3>
        <textarea
          style={{ width: "100%", minHeight: 90, padding: 10 }}
          placeholder="시나리오를 입력하세요"
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
        />
        <button
          onClick={async () => {
            const resp = await postJSON<any>("/report", { user_id: "demo", scenario, top_k: 10 });
            setReport(resp);
          }}
        >
          Generate Report
        </button>

        {report && (
          <>
            <p><b>doc_group:</b> {report.doc_group} / <b>trace_id:</b> {report.trace_id}</p>
            <pre style={{ whiteSpace: "pre-wrap" }}>{report.report_json}</pre>
          </>
        )}
      </section>
    </div>
  );
}
