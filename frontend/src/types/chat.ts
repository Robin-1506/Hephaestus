// ------------------- TYPES -------------------
export type Message = {
  id: number;
  text: string;
  sender: "user" | "bot";
};

export type Conversation = {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
};