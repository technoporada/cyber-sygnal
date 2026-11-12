# Cyber Sygnał

[![CI](https://github.com/technoporada/cyber-sygnal/actions/workflows/ci.yml/badge.svg)](https://github.com/technoporada/cyber-sygnal/actions/workflows/ci.yml)

Lekki, lokalny przegląd wiadomości o cyberbezpieczeństwie. Pobiera publiczne
kanały RSS, filtruje wpisy po słowach i pozwala przeczytać je głosem dostępnym
w przeglądarce. Wszystko działa lokalnie na Twoim komputerze — nie ma kont,
kluczy API ani telemetrii.

---

## 🚀 Uruchomienie

Wymaga Pythona 3.10+; nie wymaga instalowania żadnych paczek z PyPI ani konta:

```bash
git clone https://github.com/technoporada/cyber-sygnal.git
cd cyber-sygnal
python3 app.py
```

Otwórz <http://127.0.0.1:8777> w przeglądarce. Serwer nasłuchuje wyłącznie na
`127.0.0.1` (tylko Twój komputer). Zatrzymasz go przez `Ctrl+C`.

Po otwarciu strony wpisy z kanałów RSS pobierają się automatycznie w tle — nie
musisz klikać „Odśwież RSS”, choć przycisk ten działa i wymusza ponowne
pobranie najnowszych wpisów.

---

## 📰 Co działa

| Funkcja | Opis |
|---------|------|
| Kanały RSS | Niebezpiecznik i Sekurak (pobierane automatycznie przy starcie) |
| Kategoryzacja | Phishing, Wycieki, Podatności, Ataki, Inne (na podstawie słów kluczowych) |
| Wyszukiwanie | Filtruj wpisy po tytule, opisie i źródle |
| Czytanie na głos | Przeglądarka czyta tytuł i opis (TTS lokalnie, bez wysyłania tekstu z zewnątrz) |
| Linki do oryginałów | Kliknij tytuł, aby otworzyć artykuł w nowej karcie |
| Błędy źródeł | Komunikaty na stronie, gdy kanał RSS jest niedostępny |

Aplikacja nie pobiera całych artykułów ani załączników — tylko nagłówki, streszczenia i linki do oryginałów.

---

## 🔐 Bezpieczeństwo

- Aplikacja nasłuchuje wyłącznie na `127.0.0.1` — nie jest dostępna z sieci zewnętrznej.
- Nie ma kluczy API, kont użytkowników, telemetrii ani lokalnej bazy danych.
- Kanały RSS są pobierane przez HTTPS z zaufanych domen (`feeds.feedburner.com`, `sekurak.pl`).
- Serwer odrzuca każde przekierowanie poza dozwolony host źródła.
- Głos (TTS) działa lokalnie w przeglądarce — tekst nie jest wysyłany do żadnej zewnętrznej usługi.

---

## 📦 Wersje / Release

| Wersja | Data | Co nowego |
|--------|------|-----------|
| `v0.4.0` | 2026-11-12 | Lokalne zapisywanie wpisów do `data/items.json` — wycieki i inne wpisy nie giną po odświeżeniu, endpoint `/api/leaks` zwraca tylko wycieki |
| `v0.3.0` | 2026-11-12 | 17 testów jednostkowych (testy kategorii, deduplikacji, sortowania po dacie, zapis/odczyt z pliku) |
| `v0.2.0` | 2026-11-12 | Auto-pobieranie RSS przy starcie serwera, naprawiony sparse checkout (przywrócono `static/` i `tests/`), serwer nasłuchuje tylko na `127.0.0.1` |
| `v0.1.0` | 2026-11-11 | Pierwsza wersja: RSS z Niebezpiecznika i Sekurak, kategoryzacja, TTS, prosty serwer HTTP |

Wszystkie release są otagowane na GitHubie:  
https://github.com/technoporada/cyber-sygnal/releases

---

## 🔒 Prywatność i ograniczenia

Aplikacja pobiera RSS wyłącznie po starcie serwera lub po kliknięciu „Odśwież RSS”. Nie ma kluczy API, konta, telemetrii ani lokalnej bazy danych. Kanały RSS są źródłem nagłówków, nie pełną bazą podatności ani gwarancją wykrycia zagrożeń. Kategoryzacja opiera się na prostych słowach kluczowych, więc może się mylić.

Głos zależy od przeglądarki i zainstalowanych w systemie głosów TTS. Aplikacja nie wysyła tekstu do zewnętrznej usługi.

Lokalne pliki danych, środowiska Pythona i bazy są ignorowane przez Git.
