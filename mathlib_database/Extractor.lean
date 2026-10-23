import Lean
import Mathlib

open Lean Json

-- 1. Hilfsfunktion (unverändert)
partial def exprToJson : Expr → Json
  | Expr.bvar idx =>
      mkObj [("type", "bvar"), ("index", toJson idx)]
  | Expr.const name _ =>
      mkObj [("type", "const"), ("name", toJson name.toString)]
  | Expr.app fn arg =>
      mkObj [("type", "app"), ("fn", exprToJson fn), ("arg", exprToJson arg)]
  | Expr.lam name domain body _ =>
      mkObj [("type", "lam"), ("var", toJson name.toString), ("domain", exprToJson domain), ("body", exprToJson body)]
  | Expr.forallE name domain body _ =>
      mkObj [("type", "forallE"), ("var", toJson name.toString), ("domain", exprToJson domain), ("body", exprToJson body)]
  | Expr.sort _ =>
      mkObj [("type", "sort")]
  | Expr.letE name type val body _ =>
      mkObj [("type", "letE"), ("var", toJson name.toString), ("expr_type", exprToJson type), ("val", exprToJson val), ("body", exprToJson body)]
  | Expr.mdata _ expr =>
      exprToJson expr
  | Expr.lit (Literal.natVal v) =>
      mkObj [("type", "lit"), ("val", toJson v)]
  | Expr.lit (Literal.strVal s) =>
      mkObj [("type", "lit"), ("val", toJson s)]
  | _ =>
      mkObj [("type", "unsupported")]

-- 2. Streaming-Logik
def extractMathlib : CoreM Unit := do
  let env ← getEnv
  let mut count := 0

  -- Datei-Handle im Schreib-Modus öffnen (Stream)
  let handle ← IO.FS.Handle.mk "mathlib_dump.jsonl" IO.FS.Mode.write

  for (name, constInfo) in env.constants.toList do
    if name.toString.startsWith "Mathlib" then
      let declJson := mkObj [
        ("name", toJson name.toString),
        ("type", exprToJson constInfo.type)
      ]
      -- Schreibt das JSON für genau ein Theorem und macht einen Zeilenumbruch
      handle.putStrLn declJson.compress
      count := count + 1

  IO.println s!"Gefunden und exportiert: {count} Mathlib-Einträge."

-- 3. Hauptprogramm
def main : IO Unit := do
  IO.println "Initialisiere Pfade..."
  initSearchPath (← Lean.findSysroot)

  IO.println "Lade Mathlib in den Speicher (das dauert 1-3 Minuten)..."
  let env ← importModules #[{ module := `Mathlib }] {}

  -- WICHTIG: Rekursionstiefe extrem erhöhen, damit Lean bei tiefen Bäumen nicht abbricht
  let ctx : Core.Context := {
    fileName := "Extractor",
    fileMap := FileMap.ofString "",
    maxRecDepth := 100000
  }
  let state : Core.State := { env := env }

  IO.println "Starte Extraktion (Streaming in .jsonl Datei)..."
  let _ ← extractMathlib.toIO ctx state
  IO.println "Fertig! 'mathlib_dump.jsonl' wurde erfolgreich erstellt."