# Immich Kiosk Gallery

Jednoduchý addon pre Home Assistant, ktorý sa pripája na Immich server cez API a zobrazuje fotografie v slideshow režime.

## Funkcie

- 🖼️ Slideshow fotográfií z Immich servera
- 🎯 Podpora pre albumy a spomienky
- 🌐 Webové rozhranie prístupné na porte 8456
- ⚙️ Konfigurácia cez Home Assistant UI
- 🔄 Automatické obnovenie obsahu

## Konfigurácia

### Povinné nastavenia

- **immich_url**: URL adresa vášho Immich servera (napríklad: `http://192.168.1.100:2283`)
- **immich_api_key**: API kľúč pre prístup k Immich serveru

### Voliteľné nastavenia

- **immich_show_memories**: Zobrazovať spomienky (predvolené: `true`)
- **immich_show_albums**: Zobrazovať albumy (predvolené: `true`)  
- **immich_albums**: Zoznam konkrétnych albumov na zobrazenie (predvolené: všetky)
- **log_level**: Úroveň logovania (predvolené: `info`)

### Príklad konfigurácie

```yaml
immich_url: "http://192.168.1.100:2283"
immich_api_key: "your-api-key-here"
immich_show_memories: true
immich_show_albums: true
immich_albums: 
  - "Vacation 2024"
  - "Family Photos"
log_level: info
```

## Použitie

1. Nainštalujte addon v Home Assistant
2. Nastavte konfiguráciu (minimálne `immich_url` a `immich_api_key`)
3. Spustite addon
4. Otvorte webové rozhraní na `http://homeassistant:8456`

## Získanie API kľúča

1. Prihláste sa do svojho Immich servera
2. Choďte do Settings → API Keys
3. Vytvorte nový API kľúč
4. Skopírujte kľúč a vložte ho do konfigurácie addon-u

## Riešenie problémov

### Addon sa nespustí
- Skontrolujte, či je Immich server dostupný
- Overte správnosť URL adresy a API kľúča
- Pozrite si logy addon-u v Home Assistant

### Žiadne fotografie sa nezobrazujú
- Skontrolujte, či máte fotografie v Immich serveri
- Overte nastavenia albumov a spomienok
- Skontrolujte, či API kľúč má potrebné oprávnenia

## License
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.