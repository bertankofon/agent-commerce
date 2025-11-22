import express from "express";
import cors from "cors";
import { spawn } from "child_process";

const app = express();
app.use(cors());
app.use(express.json());

app.post("/deploy-agent", (req, res) => {
    const { agentType, config } = req.body;

    const py = spawn("python3", [
        "agents/run_agent.py",
        agentType,
        JSON.stringify(config)
    ]);

    py.stdout.on("data", (data) => {
        res.json(JSON.parse(data.toString()));
    });
});

app.listen(3001, () => console.log("Backend running on :3001"));
