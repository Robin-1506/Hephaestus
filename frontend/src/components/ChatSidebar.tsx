import logo from "../assets/blanc_navigas.svg"

import type { Conversation } from "../types/chat";

type Props = {
  conversations: Conversation[];
  activeId: string | null;
  open: boolean;
  onSelectConversation: (id: string) => void;
  onCreateConversation: () => void;
  onDeleteConversation: (id: string) => void;
  onClose: () => void;
};

export default function ChatSidebar({
  conversations,
  activeId,
  open,
  onSelectConversation,
  onCreateConversation,
  onDeleteConversation,
  onClose,
}: Props) {
  return (
    <>
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <img
          src={logo}
          alt="NaviGas"
          className="sidebar-logo"
          onClick={() => (document.location.href = "/")}
        />

        <button className="new-chat" onClick={onCreateConversation}>
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
                onClick={() => {
                  onSelectConversation(c.id);
                  onClose();
                }}
              >
                {c.title}
              </span>

              <button
                className="delete-btn"
                onClick={() => onDeleteConversation(c.id)}
              >
                🗑
              </button>
            </div>
          ))}
        </div>
      </aside>

      {open && <div className="overlay" onClick={onClose} />}
    </>
  );
}