# Digital Box GUI

PyQt5 aplikacija za Digital Box, RPi, ESP32 in povezane naprave.
Struktura sledi sosednjemu projektu OvenDeviceConnect.

## Struktura

```text
gui_project/
   BOX_GUI.py              zdruzljiv zagonski skript
   BOX_GUI.py.bak          izvirnik pred razdelitvijo
   src/
      main.py             vstopna tocka
      launcher.py         zagon in ustvarjanje oken
      ui.py               glavno okno, signali in odpiranje dodatnih oken
      connections.py      povezovanje, seznam naprav in prikaz iskanja
      discovery.py        omrezno in SSH iskanje RPi
      devices.py          struktura podatkov in seznam serial naprav
      digital_controls.py digitalni vhodi, izhodi in auto tipke
      analog_controls.py  potenciometri, DAC, ADC, napetost in PWM
      saving.py           shranjevanje meritev in varnostne kopije
      state.py            skupne nastavitve, vrednosti in reference oken
      paths.py            poti do podatkov in UI
      styles.py           slogi Qt kontrol
      helpers.py          seznami tabel, jeziki in barve drsnikov
      workers.py          delavec za prikaz napredka
      tables.py           okna za DAC in ustvarjanje tabel
      setup_windows.py    nastavitve HUSA in pyro sistema
      automation.py       okna avtomatskih testov
      g800.py             okno G800
      bio24.py            okno BIO24
   tests/
      test_structure.py   preverjanje strukture in zagona brez naprav
   DigitalBox/             obstojeci protokoli in strojni ukazi
   package/                obstojece interne knjiznice
   QT_designer/            Qt Designer datoteke
   config_file/
   data/
```

Glavno okno sestavlja funkcionalne module prek razredov `ConnectionMixin`,
`SavingMixin`, `DigitalControlsMixin` in `AnalogControlsMixin`. UI signali zato
se vedno uporabljajo iste metode, njihova implementacija pa je locena po namenu.
Skupne vrednosti se berejo in spreminjajo prek `state`, ne prek kopiranih uvozov.
Strojni protokoli, podatkovne datoteke in postavitev oken niso spremenjeni.
Tipka `ConnectToDevice` zazene loceno aplikacijo `OvenDeviceConnect.exe`.
EXE se najprej isce poleg zagonske aplikacije, nato v sosednjem projektu
`OvenDeviceConnect/dist`. Pri zagonu iz Python kode je prva lokacija mapa
`gui_project`, pri zapakiranem EXE pa mapa tega EXE-ja. Glavno okno ostane odprto;
ob manjkajocem EXE-ju ali napaki zagona se prikaze opozorilo.

## Zagon

Uporabi obstojece okolje `testOven`, v katerem so na voljo PyQt5 in interne
knjiznice. Namestitev v novo okolje zahteva odvisnosti iz `requirements.txt`
ter ustrezno interno knjiznico `stream`; istoimenski paket iz PyPI ni nujno pravilen.

```powershell
conda activate testOven
python BOX_GUI.py
```

Podprta sta tudi `python -m src.main` in `python src/main.py`.
Zaganjalnik nastavi delovno mapo na mapo projekta, ker obstojeci strojni moduli
in Qt okna uporabljajo relativne poti. Pri EXE uporabi PyInstallerjevo mapo virov.
Ob zagonu ostane obstojeci postopek kopiranja virov v sosednjo `gui_application`;
sam uvoz modulov ne kopira datotek in ne odpira oken.

## Preverjanje

```powershell
python -m unittest discover -s tests -p test_structure.py -v
```

Preizkusi preverijo uvoze, sintakso, sestavo glavnega okna, reference dodatnih
oken in zagon EXE-ja prek tipke `ConnectToDevice`. Zagon zunanje aplikacije,
omrezno iskanje in povezovanje naprav so nadomesceni v testih.
Preverjanje s fizicnimi napravami je se vedno potrebno.

## Windows EXE

Iz okolja z namescenimi PyInstaller, PyQt5 in internimi knjiznicami zazeni:

```powershell
conda activate testOven
python create_exe.py
```

Skript uporablja projektne poti iz `BOX_GUI.spec` in ustvari enodatotecni
`dist/BOX_GUI.exe` brez konzolnega okna. Vkljuceni so moduli aplikacije,
Qt obrazci, konfiguracija, slike, tabele in interne knjiznice. Obstojecega
`OvenDeviceConnect.exe` iz sosednjega projekta kopira v isto mapo `dist`.
Za tipko `ConnectToDevice` morata biti oba EXE-ja v isti mapi.

Qt obrazci iz `QT_designer` ostanejo vgrajeni v EXE in se nalagajo iz njegovega
paketa; zunanja mapa `QT_designer` ob EXE-ju ni potrebna. V izvornem projektu
ostane potrebna za zagon Python kode in ponovno izdelavo EXE-ja.

Tudi `config_file` se bere neposredno iz paketa EXE-ja, ne iz zunanje mape.
Spremembe JSON konfiguracije zahtevajo ponovno izdelavo EXE-ja. Izvorna mapa
`config_file` zato ostane del projekta za zagon Python kode in izdelavo.

Ob prvem zagonu `BOX_GUI.exe` ustvari `data` in `file.ini`
ob EXE-ju. Obstojecih datotek ne prepisuje; meritve in spremembe
nastavitev tako ostanejo tudi po zaprtju. EXE postavi v mapo, v katero imas
pravico pisanja. Za prenos obstojecih nastavitev in meritev prenesi tudi te mape.
Python za osnovni zagon ni potreben; obstojeci avtomatizacijski skripti,
ki posebej zaganjajo conda/Python okolje, to okolje se vedno potrebujejo.

## GitLab Posodobitev

`update.py` uporablja nastavljeni Git remote in upstream trenutne veje.
Git mora biti namescen, mapa aplikacije pa mora biti znotraj Git repozitorija.
Samostojni EXE brez repozitorija `.git` ne more izvajati Git posodobitev.
Prijava uporablja obstojece Git nastavitve; gesla ali tokeni niso zapisani v kodo.

Posodobitev ohrani celotno trenutno vsebino `data` in `config_file`: spremenjene,
nove, ignorirane in izbrisane datoteke. Najprej naredi varnostno kopijo zunaj
repozitorija ter zacasno umakne spremembe samo teh map v svoj Git stash.
Nato izvede `git pull --ff-only` in obnovi lokalni podatkovni mapi, tudi ce
posodobitev ne uspe. Nove ali spremenjene datoteke iz oddaljenih podatkovnih
map se ne uveljavijo. Obstojeci uporabniski stash ostane nedotaknjen.

Lokalne spremembe kode zunaj teh map, pripravljen commit ali razhajanje vej
ustavijo posodobitev brez prisilnega prepisovanja kode. Ce obnova podatkov
odpove, napaka navede lokacijo ohranjene varnostne kopije. `.gitignore` sam
ne izkljuci sprememb datotek, ki jim Git ze sledi.

```powershell
python -m unittest discover -s tests -p test_update.py -v
```

Preizkusi uporabljajo le zacasne lokalne Git repozitorije. Tipka v glavnem
oknu trenutno zaganja `update.exe`; sprememba `update.py` zato zahteva tudi
ponovno izdelavo `update.exe`, preden jo uporabis prek te tipke.

