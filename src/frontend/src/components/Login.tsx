import React, { useState } from "react";
import { useAuth } from "../AuthContext";

const Login: React.FC = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const { login } = useAuth();
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("http://localhost:8001/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username, password }),
      });
      if (!res.ok) throw new Error("Login failed");
      const data = await res.json();
      login(data.access_token);
    } catch (err) {
      setError("Invalid credentials");
    }
  };

  return (
    <div className="card" style={{ maxWidth: 400, margin: "2rem auto", padding: "2rem" }}>
      <h2>Login</h2>
      {error && <div style={{ color: "red", marginBottom: "1rem" }}>{error}</div>}
      <form onSubmit={handleLogin}>
        <div style={{ marginBottom: "1rem" }}>
          <label>Username</label><br />
          <input value={username} onChange={e => setUsername(e.target.value)} required style={{ width: "100%", padding: "0.5rem" }} />
        </div>
        <div style={{ marginBottom: "1rem" }}>
          <label>Password</label><br />
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={{ width: "100%", padding: "0.5rem" }} />
        </div>
        <button type="submit" style={{ width: "100%", padding: "0.75rem" }}>Login</button>
      </form>
    </div>
  );
};

export default Login;

