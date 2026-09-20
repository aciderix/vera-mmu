/**
 * Ce que la fenêtre montre de ce qu'elle vient de faire.
 *
 * **Deux défauts mesurés à l'écran**, en pilotant l'AppImage `v0.1.0-rc.5` sous écran virtuel.
 *
 * Le premier n'était pas celui que j'avais annoncé. J'avais écrit que la fenêtre « avalait les
 * refus » : c'est faux, elle les affiche — dans un bandeau placé tout en bas d'une page haute de
 * plusieurs écrans. En cliquant « Compiler le preview » au milieu de la page, le motif
 * apparaissait hors de vue, et le bouton semblait ne rien faire. Le message existait ; personne
 * ne pouvait le lire. La correction épinglée ici est donc celle du placement, pas celle de la
 * transmission — et c'est aussi pour cela que le premier diagnostic ne valait rien : il aurait
 * conduit à réparer une chaîne qui fonctionnait.
 *
 * Le second est réel et distinct : après « Confirmer l'installation MCP », trois fichiers sont
 * écrits hors de `.vera-mmu/` et la fenêtre n'en nommait aucun. « L'opération a été contrôlée
 * localement par VERA » dit que rien n'a débordé — vrai, et insuffisant pour un produit dont la
 * thèse est la traçabilité.
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { installedPaths } from "./DesktopConsole";

const lire = (nom: string) => readFileSync(fileURLToPath(new URL(nom, import.meta.url)), "utf8");

describe("les chemins écrits par l'installation", () => {
  it("nomme les trois cibles que le preview déclare, dans son ordre", () => {
    const preview = {
      preview: {
        mcpPath: "/projet/.mcp.json",
        settingsPath: "/projet/.claude/settings.json",
        statePath: "/projet/.vera-mmu/generated/claude-code-local-install.json",
      },
    };
    expect(installedPaths(preview)).toEqual([
      "/projet/.mcp.json",
      "/projet/.claude/settings.json",
      "/projet/.vera-mmu/generated/claude-code-local-install.json",
    ]);
  });

  it("accepte aussi la forme sans enveloppe, que le bridge rend selon l'opération", () => {
    expect(installedPaths({ mcpPath: "/p/.mcp.json" })).toEqual(["/p/.mcp.json"]);
  });

  it("n'invente aucun chemin quand le preview n'en déclare pas", () => {
    // Nommer un fichier qu'on n'a pas écrit serait la faute symétrique de le taire.
    expect(installedPaths(null)).toEqual([]);
    expect(installedPaths({})).toEqual([]);
    expect(installedPaths({ preview: { mcpPath: 42, settingsPath: "  " } })).toEqual([]);
  });
});

describe("le bandeau de message", () => {
  it("reste visible là où l'action a lieu, et non au pied de la page", () => {
    const styles = lire("./styles.css");
    const bandeau = styles.slice(styles.indexOf(".notice {"), styles.indexOf(".notice b {"));
    expect(bandeau).toContain("position: sticky");
    expect(bandeau).toContain("bottom:");
  });

  it("rapporte le détail rendu par l'action plutôt qu'une formule fixe", () => {
    const source = lire("./DesktopConsole.tsx");
    expect(source).toContain("const resultat = await work();");
    expect(source).toContain("typeof resultat === \"string\"");
    // Et l'installation s'en sert pour nommer ce qu'elle a écrit.
    expect(source).toContain("`Écrit : ${ecrits.join(\", \")}.`");
  });
});

describe("les lignes de parcours", () => {
  it("place chaque rôle dans sa colonne, y compris sans index", () => {
    // Les hachages de §34 et les alertes n'ont pas d'index : sans placement explicite, le
    // libellé tombait dans les 34px réservés au numéro et la valeur se superposait au texte.
    const styles = lire("./styles.css");
    expect(styles).toContain(".journey-step > .journey-label { grid-column: 2;");
    expect(styles).toContain(".journey-step > .journey-state { grid-column: 3;");
    expect(styles).toContain(".journey-step > .journey-index { grid-column: 1; }");
  });

  it("laisse un libellé long se replier au lieu de déborder", () => {
    const styles = lire("./styles.css");
    const regle = styles.slice(styles.indexOf(".journey-step > .journey-label"));
    expect(regle.slice(0, 160)).toContain("overflow-wrap: anywhere");
  });
});
