import { createContext, useState, useContext, ReactNode } from "react";

export const AuthContext = createContext<any>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));
  const [incidentId, setIncidentId] = useState<string | null>(localStorage.getItem("incident_id"));

  const login = (newToken: string) => {
    localStorage.setItem("token", newToken);
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("incident_id");
    setToken(null);
    setIncidentId(null);
  };

  const selectIncident = (id: string) => {
    localStorage.setItem("incident_id", id);
    setIncidentId(id);
  };

  return (
    <AuthContext.Provider value={{ token, incidentId, login, logout, selectIncident }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

