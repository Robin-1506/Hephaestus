import { useEffect, useRef, useState } from "react";
import logo from "../assets/NaviGas.png";
import mascotte from "../assets/Navi.png";
import "./Chatbot.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/chat";

// ------------------- TYPES -------------------
type Message = {
  id: number;
  text: string;
  sender: "user" | "bot";
};

type Conversation = {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
};

// ------------------- API -------------------
async function sendMessageAPI(
  message: string,
  latitude?: number,
  longitude?: number
) {
  const payload: any = { prompt: message };
  if (latitude !== undefined) payload.latitude = latitude;
  if (longitude !== undefined) payload.longitude = longitude;

  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw new Error("API error");
  return res.json();
}

// ------------------- UTILS -------------------
function generateTitleFromMessage(message: string) {
  const carburantMatch = message.match(/Sans Plomb \d{2}/i);
  const carburant = carburantMatch ? carburantMatch[0] : "Recherche";

  const rayonMatch = message.match(/(\d+)\s?km/i);
  const rayon = rayonMatch ? rayonMatch[1] + "km" : "";

  return `${carburant}${rayon ? `, ${rayon}` : ""} de votre position`;
}

// ------------------- COMPONENT -------------------
export default function Chatbot() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const [userLocation, setUserLocation] = useState<{
    lat: number;
    lon: number;
  } | null>(null);

  const [locationStatus, setLocationStatus] = useState<
    "unknown" | "requesting" | "granted" | "denied"
  >("unknown");

  const endRef = useRef<HTMLDivElement | null>(null);

  const activeConversation = conversations.find(c => c.id === activeId);

  // ------------------- GEOLOCATION -------------------
  const requestLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus("denied");
      return;
    }

    setLocationStatus("requesting");

    navigator.geolocation.getCurrentPosition(
      position => {
        setUserLocation({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        });
        setLocationStatus("granted");
      },
      error => {
        console.error("Erreur géolocalisation :", error);
        setLocationStatus(
          error.code === error.PERMISSION_DENIED ? "denied" : "unknown"
        );
      }
    );
  };

  useEffect(() => {
    requestLocation();
  }, []);

  // ------------------- PERSISTENCE -------------------
  useEffect(() => {
    const saved = localStorage.getItem("conversations");
    if (saved) {
      const parsed: Conversation[] = JSON.parse(saved);
      if (parsed.length > 0) {
        setConversations(parsed);
        setActiveId(parsed[0].id);
        return;
      }
    }
    createConversation();
  }, []);

  useEffect(() => {
    const nonEmpty = conversations.filter(c => c.messages.length > 0);
    if (nonEmpty.length > 0) {
      localStorage.setItem("conversations", JSON.stringify(nonEmpty));
    }
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversations]);

  // ------------------- ACTIONS -------------------
  const createConversation = () => {
    const conv: Conversation = {
      id: crypto.randomUUID(),
      title: "Nouvelle conversation",
      messages: [],
      createdAt: Date.now(),
    };
    setConversations(prev => [conv, ...prev]);
    setActiveId(conv.id);
  };

  const deleteConversation = (id: string) => {
    setConversations(prev => {
      const filtered = prev.filter(c => c.id !== id);
      if (id === activeId) {
        setActiveId(filtered[0]?.id ?? null);
      }
      return filtered;
    });
  };

  // ------------------- SEND MESSAGE (FIXED) -------------------
  const sendMessage = async () => {
    if (!query.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now(),
      text: query,
      sender: "user",
    };

    let conversationId = activeId;

    if (!conversationId) {
      const newConv: Conversation = {
        id: crypto.randomUUID(),
        title: generateTitleFromMessage(query),
        messages: [userMessage],
        createdAt: Date.now(),
      };
      setConversations(prev => [newConv, ...prev]);
      setActiveId(newConv.id);
      conversationId = newConv.id;
    } else {
      setConversations(prev =>
        prev.map(c =>
          c.id === conversationId
            ? { ...c, messages: [...c.messages, userMessage] }
            : c
        )
      );
    }

    setQuery("");
    setLoading(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 2000));

      const res = await sendMessageAPI(
        userMessage.text,
        userLocation?.lat,
        userLocation?.lon
      );

      const botMessage: Message = {
        id: Date.now() + 1,
        text: res.response,
        sender: "bot",
      };

      setConversations(prev =>
        prev.map(c =>
          c.id === conversationId
            ? { ...c, messages: [...c.messages, botMessage] }
            : c
        )
      );
    } catch {
      setConversations(prev =>
        prev.map(c =>
          c.id === conversationId
            ? {
                ...c,
                messages: [
                  ...c.messages,
                  {
                    id: Date.now() + 1,
                    text: "Oups 😕 Une erreur est survenue.",
                    sender: "bot",
                  },
                ],
              }
            : c
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const [sidebarOpen, setSidebarOpen] = useState(false);

  // ------------------- RENDER -------------------
  return (
    <div className="chat-layout">
      {/* SIDEBAR */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <img
          src={logo}
          alt="NaviGas"
          className="sidebar-logo"
          onClick={() => (document.location.href = "/")}
        />

        <button className="new-chat" onClick={createConversation}>
          + Nouvelle conversation
        </button>

        <div className="conversation-list">
          {conversations.map(c => (
            <div
              key={c.id}
              className={`conversation-item ${
                c.id === activeId ? "active" : ""
              }`}
            >
              <span
                className="conversation-title"
                onClick={() => setActiveId(c.id)}
              >
                {c.title}
              </span>

              <button
                className="delete-btn"
                onClick={() => deleteConversation(c.id)}
              >
                🗑
              </button>
            </div>
          ))}
        </div>
      </aside>

      {sidebarOpen && <div className="overlay" onClick={() => setSidebarOpen(false)} />}

      {/* CHAT */}
      <main className="chat">
        <button
  className="sidebar-toggle"
  onClick={() => setSidebarOpen(true)}
>
  ☰
</button>
        <div className="messages">
          {(!activeConversation ||
            activeConversation.messages.length === 0) && (
            <div className="empty">
              <img src={mascotte} alt="Navi" />
              <p>
                "Aide-moi à trouver du Sans Plomb 95 dans un rayon de 5km."
              </p>
            </div>
          )}

          {activeConversation?.messages.map(m => (
            <div key={m.id} className={`message ${m.sender}`}>
              {m.sender === "bot" && <img src={mascotte} alt="bot" />}
              <div className="bubble">{m.text}</div>
            </div>
          ))}

          {loading && (
            <div className="message bot">
              <img src={mascotte} alt="bot" />
              <div className="bubble typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>

        <form
          className="input-bar"
          onSubmit={e => {
            e.preventDefault();
            sendMessage();
          }}
        >
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Ex : stations à moins de 5km..."
          />

          {locationStatus !== "granted" ? (
            <button
              type="button"
              onClick={requestLocation}
              disabled={locationStatus === "requesting"}
              className={`location-btn ${locationStatus}`}
            >
              {locationStatus === "requesting"
                ? "📍 Localisation..."
                : "📍 Activer la localisation"}
            </button>
          ) : (
            <div className="location-ok">✓ Localisé</div>
          )}

          {locationStatus === "denied" && (
            <div className="location-help">
              📍 Autorisez la localisation dans votre navigateur
            </div>
          )}

          <button disabled={!query.trim() || loading}>➤</button>
        </form>
      </main>
    </div>
  );
}
