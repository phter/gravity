Benutzte Bibliotheken:

math       - obviously
random     - to generate random planet positions
time       - to get accurate clock information
tkinter    - GUI
numpy      - to store trajectories in compact arrays





Nützliche Mathematik:

- Der Flächeninhalt eines Dreiecks, das von zwei Vektoren im 2-dimensionalen
  Raum aufgespannt wird, ist ein gutes Maß für die "Verschiedenheit" von
  zwei Vektoren und einfach zu berechnen: (v.x*w.y - v.y*w.x)/2.
  Wir benutzen das zur Abschätzung von dt bei der Berechnung der Flugbahn.