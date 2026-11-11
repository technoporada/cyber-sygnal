# Cyber Sygnał

[![CI](https://github.com/technoporada/cyber-sygnal/actions/workflows/ci.yml/badge.svg)](https://github.com/technoporada/cyber-sygnal/actions/workflows/ci.yml)

Lekki, lokalny przegląd wiadomości o cyberbezpieczeństwie. Pobiera publiczne
kanały RSS, filtruje wpisy po słowach i pozwala przeczytać je głosem dostępnym
w przeglądarce.

## Uruchomienie

Wymaga Pythona 3.10+; nie wymaga instalowania paczek ani konta:

```bash
python3 app.py
```

Otwórz <http://127.0.0.1:8777> i kliknij **Odśwież RSS**. Serwer nasłuchuje
wyłącznie na komputerze lokalnym. Zatrzymasz go przez `Ctrl+C`.

## Co już działa

- RSS z Niebezpiecznika i Sekuraka
- wyszukiwanie i proste kategorie: phishing, wycieki, podatności, ataki
- przycisk czytania tytułu i opisu przez głos przeglądarki
- komunikaty, gdy źródła RSS są niedostępne

Nie pobiera całych artykułów ani załączników. Wpisy RSS są wyświetlane jako
zwykły tekst, a link do oryginału otwiera się w nowej karcie. Głos zależy od
przeglądarki i głosów zainstalowanych w systemie; aplikacja nie wysyła tekstu
do zewnętrznej usługi TTS.

## Prywatność i ograniczenia

Aplikacja pobiera RSS wyłącznie po kliknięciu odświeżenia. Nie ma kluczy API,
konta, telemetrii ani lokalnej bazy danych. Kanały RSS są źródłem nagłówków,
nie pełną bazą podatności ani gwarancją wykrycia zagrożeń. Kategoryzacja opiera
się na prostych słowach kluczowych, więc może się mylić.

Lokalne pliki danych, środowiska Pythona i bazy są ignorowane przez Git.
