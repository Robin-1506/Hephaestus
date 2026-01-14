// ------------------- UTILS -------------------
export function generateTitleFromMessage(message: string): string {
  const carburantMatch = message.match(/Sans Plomb \d{2}/i);
  const carburant = carburantMatch ? carburantMatch[0] : "Recherche";

  const rayonMatch = message.match(/(\d+)\s?km/i);
  const rayon = rayonMatch ? rayonMatch[1] + "km" : "";

  return `${carburant}${rayon ? `, ${rayon}` : ""} de votre position`;
}