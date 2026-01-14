import { useRef, useState } from "react";

import mascotte from "../assets/Navi.png";

import "./Chatbot.css";

import type { Message } from "../types/chat";
import { sendMessageAPI } from "../api/chatApi";
import ChatSidebar from "../components/ChatSidebar";
import { useConversations } from "../hooks/useConversations";
import { useGeolocation } from "../hooks/useGeolocation";





// ------------------- COMPONENT -------------------
export default function Chatbot() {
  const {
    conversations,
    activeId,
    activeConversation,
    setActiveId,
    createConversation,
    deleteConversation,
    addMessage,
  } = useConversations();

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  // const [userLocation, setUserLocation] = useState<{
  //   lat: number;
  //   lon: number;
  // } | null>(null);

  // const [locationStatus, setLocationStatus] = useState<
  //   "unknown" | "requesting" | "granted" | "denied"
  // >("unknown");

  const endRef = useRef<HTMLDivElement | null>(null);

  // ------------------- GEOLOCATION -------------------
  // const requestLocation = () => {
  //   if (!navigator.geolocation) {
  //     setLocationStatus("denied");
  //     return;
  //   }

  //   setLocationStatus("requesting");

  //   navigator.geolocation.getCurrentPosition(
  //     position => {
  //       setUserLocation({
  //         lat: position.coords.latitude,
  //         lon: position.coords.longitude,
  //       });
  //       setLocationStatus("granted");
  //     },
  //     error => {
  //       console.error("Erreur géolocalisation :", error);
  //       setLocationStatus(
  //         error.code === error.PERMISSION_DENIED ? "denied" : "unknown"
  //       );
  //     }
  //   );
  // };

  // useEffect(() => {
  //   requestLocation();
  // }, []);

  const { location: userLocation, status: locationStatus, requestLocation } = useGeolocation();

  const sendMessage = async () => {
  if (!query.trim() || loading || !activeId) return;

  const userMessage: Message = {
    id: Date.now(),
    text: query,
    sender: "user",
  };

  addMessage(activeId, userMessage);

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

    addMessage(activeId, botMessage);
  } catch {
    addMessage(activeId, {
      id: Date.now() + 1,
      text: "Oups 😕 Une erreur est survenue.",
      sender: "bot",
    });
  } finally {
    setLoading(false);
  }
};


  const [sidebarOpen, setSidebarOpen] = useState(false);

  // ------------------- RENDER -------------------
  return (
    <div className="chat-layout">
      {/* SIDEBAR */}
      <ChatSidebar
        conversations={conversations}
        activeId={activeId}
        open={sidebarOpen}
        onCreateConversation={createConversation}
        onSelectConversation={setActiveId}
        onDeleteConversation={deleteConversation}
        onClose={() => setSidebarOpen(false)}
      />

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
