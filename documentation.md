tamina Documentation

## Kurzfassung

In unserem Projekt geht es darum, eine App zu entwickeln, welche ihre Nutzer durch ein Spiel animiert, sich zu bewegen.

Die App soll dem Nutzer eine Übung vorgeben und über eine Webcam erkennen, ob er sie korrekt ausführt.

Hierfür werden die für ein Level relevanten Körperteile mit farbigen Markern gekennzeichnet, deren Positionen von der App erfasst und ausgewertet werden.

Das Programm soll in Kombination mit Hilfsmitteln (z. B. Hanteln, etc.), welche ggf. auch farbig markiert werden, einsetzbar sein.

Zunächst möchten wir die App für PCs und Laptops entwickeln, da uns hier mehr Rechenleistung zur Verfügung steht. Den wichtigsten Code werden wir in Python schreiben und hierbei, unter anderem, die Libraries OpenCV und NumPy verwenden.

Einen besonderen Schwerpunkt möchte ich bei der Programmierung auf die Variabilität (durch universellen Level-Interpreter, welcher leichtes Hinzufügen neuer "Levels" ermöglicht, und durch eine integriertes Kalibrierungstool zur Anpassung der Farben an Lichtverhältnisse) setzten.

## Einleitung

Mit unserer Arbeit möchten wir etwas entwickeln, wovon viele Menschen profitieren können. Ein grundlegendes menschliches Bedürfnis, welches jede und jeder hat, ist das der Gesundheit. Wenn es um die Verbesserung der Gesundheit geht, denken die meisten an die, sich mit rasender Geschwindigkeit weiterentwickelnde, Medizin – doch ein weiterer, annähernd so wichtiger Faktor wird von vielen vernachlässigt: Die Fitness. Wer sich durch regelmäßige Bewegung fit hält ist gesünder und lebt länger, da unter anderem Kreislauf, Knochen und Immunsystem gestärkt werden.

Doch so einfach dies gesagt ist, so schwer fällt es vielen, sich hierfür zu motivieren. Besonders in Zeiten einer Pandemie, in denen Sportstudios und öffentliche Parks geschlossen sind, fehlt vielen eine Beschäftigung, die sie fit hält und zu der sie motiviert sind. Hier wollen wir mit unserer Forschung helfen: Wir entwickeln eine App, die ihre User animiert, sich zu bewegen und fit zu halten. Hierbei soll dem User eine Trainingsübung vorgegeben werden, welche dieser wiederholt ausführen soll und dafür mit einem Punktestand belohnt wird. Diese Level können selbst ohne Programmierkenntnisse in einer Datei geschrieben und hinzugefügt werden. Für diese muss unser Programm die Bewegungen des Users erkennen und mit den vorgegebenen abgleichen. Es gibt bereits einige Lösungen hierzu, doch die zuverlässigen erfordern spezielle Hardware, wie 3D-Tracker, über die nicht jeder verfügt. Da wir eine Lösung für den Großteil der Bevölkerung schaffen wollen, müssen wir auf Dinge zurückgreifen, die jeder zuhause hat und entschieden uns daher für eine Erkennung der Bewegungen mithilfe farblicher Markierungen am Körper des Users.

Wie man auch in vielen anderen Bereichen beobachten kann, gibt selbst das einfachste Belohnungssystem einen hohen [Motivationsschub][1]. Wir haben Stamina mit dem Ziel entwickelt, auch während des Lockdowns für ausreichend Bewegung zu sorgen, da es ansonsten sehr schwierig sein kann, sich ausreichend zu motivieren. Wie zahlreiche Bekannte berichten, bewegen sich die meisten nur wenig. Unser Programm Stamina ist bestens dafür geeignet, Fitness und ansprechenden Zeitvertreib zu kombinieren.

## Funktionsweise

### Erklärung wichtiger Begriffe

Zunächst sind einige Begriffe zu erklären:

#### Level

