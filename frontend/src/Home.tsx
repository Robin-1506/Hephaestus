import React, { useState, useRef, useEffect } from 'react'

import logo from './assets/NaviGas.png'

import './Home.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/chat'
type Message = { id: number; text: string; sender: 'user' | 'bot' }

async function sendMessage(message:string) {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: message,
      }),
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Erreur lors de la requête POST:', error);
    throw error;
  }
}

function Home() {
    const [query, setQuery] = useState('')

    const [messages, setMessages] = useState<Message[]>([])

    const endRef = useRef<HTMLDivElement | null>(null)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        const text = query.trim()
        if (!text) return

        const userMessage: Message = { id: Date.now(), text, sender: 'user'}
        setMessages((prevMessages) => [...prevMessages, userMessage])
        setQuery('')

        try {
            const response = await sendMessage(text)
            const botMessage: Message = { id: Date.now() + 1, text: response.response, sender: 'bot' }
            setMessages((prevMessages) => [...prevMessages, botMessage])
        } catch (error) {
            const errorMessage: Message = { id: Date.now() + 1, text: "Erreur lors de la communication avec le serveur", sender: 'bot' }
            setMessages((prevMessages) => [...prevMessages, errorMessage])
        }
    }

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    return (
        <div className="container">
            <header className='header'>
                <img src={logo} alt="NaviGas" className='logo' />
            </header>

            <main className='main'>
                <div className="messages">
                    {messages.length === 0 ? (
                        <div className="empty">
                            <img src={logo} alt="NaviGas" className='logo' />
                            <p>"Aide-moi à trouver du Sans Plomb 95 dans un rayon de 5km autour de moi."</p>
                        </div>
                    ) : (
                        messages.map(m => (
                            <div
                                key={m.id}
                                className={`message ${m.sender === 'user' ? 'user' : 'bot'}`}
                            >
                                {m.text}
                            </div>
                        ))
                    )}
                    <div ref={endRef} />
                </div>

                <form 
                    className='chatbotForm'
                    onSubmit={handleSubmit}
                >
                    <input
                        type="text"
                        className='searchInput'
                        placeholder="Tapez votre recherche..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <button
                        type="submit"
                        className="searchButton"
                        aria-label="Rechercher"
                        title="Rechercher"
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                            <path d="M12 19V6"></path>
                            <polyline points="5 12 12 5 19 12"></polyline>
                        </svg>
                    </button>
                </form>
            </main>
        </div>
    )
}

export default Home