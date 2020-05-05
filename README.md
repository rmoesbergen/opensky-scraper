## OpenSky Scraper
Dit programma houdt vluchtgegevens bij door het periodiek bevragen van de OpenSky API
(https://opensky-network.org/apidoc/rest.html)

### Installatie instructies
Het programma is gemaakt om op een Raspberry PI (of soortgelijke mini-computer) te draaien.
Alvorens het te installeren, moet eerst de Raspberry van een OS + connectiviteit worden voorzien.
Instructies hiervoor zijn hier te vinden:

https://desertbot.io/blog/headless-raspberry-pi-4-ssh-wifi-setup

Zorg dat SSH toegang mogelijk is en het device via WiFi bereikbaar is.
Volg onderstaande stappen nadat de PI op het netwerk toegankelijk is:

- Log in via SSH op de Raspberry pi
```bash
ssh pi@<ip adres pi>
```
- Start het volgende commando:
```bash
curl https://raw.githubusercontent.com/rmoesbergen/opensky-scraper/master/install.sh | bash
```
- Pas in /home/pi het bestand 'settings.json' naar wens aan. Zie hieronder voor uitleg van alle instellingen.

- Start het programma als service:
```bash
sudo systemctl start opensky-scraper.service
```

Het programma wordt op de achtergrond gestart en zal de logfiles en CSV gaan genereren. Bij een
herstart van de raspberry pi zal het programma automatisch weer gestart worden.

### Instellingen
Alle instellingen bevinden zich in een bestand 'settings.json'. De instellingen zijn als volgt:

- api_url: De lokatie van de OpenSky API service. Deze hoeft normaal gesproken niet aangepast te worden
- lamin, lamax, lomin, lomax: Deze 4 parameters geven het geografisch gebied aan waarop gefilterd moet worden bij het ophalen van vluchten.
- poll_interval: Het interval waarmee de API service wordt bevraagd, in seconden.
- username: De gebruikersnaam die meegestuurd moet worden om in te loggen op de OpenSky API.
Als de gebruikersnaam leeg wordt gelaten (""), zal geen authenticatie plaatsvinden
- password: Het password dat bij de OpenSky username hoort.
- max_geo_altitude: De maximale hoogte van een vlucht voor registratie in het CSV bestand, in meters. Als de vlucht boven deze grens is,
zal deze niet worden geregistreerd in het CSV bestand.
- log_file: De lokatie van een (debug) logbestand waarin alle responses van de API 1 op 1 ongefilterd worden gelogged.
- csv_file: De lokatie van het CSV bestand waarin alle vluchten die voldoen aan alle criteria worden geschreven.
De bestandsnaam kan "datum formatterings tekens" bevatten om periodiek een nieuw bestand te schrijven. Voor een overzicht van te gebruiken
formatteringstekens, zie: https://strftime.org/
In het standaard voorbeeld wordt "flights-%m.csv" gebruikt, waarmee elke maand een nieuw bestand wordt geschreven, met in de bestandsnaam
het maandnummer, uitgevuld met een '0'.
- history_file: De lokatie van het bestand waarin de vluchten die reeds 'gezien' zijn wordt bewaard. Dit bestand wordt bijgehouden om dubbele logging
van vluchten te voorkomen. Het formaat is in JSON en bevat alle icao24 codes en een timestamp van vluchten.
Bij het herstarten van het programma zal deze historie weer worden ingelezen, zodat vluchten nooit dubbel worden geschreven in de CSV file.
- keep_history: Hoe lang het programma de vluchten 'onthoudt' in de history file, om te ontdubbelen, in seconden.
Als een vlucht binnen dit interval 2 of meer keer wordt 'gezien', zal er maar 1 record worden geschreven in de CSV file.
