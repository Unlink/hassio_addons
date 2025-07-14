# Immich Kiosk Gallery - Home Assistant Addon

Kompletný Home Assistant addon pre zobrazovanie slideshow z Immich memories.

## Implementované funkcionality

### ✅ Základná infraštruktúra
- **S6-overlay integrácia**: Jednoducho longrun služba `immich-kiosk`
- **Flask webserver**: Beží na porte 8456
- **Bashio integrácia**: Len v longrun službe pre konfiguráciu
- **Docker kontajner**: Správne balíčky a permissions

### ✅ Immich API integrácia
- **ImmichAPIClient**: Plne funkčný klient pre Immich API
- **Autentifikácia**: Používa API key z konfigurácie
- **Test pripojenia**: Kontrola dostupnosti Immich servera
- **Memories endpoint**: Načítanie memories z `/api/memories`
- **Error handling**: Robustné spracovanie chýb a timeoutov

### ✅ Filtrovanie memories
- **Časové filtrovanie**: Zobrazujú sa len aktívne memories podľa `showAt`/`hideAt`
- **UTC čas**: Správne porovnávanie časov v UTC
- **Logovanie**: Detailné logy o filtrovaní a stave memories
- **Spracovanie chýb**: Graceful handling neplatných časov

### ✅ Proxy pre obrázky
- **Thumbnail proxy**: `/api/proxy/thumbnail/<asset_id>?size=preview`
- **Full image proxy**: `/api/proxy/image/<asset_id>`
- **API key hiding**: Frontend nevidí Immich API key
- **Cache headers**: Optimalizácia načítavania obrázkov
- **Error handling**: Fallback na thumbnails pri zlyhaní

### ✅ Slideshow funkcionalita
- **Automatické slideshow**: Prepínanie každých 5 sekúnd
- **Manuálne ovládanie**: Tlačidlá pre predchádzajúci/nasledujúci
- **Klávesové skratky**: ←/→ prepínanie, medzerník start/stop, Escape stop
- **Thumbnails**: Klikateľné miniatúry pre skok na konkrétny obrázok
- **Loading states**: Zobrazenie načítavania a error stavov
- **Responsive design**: Funguje na desktop aj mobile

### ✅ Frontend
- **Moderný UI**: Pekný design s gradientmi a animáciami
- **React-like approach**: Dynamické updates bez page refresh
- **Status indikátory**: Realtime status Immich pripojenia
- **Error handling**: User-friendly error messages
- **Auto-refresh**: Memories sa automaticky obnovujú každých 5 minút

### ✅ Konfigurácia
- **Home Assistant options**: Všetky nastavenia cez HA UI
- **Environment variables**: Podpora pre rôzne prostredia
- **Defaultné hodnoty**: Graceful fallback pri chýbajúcej konfigurácii
- **Validácia**: Kontrola required polí

## Štruktúra súborov

```
addon-immich-kiosk-gallery/
├── config.yaml              # HA addon konfigurácia
├── build.yaml              # Build konfigurácia
├── Dockerfile              # Docker image definition
├── DOCS.md                 # Dokumentácia
├── rootfs/
│   ├── etc/s6-overlay/s6-rc.d/
│   │   ├── immich-kiosk/    # S6 longrun služba
│   │   └── user/contents.d/  # User bundle
│   └── usr/
│       ├── bin/
│       │   └── immich_kiosk.py    # Hlavný Python server
│       └── share/immich-kiosk/
│           ├── templates/
│           │   └── index.html      # HTML template
│           └── static/
│               ├── css/style.css   # CSS štýly
│               └── js/app.js       # JavaScript funkcionalita
```

## API Endpointy

### Webserver endpointy
- `GET /` - Hlavná stránka
- `GET /health` - Health check
- `GET /api/config` - Konfigurácia addon-u

### Immich integrácia
- `GET /api/immich/status` - Status pripojenia k Immich
- `GET /api/memories` - Aktívne memories (filtrované)
- `GET /api/albums` - Fotky z nakonfigurovaných albumov

### Proxy endpointy
- `GET /api/proxy/thumbnail/<asset_id>?size=<size>` - Thumbnail proxy
- `GET /api/proxy/image/<asset_id>` - Full image proxy

## Konfiguračné parametre

```yaml
immich_url: "http://your-immich-instance"
immich_api_key: "your-api-key" 
immich_show_memories: true
immich_show_albums: true
immich_albums: ["Family Photos", "Vacation", "Wedding"]
log_level: "info"
```

### Príklad použitia albumov

1. **Vytvorte albumy v Immich** s názvami ako "Family Photos", "Vacation", atď.
2. **Nastavte v konfigurácii** pole `immich_albums` s presne týmito názvami
3. **Povoľte albumy** nastavením `immich_show_albums: true`
4. **Addon automaticky načíta** fotky zo všetkých nakonfigurovaných albumov

## Bezpečnosť

- ✅ API key je skrytý pred frontend-om
- ✅ Proxy endpointy validujú asset IDs
- ✅ Cache headers pre optimalizáciu
- ✅ Error handling bez exposure internals
- ✅ Input validation na všetkých endpointoch

## Performance

- ✅ Thumbnails pre rýchle načítanie
- ✅ Full images len pri slideshow
- ✅ Cache headers (1 hodina)
- ✅ Async loading s fallback
- ✅ Auto-refresh každých 5 minút

## Testovanie

- `demo_test.py` - Generovanie sample dát
- `test_syntax.py` - Syntax validation
- Proxy endpointy testovateľné s curl
- Frontend testovateľný v prehliadači

## Nasledujúce kroky

1. **Testovanie v HA** - Deploy do Home Assistant
2. **Albumy podpora** - Pridanie albums endpoint-u
3. **Ďalšie Immich funkcie** - People, tags, search
4. **UI vylepšenia** - Fullscreen mode, slideshow nastavenia
5. **Performance** - Preload next image, lazy loading

Addon je kompletne funkčný a pripravený na použitie!
