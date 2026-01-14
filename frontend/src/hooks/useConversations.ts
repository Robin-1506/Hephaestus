import { useEffect, useState } from "react";
import type { Conversation, Message } from "../types/chat";

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);

  const activeConversation = conversations.find(c => c.id === activeId);

  // -------- INIT (localStorage) --------
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // -------- PERSISTENCE --------
  useEffect(() => {
    const nonEmpty = conversations.filter(c => c.messages.length > 0);
    if (nonEmpty.length > 0) {
      localStorage.setItem("conversations", JSON.stringify(nonEmpty));
    }
  }, [conversations]);

  // -------- ACTIONS --------
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

  const addMessage = (conversationId: string, message: Message) => {
    setConversations(prev =>
      prev.map(c =>
        c.id === conversationId
          ? { ...c, messages: [...c.messages, message] }
          : c
      )
    );
  };

  return {
    conversations,
    activeId,
    activeConversation,
    setActiveId,
    createConversation,
    deleteConversation,
    addMessage,
  };
}
