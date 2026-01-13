// src/pages/Chatbot.jsx
import React, { useEffect, useRef, useState } from "react";
import logo from "../assets/NaviGas.png";
import mascotte from "../assets/Navi.png";
import "./Chatbot.css";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/chat";

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

async function sendMessageAPI(message: string) {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: message }),
  });

  if (!res.ok) throw new Error("API error");
  return res.json();
}

function generateTitle(text: string): string {
  return text
    .replace(/[?.!]/g, "")
    .slice(0, 40)
    .trim() + (text.length > 40 ? "…" : "");
}


export default function Chatbot() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement | null>(null);

  const navigate = useNavigate();

  /* =====================
     INIT + PERSISTENCE
  ====================== */

  useEffect(() => {
  const saved = localStorage.getItem("conversations");
  if (saved) {
    const parsed = JSON.parse(saved);
    setConversations(parsed);
    setActiveId(parsed[0]?.id ?? null);
  } else {
    // Crée une conversation par défaut si aucune sauvegarde
    createConversation();
  }
}, []);


  useEffect(() => {
    localStorage.setItem("conversations", JSON.stringify(conversations));
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversations, activeId]);

  const activeConversation = conversations.find(c => c.id === activeId);

  /* =====================
     ACTIONS
  ====================== */

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

  let conv = activeConversation;

  // Si aucune conversation n'est active, on en crée une nouvelle
  if (!conv) {
    conv = {
      id: crypto.randomUUID(),
      title: "Nouvelle conversation",
      messages: [],
      createdAt: Date.now(),
    };
    setActiveId(conv.id);
    // On met à jour les conversations directement avec cette nouvelle conversation
    setConversations(prev => [conv, ...prev]);
  }

  // Crée le message utilisateur
  const userMessage: Message = {
    id: Date.now(),
    text: query,
    sender: "user",
  };

  // Ajoute le message à la conversation
  const updatedMessages = [...conv.messages, userMessage];

  // Met à jour la conversation dans le state
  setConversations(prev =>
    prev.map(c =>
      c.id === conv!.id ? { ...c, messages: updatedMessages } : c
    )
  );

  setQuery("");
  setLoading(true);

  try {
    const res = await sendMessageAPI(query);
    const botMessage: Message = {
      id: Date.now() + 1,
      text: res.response,
      sender: "bot",
    };

    const finalMessages = [...updatedMessages, botMessage];

    setConversations(prev =>
      prev.map(c =>
        c.id === conv!.id ? { ...c, messages: finalMessages } : c
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
        c.id === conv!.id
          ? { ...c, messages: [...updatedMessages, errorMessage] }
          : c
      )
    );
  } finally {
    setLoading(false);
  }
};



  const updateConversation = (messages: Message[], updateTitle = false) => {
    setConversations(prev =>
      prev.map(c =>
        c.id === activeId
          ? {
              ...c,
              messages,
              title:
                updateTitle && c.messages.length === 0
                    ? generateTitle(messages[0].text)
                    : c.title,

            }
          : c
      )
    );
  };

  /* =====================
     RENDER
  ====================== */

  return (
    <div className="chat-layout">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <img src={logo} alt="NaviGas" className="sidebar-logo" onClick={() => navigate("/")} />

        <button className="new-chat" onClick={createConversation}>
          + Nouvelle conversation
        </button>

        <div className="conversation-list">
          {conversations.map(c => (
            <div
              key={c.id}
              className={`conversation-item ${c.id === activeId ? "active" : ""}`}
              onClick={() => setActiveId(c.id)}
              title={c.title}
            >
              {c.title}
            </div>
          ))}
        </div>
      </aside>

      {/* CHAT */}
      <main className="chat">
        <div className="messages">
          {activeConversation?.messages.length === 0 && (
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
                <span></span><span></span><span></span>
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>

        <form
          className="input-bar"
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage();
          }}
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ex : stations à moins de 5km..."
          />
          <button disabled={!query.trim()}>➤</button>
        </form>
      </main>
    </div>
  );
}
