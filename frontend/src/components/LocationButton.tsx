import LocOK from './../assets/OUI_navigas.png';
import LocNO from './../assets/NON_navigas.png';
import LocSearch from './../assets/loupe.png';

type LocationButtonProps = {
  status: "unknown" | "requesting" | "granted" | "denied";
  onRequest: () => void;
};

export default function LocationButton({ status, onRequest }: LocationButtonProps) {
  if (status === "granted") {
  return (
      <div className="location-ok">
        <img
          src={LocOK}
          alt="Localisation activée"
          className="icon-loc"
        />
        <span className='loc-desktop'>Localisé</span>
      </div>
  )}

  return (
    <>
      <button
        type="button"
        onClick={onRequest}
        disabled={status === "requesting"}
        className={`location-btn ${status}`}
      >
        {/* {status === "requesting" ? "📍 Localisation..." : "📍 Activer la localisation"} */}
        {status === "requesting" ? (
          <img src={LocSearch} className="icon-loc" alt="Localisation en cours" />
        ) : (
          <>
            <img src={LocNO} className="icon-loc" alt="Localisation" />
            <span className='loc-desktop'>Activer la localisation</span>
            <span className='loc-mobile'>Localiser</span>
          </>
        )}
      </button>

      {/* {status === "denied" && (
        <div className="location-help">
          <img
          src={LocSearch}
          alt="Cherche localisation"
          className="icon-loc-search"
        />
          Autoriser la localisation
        </div>
      )} */}
    </>
  );
}