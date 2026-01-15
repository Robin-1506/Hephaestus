import { useState, useEffect } from "react";

type Location = { lat: number; lon: number };

export function useGeolocation() {
  const [location, setLocation] = useState<Location | null>(null);
  const [status, setStatus] = useState<"unknown" | "requesting" | "granted" | "denied">("unknown");

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setStatus("denied");
      return;
    }

    setStatus("requesting");

    navigator.geolocation.getCurrentPosition(
      position => {
        setLocation({ lat: position.coords.latitude, lon: position.coords.longitude });
        setStatus("granted");
      },
      error => {
        console.error("Erreur géolocalisation :", error);
        setStatus(error.code === error.PERMISSION_DENIED ? "denied" : "unknown");
      }
    );
  };

  useEffect(() => {
    requestLocation();
  }, []);

  return { location, status, requestLocation };
}
