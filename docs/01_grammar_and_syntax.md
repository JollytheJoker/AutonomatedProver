# 01. Grammatik und Syntax

## 1. Motivation
Um logische Aussagen über alle Themengebiete formel richtig abzubilden, müssen wir Bausteiene katorisieren.
Wir unterteilen hierbei in Funktionen, Mengen und Variablen.

## 2. Formale Definition
> **Definition (Mathematisches Objekt)** <br>
> Ein mathematisches Objekt ist ein Tuple $(\mathcal{T}, \mathcal{B}, \mathcal{M}, \mathcal{Q}, \mathrm{id})$, wobei
> 1. **Typ $(\mathcal{T})$:** Entweder *Urmenge* $(\mathscr{U})$, *Menge* $(\mathscr{M})$, *Funktion* $(\mathscr{F})$, *Variable* $(\mathscr{V})$. Diese bestimmen die Weitere Form des Tupels.
> 2. **Bindungsbedingung $(\mathcal{B}): $** Alle Mengen, Funktionen & Variablen müssen durch Bindungsbedingungen an Urmengen/Mengen gebunden sein. Diese definieren den Raum auf dem sie operieren können. Urmengen, besitzen keine Bindugnsbedingung. Die Bindungsbedingungen sind ein Tupel aus (Ur-)mengen
>   * Für eine Menge enthält das Tupel ein Tupel aus einer beliebigen Menge an (Ur-)mengen. Strukturell kann diese als Obermenge betrachtet werden, von welcher die Menge eine Teilmenge ist.
>   * Das $\mathcal{B}$-Tupel für Element ist ebenfalls genau der Größe 1. Analog ist hier ein Element aus seiner Obermenge
>   * Für eine Funktion gilt $\mathcal{B}=(U, B)$, wobei $U$ das Urbild und $B$ das Bild der Funktion ist.
> 3. **Mathematische Bedingungen $(\mathcal{M})$:**  Ist die Menge aller weitern *Ausdürcke* $P$ die unter Einsatz des Objekts wahr sind
> 4. **Quator $(\mathcal{Q})$:** Geben die Anzahl von Objekten an. Wir nutzen 
>   * $\forall$: Für alle Objekte die diese Bindungsgedingung erfüllen
>   * $\exists$: Es existiert mind. ein Objekte, welches eine Bindungsbedingung erfüllt
>   * $D$: Definiere ein Objekt, welches seine Bindungsbedingung erfüllt (alle Urmengenen müssen definiert werden)
> 5. **Identifikator $(\mathrm{id}): $** Eine Zahl, welche zur Unterscheidung verschiedener mathematischer Objekter gleicher Werte in $\mathcal{T}, \mathcal{B}, \mathcal{M}, \mathcal{Q}$ dient.

Formal müsste man zunächst mathematisch bedingungslose Objekte (also $\mathcal{M}=\{\}$) um damit Ausdrücke wie später zu definieren, um dann Objekte mit Ausdrücken zu definieren. Jedoch können diese in eine Menge eingebettet werden.

## 3. Übersicht der mathematischen Objekte
In der Implementierung definieren mathematische objekte als statische Objekte mit eigenschaften $(\mathcal{B}, \mathcal{M}, \mathcal{Q}, \mathrm{id})$; für lesbarkeit fürgen wir das Attribut eines Assoziations-String hinzu. Der $\mathcal{T}$ wird als Vererbung auf vier unter Klassen verteilt. Ferner definieren wir potenzmengen als weiteres Objekt, um Mengen von Mengen effizient abbilden zu können.

## 4. Beispiel
Wir assozierien & definieren $(\mathscr{U}, \{\}, \{\}, D, 0)$ mit dem Namen X als Urmenge. Ferner sei $(\mathscr{U}, \{\}, \{\}, D, 1)$ mit Y assoziert. Sei nun A mit $(\mathscr{M}, ((\mathscr{U}, \{\}, \{\}, D, 0)), \{\}, 0)$ assoziert (es ist also $A \subseteq X$). Eine Funktion $f: A\rightarrow Y$ ist dann $(\mathscr{F}, ((\mathscr{M}, ((\mathscr{U}, \{\}, \{\}, D, 0)), \{\}, 0), (\mathscr{U}, \{\}, \{\}, D, 1)), \{\}, 0)$, oder (für lesbarkeit) $(\mathscr{F}, (A, Y), \{\}, 0)$.
