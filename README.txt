Benutzte Bibliotheken
=====================

math                  - obviously
random                - to generate random planet positions
tempfile              - to store background images
concurrent.futures    - to load images asynchronously
time                  - to get accurate clock information
tkinter               - GUI
numpy                 - to store trajectories in compact arrays
matplotlib            - to create gravity visualization
PIL                   - to transform images / make matplotlib play nice with Tkinter


Nützliche Mathematik
====================

- Der Flächeninhalt des Parallelograms, das von zwei Vektoren im 2-dimensionalen
  Raum aufgespannt wird, ist ein gutes Maß für die "Verschiedenheit" von
  zwei Vektoren und einfach zu berechnen: (v.x*w.y - v.y*w.x)/2.
  Wir benutzen das zur Abschätzung von dt bei der Berechnung der Flugbahn.


Bugs / Verbesserungsmöglichkeiten
===================================

Viele :)

- Durch die vielen Einstellungsmöglichkeiten gibt es Kombinationen, die vom
  Programm nicht korrekt behandelt werden (können)
  Zum Beispiel können nicht sehr viele Planeten maximaler Größe mit
  maximalem Mindestabstand erzeugt werden.
