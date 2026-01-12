import React, { useState } from 'react'

import './Home.css'

function Home() {
    const [query, setQuery] = useState('')

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        console.log('Recherche envoyée :', query)
        // TODO: remplacer par appel API / navigation
        setQuery('')
    }

    return (
        <div className="container">
            <header className='header'>
                <h1>Find your fuel</h1>
            </header>

            <main className='main'>
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