Ein Level ist eine Aufgabenstellung, welche wiederholt ausgeführt werden muss, um den Score zu erhöhen.

#### Marker

Ein Marker ist eine farbliche Markierung am Körper des Users, welche vom Programm erkannt werden kann. Dies kann beispielsweise ein farbiger Pompom sein.

#### Part

Ein Part ist ein Körperteil des Users, dessen Koordinaten erkannt werden können. Die Parts werden mit Markern versehen. Levels können beliebig viele Parts verwenden.

#### Waypoint

Waypoints sind Punkte, welchen sich die Parts in einer bestimmten Reihenfolge annähern müssen, um den Score zu erhöhen.

### Level-Interpreter

Um beim Design der Levels die Aspekte der Variabilität und der Erweiterbarkeit zu wahren, galt es, eine Methode zu entwickeln, mit der sich vielfältige Aufgabenstellungen umsetzen lassen, während das Hinzufügen neuer Levels möglichst einfach bleibt. Wir entschieden uns daher, jedes Level in einer eigenen Datei zu speichern, welche anhand ihrer Kategorien in einer Ordnerstruktur lokalisiert sind. Beim Programmstart wird nun das Verzeichnis `/resources/challenges` nach Unterordnern wie `/category_1` durchsucht, welche nun wiederum die Level-Dateien, bspw. `level_03` enthalten. Alle gefundenen Levels werden, nach Kategorien geordnet, in einem Dictionary gespeichert.

Eine typische Level-Datei sieht wie folgt aus:
```python
{
 "part0" : {
  "name" : "part0",
  "color" : "gelb1",
  "waypoints" : [{"x" : 50, "y" : 50},{"x" : 30, "y" : 30},{"x" : 40, "y" : 40},{"x" : 10, "y" : 10}],
  "maxTime" : 10,
  "wpTolerance" : 40,
  "wpColor" : (0, 255, 255)
 },
 "part1" : {
  "name" : "part1",
  "color" : "gruen1",
  "waypoints" : [{'x': 40, 'y': 15},{'x': 48, 'y': 33}],
  "maxTime" : 5,
  "wpTolerance" : 30,
  "wpColor" : (255, 255, 0)
 },
}
```

Die Datei kann eine beliebige Anzahl an Parts (hier zwei) enthalten, welche wiederum ihren Namen (hier oben `part0`), den Namen des Standard-Farb-Arrays (hier oben `gelb1`), die Koordinaten (0 bis 100 jeweils für x und y) beliebig vieler Waypoints (hier oben 4), einen Maximalwert für die Zeit, die Toleranz der Waypoints, sowie die Farbe der anzuzeigenden Waypoints speichern.

### Erkennung der Positionen der Marker

Als Koordinaten der Parts soll der Mittelpunkt der größten zusammenhängenden Fläche von Pixeln einer bestimmten Farbe (mit Toleranz) gewählt werden, sofern jene Fläche den in der Konfigurationsdatei festgelegten Mindestwert an Pixeln aufweist.

Hierzu wird zunächst eine [HSV-Version][2] des Eingangsbildes erstellt, aus welcher mithilfe der Arrays für die jeweiligen Maximal- und Minimalwerte von Farbwert (Hue), Farbsättigung (Saturation) und Hellwert (Value) eine binäre Maske errechnet wird, deren Pixel an Stellen, deren Farben im gewünschten Farbbereich liegen, weiß und an allen anderen Stellen schwarz sind. Nun sucht das Programm die an den Grenzen liegenden Konturen und sortiert diese nach deren Flächeninhalte. Sollte die größte Fläche den Minimalwert für die Part-Flächen erfüllen, so wird deren Mittelpunkt als Koordinate für den Part verwendet.

### Vervollständigung der Bewegung der Markerzentren

