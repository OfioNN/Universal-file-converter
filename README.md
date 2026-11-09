## Obsługiwane konwersje

| Kierunek    | Grupa | Narzędzie              | Status           | Znane ograniczenia |
|-------------|-------|------------------------|------------------|--------------------|
| CSV → JSON  | A     | csv, json (wbudowane)  | działa (Lab 2)   | wszystkie wartości zapisywane jako tekst |
| JSON → CSV  | A     | csv, json (wbudowane)  | działa (Lab 2)   | tylko lista płaskich obiektów; wartości zagnieżdżone nieobsługiwane |
| TXT → DOCX  | B     | python-docx            | działa (Lab 3)   | każda linia to osobny akapit; plik musi być w UTF-8 |
| DOCX → TXT  | B     | python-docx            | działa (Lab 3)   | tylko tekst akapitów; formatowanie, znaczniki list i tabele są pomijane |
| DOCX → PDF  | C     | LibreOffice (headless) | działa (Lab 3)   | wygląd zależy od czcionek w systemie; inny dokument Office przemianowany na .docx też zostanie przekonwertowany |
| ODT → PDF   | C     | LibreOffice (headless) | działa (Lab 3)   | jak wyżej |