import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home.tsx";
import Chatbot from "./pages/Chatbot.tsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/chatbot" element={<Chatbot />} />
    </Routes>
  );
}
