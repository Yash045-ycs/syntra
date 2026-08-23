import { useState } from "react";
import { checkBackendHealth } from "./services/api";

function App() {
  const [backendStatus, setBackendStatus] = useState("Not connected");

  const handleCheckBackend = async () => {
    try {
      const data = await checkBackendHealth();

      setBackendStatus(data.status);
    } catch (error) {
      console.error(error);

      setBackendStatus("Backend connection failed");
    }
  };

  return (
    <div style={{ padding: "40px" }}>
      <h1>Syntra</h1>

      <p>Autonomous AI Engineering Agent</p>

      <br />

      <button onClick={handleCheckBackend}>
        Check Backend
      </button>

      <p style={{ marginTop: "20px" }}>
        Backend Status: {backendStatus}
      </p>
    </div>
  );
}

export default App;