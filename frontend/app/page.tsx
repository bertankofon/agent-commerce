"use client";
import { useState } from "react";

export default function DeployPage() {
  const [type, setType] = useState("seller");
  const [name, setName] = useState("");

  async function deploy() {
    const res = await fetch("http://localhost:3001/deploy-agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agentType: type,
        config: { name, domain: `${name}.agent.com` }
      })
    });

    const data = await res.json();
    alert("Deployed agent ID: " + data.agent_id);
  }

  return (
    <div style={{ padding: 40 }}>
      <h1>Deploy Agent</h1>

      <select value={type} onChange={(e) => setType(e.target.value)}>
        <option value="seller">Seller</option>
        <option value="buyer">Buyer</option>
      </select>

      <br /><br />

      <input
        placeholder="Agent Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />

      <br /><br />

      <button onClick={deploy}>
        Deploy
      </button>
    </div>
  );
}
