import { useEffect, useState } from "react";
import api from "./api";
import "./App.css";

function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [tekst, setTekst] = useState("");
  const [tasks, setTasks] = useState([]);
  const [token, setToken] = useState(localStorage.getItem("token") || "");

  const fetchTasks = async () => {
    try {
      const res = await api.get("/tasks", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setTasks(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const register = async () => {
    try {
      await api.post("/register", { username, password });
      alert("Zarejestrowano");
    } catch (err) {
      console.error("REGISTER ERROR:", err);
      alert("Błąd rejestracji");
    }
  };

  const login = async () => {
    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await api.post("/token", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      localStorage.setItem("token", res.data.access_token);
      setToken(res.data.access_token);
      alert("Zalogowano");
    } catch (err) {
      console.error("LOGIN ERROR:", err);
      alert("Błąd logowania");
    }
  };

  const addTask = async () => {
    try {
      await api.post(
        "/tasks",
        { tekst },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setTekst("");
      fetchTasks();
    } catch (err) {
      console.error("ADD TASK ERROR:", err);
      alert("Błąd dodawania");
    }
  };

  const deleteTask = async (taskId) => {
    try {
      await api.delete(`/tasks/${taskId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      fetchTasks();
    } catch (err) {
      console.error("DELETE ERROR:", err);
      alert("Błąd usuwania taska");
    }
  };

  const markDone = async (taskId) => {
    try {
      await api.put(
        `/tasks/${taskId}`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      fetchTasks();
    } catch (err) {
      console.error("MARK DONE ERROR:", err);
      alert("Błąd oznaczania taska");
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken("");
    setTasks([]);
    alert("Wylogowano");
  };

  useEffect(() => {
    if (token) fetchTasks();
  }, [token]);

  return (
    <div className="app">
      <div className="card">
        <h1>Todo App</h1>

        <section className="section">
          <h2>Auth</h2>
          <div className="form">
            <input
              placeholder="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <input
              placeholder="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <div className="button-row">
              <button className="btn btn-secondary" onClick={register}>
                Register
              </button>
              <button className="btn btn-primary" onClick={login}>
                Login
              </button>
              <button className="btn btn-ghost" onClick={logout}>
                Logout
              </button>
            </div>
          </div>
        </section>

        <section className="section">
          <h2>Nowe zadanie</h2>
          <div className="task-form">
            <input
              placeholder="treść zadania"
              value={tekst}
              onChange={(e) => setTekst(e.target.value)}
            />
            <button className="btn btn-primary" onClick={addTask}>
              Dodaj
            </button>
          </div>
        </section>

        <section className="section">
          <h2>Taski</h2>

          {tasks.length === 0 ? (
            <p className="empty">Brak zadań</p>
          ) : (
            <ul className="task-list">
              {tasks.map((t) => (
                <li key={t.id} className="task-item">
                  <div className="task-left">
                    <span className={`status ${t.zrobione ? "done" : "open"}`}>
                      {t.zrobione ? "✅" : "⏳"}
                    </span>
                    <span className={t.zrobione ? "task-text done-text" : "task-text"}>
                      {t.tekst}
                    </span>
                  </div>

                  <div className="task-actions">
                    {!t.zrobione && (
                      <button
                        className="btn btn-success"
                        onClick={() => markDone(t.id)}
                      >
                        Zrobione
                      </button>
                    )}

                    <button
                      className="btn btn-danger"
                      onClick={() => deleteTask(t.id)}
                    >
                      Usuń
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

export default App;