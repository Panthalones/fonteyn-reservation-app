Fonteyn Holiday Parks website

Bestanden:
- index.html: publieke website
- admin.html: verborgen adminpagina via /admin.html
- style.css: alle styling
- script.js: reservatieformulier
- admin.js: adminpagina + demo Entra ID login scherm

Belangrijk:
- API_URL staat op een lege string, zodat Nginx /api/ doorstuurt naar Flask/Gunicorn.
- admin.html staat niet in de navbar. Open direct via http://SERVER-IP/admin.html
- De Entra ID login is een demo login scherm zonder echte Microsoft authenticatie, omdat echte Entra ID een tenant ID, client ID en redirect URI nodig heeft.
