import React, { useState, useRef, useEffect } from 'react'

import './Home.css'

type Message = { id: number; text: string; sender: 'user' | 'bot' }

function Home() {
    const [query, setQuery] = useState('')

    const [messages, setMessages] = useState<Message[]>([])

    const endRef = useRef<HTMLDivElement | null>(null)

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()

        const text = query.trim()
        if (!text) return

        const userMessage: Message = { id: Date.now(), text, sender: 'user'}
        setMessages((prevMessages) => [...prevMessages, userMessage])
        setQuery('')

        setTimeout(() => {
            const botMessage: Message = { id:Date.now() + 1, text: 'message envoyé', sender: 'bot' }
            setMessages((prevMessages) => [...prevMessages, botMessage])
        }, 300)
    }

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    return (
        <div className="container">
            <header className='header'>
                <h1>Find your fuel</h1>
            </header>

            <main className='main'>
                <div className="messages">
                    {messages.length === 0 ? (
                        <div className="empty">Aucun message — envoie le premier message.</div>
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