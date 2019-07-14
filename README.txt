Gravity - ein einfaches Weltraumspiel
=====================================


Teammitglieder
==============
Barbara Honeder
Jan Köglburger
Philipp Weinfurter


Projektziel
===========

Wir wollen eine spielerische Simulation der Gravitationskräfte von Planeten
auf ein Raumschiff erstellen.

Ziel des Spiels ist es, eine Rakete von einem Planeten zu einem anderen
Planeten zu manövrieren, und dabei die Gravitation der dazwischenliegenden
Planeten geschickt auszunutzen.

Man kann die Abschussgeschwindigkeit bestimmen und auf beliebigen Planeten landen,
also beliebig viele Zwischenstopps machen.

Es gibt viele Einstellungen, um die Physik der Simulation zu verändern.
Diese reichen von Größe und Anzahl der Planeten, bis zur Einstellung der
Gravitationskonstante.

Natürlich gibt es auch schwarze Löcher!

Schließlich gibt es die Möglichkeit eine Visualisierung der Gravitation
einzublenden, in Form eines Farbverlaufs (Heatmap) und eines Vektordiagramms,
um eine bessere Vorstellung von den vorhandenen Kräften zu bekommen.

Wir haben folgende Vereinfachungen vorgenommen:

   * Das Spieluniversum ist zweidimensional.
   * Die Entfernungen zwischen Planeten sind drastisch reduziert.
   * Planeten besitzen keine Atmosphäre
   * Das Raumschiff startet stets senkrecht
   * Einmal gestartet, kann das Schiff nicht mehr gesteuert werden.
     Die Flugbahn wird also allein durch Abschussrichtung (aufgrund der Rotation
     der Planeten) und der Abschussgeschwindigkeit bestimmt.
   * Es gibt beim Start keine Beschleunigungsphase, die Rakete erreicht
     die Abschussgeschwindigkeit instantan.
   * Es gibt bei der Landung auf einem Planeten keine Abbremsung


Benutzte Bibliotheken
=====================

math                  - klar
random                - um zufällige Platetenpositionen zu erzeugen
tempfile              - Zum Speichern der Hintergrundbilder
concurrent.futures    - Um Visualisierungn asynchron zu erzeugen
traceback             - Um Exceptions von Futures sinnvoll anzeigen zu können.
time                  - Zeitmessung
tkinter               - GUI
tkinter.filedialog    - Laden / speichern
numpy                 - effizientere Berechnung / Speicherung der Flugbahn
matplotlib            - Erzeugen der Visualisierungen der Gravitation
PIL                   - Transformation der von matplotlib erzeugten Bilder,
                        Benutzung von tkPhotoImage
json                  - Einstellungen laden / speichern



Berechnung der Flugbahn
=======================

Wir approximieren die Flugbahn mit einem Polygonzug.
Die einzelnen Segmente werden iterativ berechnte.

Wird die Rakete gestartet, nimmt sie sofort die Abschussgeschwindigkeit an.
(Das ist natürlich ein vereinfachtes Modell)

Für eine bessere Approximation berechnen wir die Segmente nicht nur anhand
von Gravitation an Punkt p und momentaner Geschwindigkeit des Schiffs, sondern
berechnen einen Hilfspunkt p', an dem Das Schiff nach kurzer Zeit (dt) wäre
und berechnen den Gravitationsvektor am Ort p'. Dann verwenden wir das Mittel
der beiden Gravitationsvektoren, um die Geschwindigkeitsänderung zu berechnen.

Schematischer Ablauf des Algorithmus:
-------------------------------------

Sei g(p) der Gravitationsvektor an der Position p.
Zum Zeitpunkt t_0 ist die Rakete an Position p_0 mit Geschwindigkeit v_0.

1) Wähle dt
2) Setze v' = v_0 + g(p_0)
3) Berechne p' := p_0 + v' * dt
4) Setze g' := 1/2 * (g(p_0) + g(p'))   # mittlerer Gravitationsvektor
5) Berechne Flächeninhalt des Parallelogramms, das von v_0 * dt und g' * dt
   aufgespannt wird. Das ist unser Maß für den Approximationsfehler.
7) Fehler zu groß (konfigurierbar)? -> dann veringere dt und zurück zu 2)
8) Setze v_1 := v_0 + g' * dt
         p_1 := p_0 + v_1 * dt
         t_1 := t_0 + dt
usw.

Diese Approximation der Flugbahn erschien uns für die Simulation gut genug,
sodass wir keine Notwendigkeit sahen, genauere (und damit langsamere) Methoden
zu verwenden (wie z.B. das Runge-Kutta Verfahren, das auf einer ähnlichen Idee
beruht, aber mehrere Hilfspunkte mit verschiedenen Gewichtungen verwendet.)

Kritisch bei dieser Methode ist die Wahl von dt. Darum verwenden wir hier
ein *adaptives* Verfahren:

- Ist der Approximationsfehler schon beim ersten Durchgang unter einer gewissen
  Schwelle, wird dt *vergrößert* (In der Hoffnung, dass wir längere Segmente
  verwenden können)
- Ist der Fehler zu groß, wird dt *verkleinert*

Dies geschieht bei der Berechnung jedes Segments der Flugbahn. Die Segment-
länge passt sich also der Krümmung der Flugbahn an.
Starke Krümmung   - kürzere Segmente
Schwache Krümmung - längere Segmente


Bugs / Verbesserungsmöglichkeiten
===================================

Viele :)

- Durch die vielen Einstellungsmöglichkeiten gibt es Kombinationen, die vom
  Programm nicht korrekt behandelt werden (können)
  Zum Beispiel können nicht sehr viele Planeten maximaler Größe mit
  maximalem Mindestabstand erzeugt werden.

- Wir haben uns relativ spät entschlossen, numpy zu verwenden. Das hat
  zu zeitaufwändigen Überarbeitungen geführt, die noch nicht völlig ab-
  geschlossen sind.
  Wenn man schon numpy verwendet, sollten alle Daten in numpy arrays liegen
  und die Python Objekte sollten nur Views auf diese arrays bereitstellen.
  Das wiederum wirkt sich auf so ziemlich alle Algorithmen, bzw. deren
  Implementierung aus...

- Wir haben uns nicht klar entschieden, ob wir nun ein Spiel oder eine
  Simulation machen wollen. Beides schien interessant, lässt sich aber
  letztlich nicht vereinbaren. Vor allem bei der Gestaltung der Benutzer-
  oberfläche war das problematisch.