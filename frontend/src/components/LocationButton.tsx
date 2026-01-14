type LocationButtonProps = {
  status: "unknown" | "requesting" | "granted" | "denied";
  onRequest: () => void;
};

export default function LocationButton({ status, onRequest }: LocationButtonProps) {
  if (status === "granted") {
    return <div className="location-ok">✓ Localisé</div>;
  }

  return (
    <>
      <button
        type="button"
        onClick={onRequest}
        disabled={status === "requesting"}
        className={`location-btn ${status}`}
      >
        {status === "requesting" ? "📍 Localisation..." : "📍 Activer la localisation"}
      </button>

      {status === "denied" && (
        <div className="location-help">
          📍 Autorisez la localisation dans votre navigateur
        </div>
      )}
    </>
  );
}