Da aus Hardwaregründen starke Schwankungen in der Bildrate vorkommen können, besteht die Möglichkeit, dass durch zu schnelle Bewegungen die Waypoints ausgelassen werden. Aus diesem Grund wird aus den vorhandenen aufgenommenen Markerzentren eine Kurve berechnetet, um eine möglichst genaue Heuristik der echten Markerzentren zu erstellen. Die intuitivste Möglichkeit wäre, alle Punkte mit Geraden zu verbinden. Da Bewegungen jedoch selten linear sind, haben wir uns dazu entschieden, eine Funktion zu entwickeln, sodass mehrere Punkte miteinberechnet werden, nicht nur die beiden, zwischen denen die Kurve berechnet werden soll, wie es bei der nächsteinfachsten Möglichkeit durch Halbkreise der Fall wäre. So lässt sich ein größerer Teil der Bewegung abschätzen. Dies wird über einen [Spline][3] realisiert.

Ein Spline ist eine Funktion, welche aus mehreren Polynomfunktionen zusammengesetzt ist. In dieser Funktion wird aus den letzten Punkten eine differenzierbare Kurve mit [Polynomen][4] dritten Grades gebildet. Wie viele das sind, wird in der Konfigurationsdatei festgelegt. Dort wird auch festgelegt, wie viele Punkte auf der Kurve gezeichnet werden.

Mit dieser Methode lässt sich eine relativ genaue Heuristik der Markerzentren berechnen. Daraus wird danach schlussendlich berechnet, ob das Markerzentrum durch den Toleranzbereich kam.

### Level-Auswahl

Die Level-Auswahl findet in der aktuellen Version über zwei Trackbars statt, die im Fenster `Level Selection` zu finden sind. Der obere Regler ist für die Auswahl der gewünschten Kategorie der Übung zuständig, während sich über den unteren das Level innerhalb der Kategorie auswählen lässt. Diese Methode kann in zukünftigen Versionen noch verschönert werden, erfüllt jedoch ihren Zweck. Der Name der Kategorie, der Name des Levels und der aktuelle Score stehen in der oberen rechten Bildschirmecke.

### Abgleichen der Positionsdaten mit denen aus der Aufgabenstellung

Zunächst hielten wir es für die beste Option, eine [künstliche Intelligenz][5] zu entwickeln, welche erkennt, ob der User die Aufgabe erfüllt. Diese Methode würde bei den meisten Aufgaben wohl sehr zuverlässig funktionieren, doch wäre die Implementierung neuer Aufgaben sehr aufwändig, da man die KI hierfür immer neu trainieren müsste. Da dies die Erweiterbarkeit des Programmes stark erschwert hätte, entschieden wir uns für die Entwicklung eines Algorithmus, welcher beliebige Idealwerte mit variabler Toleranz (aus der Level-Datei) mit den Inputdaten (der Kamera) abgleichen kann. Dies verleiht uns außerdem mehr Kontrolle und Variabilität bezüglich des Level-Designs.

Ein Problem dabei war, dass, wenn man sich in eine bestimmte Richtung mit dem Marker dem Waypoint annäherte, sich auch der nächste Teil des Levels erfüllte. Dies resultierte daher, dass sich, nachdem ein Waypoint erfüllte worden war, der Punkt sofort an eine andere Position sprang. Wenn der Spline zu diesem Zeitpunkt noch an diesem Ort befand, würde auch der nächste Teil sofort erfüllt. Aus diesem Grund werden zwar alle der letzten (wie viele das sind, wird in der Konfigurationsdatei bestimmt) echten Markerzentren zur Berechnung herangezogen, aber nur die berechneten Punkte zwischen den letzten Beiden können auch tatsächlich einen Waypoint erfüllen.

Diese Lösung war allerdings auch nicht perfekt, da dies nichts daran ändert, wenn die Waypoints zwischen den neusten beiden liegen. Außerdem können je nach Beschleunigung bzw. Entschleunigung der Marker diese letzten Beiden sehr eng beieinander liegen.

In diesem Screenshot sieht man das Problem der ersten Lösung:

