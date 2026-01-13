// src/pages/Home.jsx
import { useNavigate } from "react-router-dom";
import "./Home.css";

import mascotte from '../assets/Navi.png';

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="homepage">
      <section className="hero">
        <div className="hero-content">
          <h1>Trouvez une station d’essence autour de vous, instantanément</h1>
          <p>
            Avec NaviGas, demandez à Navi quelles stations services se trouvent le plus proche de vous !
          </p>
          <p>
            Rien de plus simple : indiquez votre position et le rayon de recherche, et laissez le chatbot faire le reste.
          </p>
          <button onClick={() => navigate("/chatbot")}>
            Découvrir le chatbot
          </button>
        </div>

        <div className="hero-image">
          <div className="image-placeholder">
            <img src={mascotte} alt="Navi" className='mascotte' />
          </div>
        </div>
      </section>

      <section className="features">
        <h2>Pourquoi utiliser notre chatbot ?</h2>

        <div className="feature-grid">
          <div className="feature-card">
            <h3>Localisation précise</h3>
            <p>
              Dîtes lui où vous voulez effectuer votre recherche, soit à votre emplacement actuel, soit à une adresse spécifique.
            </p>
          </div>

          <div className="feature-card">
            <h3>Rayon personnalisable</h3>
            <p>
              Dîtes à Navi dans quel rayon vous souhaitez trouver des stations services, de 1 à 30 km.
            </p>
          </div>

          <div className="feature-card">
            <h3>Interaction simple</h3>
            <p>
              Une discussion fluide et intuitive.
            </p>
            <p>
              "Aide-moi à trouver du Sans Plomb 95 dans un rayon de 5km autour de moi."
            </p>
          </div>
        </div>
      </section>

      <section className="how-it-works">
        <h2>Comment ça marche ?</h2>

        <div className="steps">
          <div className="step">
            <span>1</span>
            <p>Ouvrez le chatbot.</p>
          </div>

          <div className="step">
            <span>2</span>
            <p>Indiquez votre position et le rayon de recherche.</p>
          </div>

          <div className="step">
            <span>3</span>
            <p>Laissez Navi faire le reste. Vous n'avez plus qu'à choisir la station qui vous convient.</p>
          </div>
        </div>
      </section>

      <section className="cta">
        <h2>Prêt à trouver une station près de vous ?</h2>
        <button onClick={() => navigate("/chatbot")}>
          Tester le chatbot
        </button>
      </section>
    </div>
  );
}
