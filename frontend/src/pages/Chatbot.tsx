import { useEffect, useRef, useState } from "react";
import logo from "../assets/NaviGas.png";
import mascotte from "../assets/Navi.png";
import "./Chatbot.css";
import { useNavigate } from "react-router";

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

// ------------------- UTILITAIRES -------------------
async function sendMessageAPI(message: string, latitude?: number, longitude?: number) {
  const payload: any = {
    prompt: message,
  };

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

function generateTitleFromMessage(message: string) {
  const carburantMatch = message.match(/Sans Plomb \d{2}/i);
  const carburant = carburantMatch ? carburantMatch[0] : "Recherche";

  const rayonMatch = message.match(/(\d+)\s?km/i);
  const rayon = rayonMatch ? rayonMatch[1] + "km" : "";

  const position = "'votre position'";

  return `${carburant}${rayon ? `, ${rayon}` : ""} de ${position}`;
}

// ------------------- COMPONENT -------------------
export default function Chatbot() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [userLocation, setUserLocation] = useState<{lat: number, lon: number} | null>(null);
  const [locationStatus, setLocationStatus] = useState<'unknown' | 'requesting' | 'granted' | 'denied'>('unknown');
  const endRef = useRef<HTMLDivElement | null>(null);

  const activeConversation = conversations.find(c => c.id === activeId);

  // Fonction pour demander la géolocalisation
  const requestLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus('denied');
      return;
    }

    setLocationStatus('requesting');
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          lat: position.coords.latitude,
          lon: position.coords.longitude
        });
        setLocationStatus('granted');
      },
      (error) => {
        console.log('Géolocalisation refusée ou indisponible:', error);
        setLocationStatus('denied');
      }
    );
  };

  // Récupérer la géolocalisation au démarrage
  useEffect(() => {
    requestLocation();
  }, []);

  // ------------------- PERSISTENCE -------------------
  useEffect(() => {
  const saved = localStorage.getItem("conversations");
  if (saved) {
    const parsed: Conversation[] = JSON.parse(saved);
    if (parsed.length > 0) {
      // On récupère l'historique et on définit la conversation active
      setConversations(parsed);
      setActiveId(parsed[0].id);
    } else {
      // Cas rare : localStorage vide → créer une nouvelle conversation
      createConversation();
    }
  } else {
    // Pas de données → créer une conversation par défaut
    createConversation();
  }
}, []);

useEffect(() => {
  // Ne sauvegarde que les conversations qui ont au moins un message
  const nonEmptyConversations = conversations.filter(c => c.messages.length > 0);

  if (nonEmptyConversations.length > 0) {
    localStorage.setItem("conversations", JSON.stringify(nonEmptyConversations));
  }

  endRef.current?.scrollIntoView({ behavior: "smooth" });
}, [conversations]);

  // ------------------- ACTIONS -------------------
  const createConversation = () => {
    const newConv: Conversation = {
      id: crypto.randomUUID(),
      title: "Nouvelle conversation",
      messages: [],
      createdAt: Date.now(),
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveId(newConv.id);
  };

  const sendMessage = async () => {
  if (!query.trim()) return;

  const userMessage: Message = {
    id: Date.now(),
    text: query,
    sender: "user",
  };

  let conv = activeConversation;

  // Si aucune conversation n'existe, on la crée avec le message utilisateur
    if (!conv) {
      const newConv: Conversation = {
        id: crypto.randomUUID(),
        title: generateTitleFromMessage(query),
        messages: [userMessage],
        createdAt: Date.now(),
      };
      setConversations(prev => [newConv, ...prev]);
      setActiveId(newConv.id);
      conv = newConv;
    } else {
      // Ajoute le message à la conversation existante
      setConversations(prev =>
        prev.map(c =>
          c.id === conv!.id ? { ...c, messages: [...c.messages, userMessage] } : c
        )
      );
    }

  setQuery("");
  setLoading(true);

//   try {
//     const res = await sendMessageAPI(query);
//     const botMessage: Message = {
//       id: Date.now() + 1,
//       text: res.response,
//       sender: "bot",
//     };

//     // Ajoute la réponse du bot au dernier state (pas de duplication du message utilisateur)
//     setConversations(prev =>
//       prev.map(c =>
//         c.id === conv!.id ? { ...c, messages: [...c.messages, botMessage] } : c
//       )
//     );
//   } catch {
//     const errorMessage: Message = {
//       id: Date.now() + 1,
//       text: "Oups 😕 Une erreur est survenue.",
//       sender: "bot",
//     };

//     setConversations(prev =>
//       prev.map(c =>
//         c.id === conv!.id ? { ...c, messages: [...c.messages, errorMessage] } : c
//       )
//     );
//   } finally {
//     setLoading(false);
//   }
try {
  // Simule un délai de réflexion de 2 secondes
  await new Promise(resolve => setTimeout(resolve, 2000));

  const res = await sendMessageAPI(query, userLocation?.lat, userLocation?.lon);
  const botMessage: Message = {
    id: Date.now() + 1,
    text: res.response,
    sender: "bot",
  };

  setConversations(prev =>
    prev.map(c =>
      c.id === conv!.id ? { ...c, messages: [...c.messages, botMessage] } : c
    )
  );
} catch {
  const errorMessage: Message = {
    id: Date.now() + 1,
    text: "Oups 😕 Une erreur est survenue.",
    sender: "bot",
  };

  setConversations(prev =>
    prev.map(c =>
      c.id === conv!.id ? { ...c, messages: [...c.messages, errorMessage] } : c
    )
  );
} finally {
  setLoading(false);
}

};

const deleteConversation = (id: string) => {
  setConversations(prev => {
    const filtered = prev.filter(c => c.id !== id);

    // Si on supprime la conversation active, on change activeId
    if (id === activeId) {
      setActiveId(filtered[0]?.id ?? null);
    }

    return filtered;
  });
};


  // ------------------- RENDER -------------------
  return (
    <div className="chat-layout">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <img
          src={logo}
          alt="NaviGas"
          className="sidebar-logo"
          onClick={() => navigate("/")}
        />

        <button className="new-chat" onClick={createConversation}>
          + Nouvelle conversation
        </button>

        <div className="conversation-list">
  {conversations.map(c => (
    <div
      key={c.id}
      className={`conversation-item ${c.id === activeId ? "active" : ""}`}
      title={c.title}
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
        title="Supprimer"
      >
        🗑
      </button>
    </div>
  ))}
</div>
      </aside>

      {/* CHAT */}
      <main className="chat">
        <div className="messages">
          {(!activeConversation || activeConversation.messages.length === 0) && (
            <div className="empty">
              <img src={mascotte} alt="Navi" />
              <p>"Aide-moi à trouver du Sans Plomb 95 dans un rayon de 5km."</p>
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
          {locationStatus !== 'granted' && (
            <button
              type="button"
              onClick={requestLocation}
              style={{
                padding: '8px 12px',
                backgroundColor: '#ff6b35',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
                whiteSpace: 'nowrap'
              }}
            >
              📍 Localisation
            </button>
          )}
          {locationStatus === 'granted' && (
            <div style={{
              padding: '8px 12px',
              backgroundColor: '#4caf50',
              color: 'white',
              borderRadius: '4px',
              fontSize: '12px',
              whiteSpace: 'nowrap'
            }}>
              ✓ Localisé
            </div>
          )}
          <button disabled={!query.trim()}>➤</button>
        </form>
      </main>
    </div>
  );
}