![image](https://github.com/Daniel7609/Stamina/blob/4bd915e98690d6fac187969a81d54e3fdcca96ac/image_solution_Abgleichen%20der%20Positionsdaten%20mit%20denen%20aus%20der%20Aufgabenstellung.jpg)

Dem mit dem Kreuz markierten Punkt und dein drei weiteren rosa Punkte (außer dem am oberen Ende) wurde der Spline generiert, doch da der türkise Waypoint nicht im letzten Viertel dieser liegt, wurde er nicht als getroffen erkannt.

Die neue Lösung besteht darin, alle Punkte der Spline zu prüfen und nachdem ein Waypoint getroffen wurde, alle echten Markerzentren aus dem Speicher löschen, sodass ein Waypoint, der daraufhin in einen Bereich verschoben würde, der noch auf dem Spline liegt, nicht mehr erkannt wird, da der Spline zurückgesetzt wird.

Man kann sich alle so berechneten Punkte auch darstellen: Mit einer Variablen kann man sich alle Punkte, die zur Berechnung verwendet werden, anzeigen lassen. Standardmäßig sind die echt gemessenen Markerzentren rosa, die zusätzlich berechneten grün und die zur Erfüllung der Waypoints verwendeten Punkte rot. Alle Farben und Größen dieser Punkte lassen sich aber in der Konfiguration festlegen.

### Level-Scoring

Um den Score eines Users zu messen, gleicht der Level-Thread kontinuierlich die Koordinaten der verwendeten Parts mit den Vorgaben aus der importierten Level-Datei ab.

Jedes Level hat mehrere Parts, die jeweils einen eigenen Partscore besitzen. Jedem Part wird ein Marker zugeordnet. Sobald ein Teil des Parts erfüllt ist, indem man den Punkt, der ihn repräsentiert mit dem Marker `berührt` wird, springt der Punkt zu einer anderen Stelle. Nach ein paar Stellen hat man dann den Part erfüllt; der Partscore erhöht sich. Dabei springt der Punkt wieder auf die Originalposition zurück und man kann den Part wiederholen. Dies muss man mit allen Markern zugleich machen. Der Gesamtscore entspricht dem niedrigsten Partscore des Levels, das heißt, man muss alle Parts gleichermaßen erfüllen, es reicht nicht, sich nur auf eine Bewegung zu fokussieren.

Der so ermittelte Gesamtscore wird über eine Zahl in der rechten oberen Ecke angezeigt. Der Partscore wird auf den entsprechenden Parts selbst angezeigt, wobei aufgrund der Lesbarkeit die Farbe dem Negativ der Farbe des Punktes entspricht.

### Working Area

Ein Problem dabei ist, dass je nach Hardware die Webcam einen so großen Winkel hat oder nicht optimal platziert werden kann, sodass große Teile des Bildes gar nicht genutzt werden können, weil der User nur einen kleinen Teil des Bildes ausmacht. Aus diesem Grund kann man selbst die Working Area festlegen, der Bereich des Bildes, der auch für das Level-Scoring genutzt wird. Standardmäßig hat diese die Größe des Kamerabildes, man kann sie allerdings mit einem Rahmen so eingrenzen, sodass nur der Teil des Bildes gewertet wird, der auch sinnvoll ist. So ersetzt die Working Area das Originalbild. Man muss allerdings beachten, dass sich durch die geringere Auflösung die Zuverlässigkeit verringern kann.

#### Working Area Conversion

Aus diesem Grund benötigen wir in mehreren Bereichen eine Methode, die aus Prozentangaben in der Working Area die Pixelkoordinaten im Gesamtbild berechnet.

### Konfigurationsdatei

```python
app_name = "Stamina"
min_area = 300
camera_port = 1
dshow = True
fps = 60
font = 0
textSize = 0.5
textColor = (0, 255, 0)
textThickness = 1
mirrorMode = True
usePlts = 4
newPlts = 500

showCapturedPoints = True
capturedPointColor = (255, 0, 255)
capturedPointSize = 10
capturedPointThickness = -1

showCurvePoints = True
curvePointColor = (0, 255, 0)
curvePointSize = 5
curvePointThickness = -1

showCheckedPoints = True
checkedPointColor = (0, 0, 255)
checkedPointSize = 15
checkedPointThickness = -1

waypointThickness = -1

doResize = True
txtOffset = 5
challengesPath = "resources/challenges"
colorsPath = "calibration/colors"

buttonPlace = [300, 200]
buttonSpace = 3
buttonHeight = 20

windowSize = [1920, 1080]
workingArea = {"x0" : 0, "x1" : 100, "y0" : 0, "y1" : 100}
workingAreaColor = (0, 255, 0)
workingAreaThickness = 2

cooldownTime = 0
```

Dies ist die Konfigurationsdatei von Stamina. Dort können verschiedene Daten verändert werden. `app-name` bezeichnet den Namen des Programms. `min_area` ist die Mindestanzahl an Pixeln, die ein Marker auf dem Bild einnehmen muss, um als solcher erkannt zu werden. `camera_port` gibt den Port der zu verwendenden Kamera ein, während `fps` die maximale Bildrate bezeichnet.

Mit `dshow` kann man toggeln, ob der Parameter DShow verwendet werden soll oder nicht (Genauere Erläuterungen zu DShow finden sich unter [Offenes Problem DShow](#offenes-problem-dshow).

Mit font, `textSize`, `textColor` und `textThickness` kann man Eigenschaften der Schrift des GUI verändern. `font = 0` ist die Standardschriftart in OpenCV. `MirrorMode` toggelt, ob die das Bild gespiegelt werden soll, was bei Beamern nützlich sein kann.

`usePlts` und `newPlts` werden zur Berechnung der Spline eingesetzt, wobei `usePlts` die Anzahl der tatsächlich erkannten Markerzentren angibt, die in die Berechnung einfließen sollen und `newPlts` die Menge der dazwischen (auf den Spline) gesetzten Punkte.

`capturedPoint` bezeichnet die echten Markerzentren, `curvePoint` die generierten, `checkedPoint` die zum Scoring herangezogenen Punkte und `waypoint` die Waypoints. Jeweils bedeuten `Color` Farbe, `Size` Radius und `Thickness` bezeichnet die Dicke des Ringes. Ist `Thickness` = -1, wird der Kreis ausgefüllt.

`txtOffset` bezeichnet den Offset des Textes, `challengePath` und `colorsPath` die Dateispeicherorte für die die Farben und Level.

Die Parameter `buttonPlace`, `buttonSpace” und `buttonheight” treten mit Version 2 in Kraft. Sie bestimmen das Menü. Diese Funktion basiert darauf, dass ein virtueller Kasten mit den Maßen `ButtonPlace` generiert wird, in dem die zur Koordination notwendigen Knöpfe mit der Länge `buttonheight` im Abstand `buttonSpace` platziert werden. Dies erlaubt auch im Graphical User Interface ein hohes Maß an Flexibilität.

`cooldownTime` ist für schwächere Geräte gedacht. In dieser Variablen kann man in allen Threads eine Verzögerung einbauen, um eine geringere Leistung zu beanspruchen. Der Wert ist in Sekunden anzugeben.

### Color-Picker

Der Color-Picker ermöglicht es dem User selbstständig die Farben auf die entsprechenden Umgebungsverhältnisse anzupassen. Da der einkommende Farbwert je nach Marker, Licht und Kamera stark schwankt, muss man vor dem Benutzen die Farben kalibrieren. Dafür gibt es ein externes Skript, welches unten eingefügt ist. Aus verschiedenen Gründen (wie Rechenleistung und Übersichtlichkeit) sollte es möglichst kompakt und einfach geschrieben sein. Um die Farben zu kalibrieren, muss man den Color-Picker zunächst öffnen, woraufhin fünf Fenster erscheinen: Auf dem Hauptfenster sind mehrere Trackbars zu sehen, in denen bei Hue, Saturation und Value jeweils einen Minimal- und einen Maximalwert einstellen kann. Außerdem öffnen sich Fenster mit der unbearbeiteten Kameraansicht und mit einer stark gesättigten Kameraansicht, bei welcher die Sättigung erhöht ist. Die nächsten beiden sind die wichtigsten: Alle Pixel, welche nicht den Kriterien, die im ersten Fenster eingestellt wurden, entsprechen, werden schwarz gefärbt. Bei einem werden die validen Pixel mit Originaleigenschaften angezeigt, bei dem anderem weiß gefärbt. Ziel der Kalibrierung ist eine Kombination aus den Werten zu finden, welche nahezu ausschließlich die Pixel des zu bearbeitenden Markers markiert, aber trotzdem eine gewisse Toleranz besitzt, sodass die Konfigurationen auch noch bei leicht veränderten Lichtverhältnissen verwendet werden können.

Wenn man `R` druckt, wird der Color-Picker auf die Standardwerte zurückgestellt. Wenn man `S` drückt oder das Fenster schließt, werden die HSV-Werte unter dem eingestellten Namen in der Farbkalibierungsdatei gespeichert. Sollte schon eine Farbe mit dem gleichen Namen dort vorhanden sein, wird diese mit den neuen Werten überschrieben. Um den Color-Picker zu schließen, ohne die Werte speichern zu wollen, muss man dafür nur `C` drücken.

### Marker

Die Marker sind ein essenzieller Bestandteil des Projekts, da sie der Kamera (dem Programm) vermitteln, wo sich verschiedene Körperteile befinden. Sie müssen deswegen bei verschiedenem Licht eine möglichst konstante Farbe beibehalten, welche sich von anderen Markern und dem Hintergrund gut abheben muss. Sie dürfen auch nicht verrutschen, da ansonsten die gesamte Bewegungserkennung ad absurdum geführt würde. Beispielhafte Positionen der Marker sind: Kopf, Schulter, Ellenbogen, Hände, Torso, Hüfte, Knie, Fuß 

Dafür lassen sich farbige Bänder verwenden, welche um die entsprechenden Körperteile gewickelt werden. Sie sollten matt sein, um eine höhere Sicherheit in Bezug auf die Farberkennung zu gewährleisten, wobei dies auch durch gute Lichtverhältnisse ausgeglichen werden kann, und gegebenenfalls dehnbar, um einen angenehmen Tragekomfort zu ermöglichen.

Um eine hohe Zuverlässigkeit zu garantieren, sollten etwa 8cm breite Bänder genommen werden, wobei dies nur bei schlechter Kamera oder Lichtverhältnissen notwendig ist. Prinzipiell lassen sich jedoch mit dem Color-Picker die meisten Stoffbänder verwenden.

Dieser Aspekt ist in der Hinsicht wertvoll, dass es kaum Vorbereitung erfordert und somit deutlich einfacher und billiger ist als die meisten Fitnesstrainer. Jene benötigen einiges an Platz, kosten viel Geld und passen optisch möglicherweise nicht zu der sonstigen Ausstattung. Stamina benötigt lediglich eine Kamera, einen Laptop oder PC und einige farbige Gegenstände, die sich an den Extremitäten befestigen lassen. Man muss nur einmal etwas Platz schaffen, wobei nur ein paar Quadratmeter benötigt werden, das Programm öffnen und kann dann mit dem interaktiven Workout loslegen.

### Klassen

Änderungen Version 1.0.2:

In der ersten Version von Stamina (1.0.1) enthielt der GUI (Graphical User Interface) Thread noch sowohl die Bildverarbeitung an sich, die GUI Bearbeitung als auch den Mausinput. Dies hatte den Nachteil, dass der Mauszustand nur relativ selten abgefragt wurde, da das UI und die Bildverarbeitung viel Rechenleistung und -zeit benötigen. In Version 1.0.2 wurde die Bildberechnung in einen weiteren Thread ausgelagert. Der ursprüngliche GUI Thread enthält jetzt nur noch die Anzeige und die Mauserkennung. Dieser fragt mit einer bestimmten Frequenz das verarbeitete Bild vom Bildverarbeitungsthread ab und fügt dazu das GUI hinzu, da eine ständige Abfrage ineffizient wäre. Währenddessen wird ständig der Mauszustand abgefragt. Dies führt zu einer höheren Performance in Bezug auf das UI.

### Performance-Optimierung

Als wir begannen, die Bilder intensiv zu verarbeiten, stellten wir fest, dass unser gesamtes Programm deutlich verlangsamt wurde. Die wohl größte Verlangsamung war auf die begrenzte Framerate der Kamera zurückzuführen, die dazu führte, dass alle anderen Funktionen auf neue Bilder warten mussten, bevor sie beginnen konnten zu arbeiten. Um dieses Problem zu beheben, begannen wir, für alle Tasks, welche theoretisch problemlos gleichzeitig ablaufen können, einen neuen Thread zu schreiben. So wandelten wir die App in zahlreiche Unterprogramme um, die es modernen Prozessoren ermöglichen, diese mithilfe von [Multithreading][6] parallel auszuführen. So muss die Bildverarbeitung beispielsweise nicht darauf warten, dass die Kamera ein neues Bild liefert, sondern kann das letzte verarbeiten, während ein neues aufgenommen wird. Auch wird das Bild, welches der User sieht, deutlich häufiger erneuert, als die Bilder verarbeitet werden, ohne andere Threads zu verlangsamen.

### Offenes Problem DShow

Ein noch nicht gelöstes Problem unseres Hauptprogramms ist DShow. Am Anfang unseres Programms muss die Videoübertragung der Webcam gestartet werden. Dies erfolgt über die Funktion VideoCapture. Allerdings benötigt das Programm ohne den Parameter DShow etwa eine Minute um zu starten. Nach einer Recherche und dem Hinzufügen lässt sich das Programm zwar sofort starten, die Bildrate ist allerdings auf 30 fps begrenzt. DShow ist die Abkürzung für DirectShow, einer Videoschnittstelle von Microsoft. Nach unserem momentanen Wissenstand sind auf der Webcam mehrere Schnittstellen möglich, aber die Begrenzung je nach Schnittstelle sind unterschiedlich, was die niedrigere Bildrate erklären würde. Eine mögliche Erklärung für die längere ist die Aufrufhierarchie von OpenCV oder der Aufbau eines Übertragungskanals von DShow zu der optimalen Kameraschnittstelle, allerdings gibt es keinerlei Verzögerung während der Laufzeit des eigentlichen Programmes selbst. Aus diesem Grund haben wir momentan eine Variable in der Konfigurationsdatei angelegt, mit der man zwischen einer höheren Bildrate und einer schnelleren Startzeit wählen kann. Je nach Hardware können sich die Auswirkungen von DShow aber ganz unterschiedlich verhalten, weshalb der User das für sich selbst entscheiden kann. In einer späteren Version von Stamina ist dieses Problem möglicherweise behoben.

## Ergebnis

Das Ergebnis unserer Forschung ist die erste Version unserer App `Stamina`, welche unter www.stamina.dev/download heruntergeladen werden kann. Dort ist der Installer für die kompilierte Version zu finden. Der Klartext ist und wird nicht verfügbar sein. Der Installer ist ein weltweiter Marktführer und sehr zuverlässig. Dieser ist in Deutsch und Englisch verfügbar. Nachdem man sich diesen auf der unserer offiziellen Website herunter hat, führt man ihn aus und geht durch das klassische Installationsverfahren. Stamina kann man entweder direkt als exe oder durch die Desktopverknüpfung ausführen. Die Farben, Level und die Konfigurationsdatei sind im Installationsordner zu finden.

Das Programm läuft unter Windows.

## Ergebnisdiskussion

Ziel unserer Forschung war es, eine App zu entwickeln, welche den User zu mehr Bewegung animiert.

Mit der Fertigstellung der ersten Version von Stamina haben wir dieses Ziel erreicht und selbst sehr viel Erfahrung und neues Wissen daraus mitgenommen. Mit unserer Forschung im Bereich der Bewegungserkennung und -zuordnung gelang es uns, wichtige Erkenntnisse zu erlangen. Probleme und Fragen während der Programmierung lösten wir durch Internetrecherchen, bei denen wir uns hauptsächlich an Diskussionen in Online-Foren beteiligten und auf Erfahrungen der Community zurückgriffen.

Jeder aus unserem Team hatte während der Entwicklung Aufgaben, welche jeder gewissenhaft erfüllte. So schrieb ich (Kevin) das Programm, während Lukas die verschiedenen Levels erstellte und Daniel sich um Hardware-Aspekte, wie Recherche bezüglich geeigneter Marker, kümmerte.

Die Weiterentwicklungsmöglichkeiten unseres Programmes sind nahezu grenzenlos: Von einigen Vereinfachungen bei der Bedienung über die Möglichkeit, einen Multiplayer-Modus hinzuzufügen bis hin zur Umwandlung in eine App für Smartphones ist mit Stamina alles möglich.

## Zusammenfassung

Ein wichtiger Aspekt von Stamina ist die Flexibilität. Das Ziel war eine Fitnessapp für möglichst viele User mit möglichst hoher Flexibilität zu entwickeln. Dies wird vor allem durch die Konfigurationsdatei und den Color Picker realisiert. Da es keine KI beinhaltet, verbraucht Stamina relativ wenig Rechenleistung.

Auf unserer Website, auf der man Stamina auch herunterladen kann, können wir auch Materialien für die User wie beispielsweise eine Bedienungsanleitung hochladen.

Da wir kein verifizierter Herausgeber sind, kann es zu Interferenzen mit dem Antivirenscanner kommen. In diesem Fall muss man dem Installer beziehungsweise Stamina die entsprechenden Berechtigungen geben. Sollte Windows Defender SmartScreen die App blockieren, muss man auf `More Infos` oder `Weitere Informationen` klicken, worauf man dann auf `Run Anyway` oder `Trotzdem Ausführen` klicken kann. Daraufhin kann man Stamina benutzten.

In dem Ordner, den der Installer installiert hat, ist auch der Color-Picker zu finden. Bevor man das Programm nutzen kann, muss man mit ihm zuerst einige Farben kalibrieren. Wie das geht, steht in der Bedienungsanleitung.

Übliche Fehler wie beispielsweise Simultanprozesse sind zu vermeiden.

Dies ist der Link für die Bedienungsanleitung.

## Quellen- und Literaturverzeichnis

### Verwendung fremder Module

Unsere App nutzt die Python-Module OpenCV (Funktionen für die Kamera) und NumPy (Mathematische Funktionen).

## Unterstützungsleistungen

Schule Birklehof e. V. (durch Irina Küsters): Logitech StreamCam

---

Text: **[Kevin Kretz](https://www.thekevinkretz.com "Homepage von Kevin Kretz"), Daniel Meiborg**


[comment]: #(Verweise)

[1]: https://de.wikipedia.org/wiki/Mesolimbisches_System
[2]: https://de.wikipedia.org/wiki/HSV-Farbraum
[3]: https://de.wikipedia.org/wiki/Spline
[4]: https://de.wikipedia.org/wiki/Polynom
[5]: https://de.wikipedia.org/wiki/K%C3%BCnstliches_neuronales_Netz
[6]: https://de.wikipedia.org/wiki/Multithreading