/** Console de contrôle VERA : encre calme, verdigris pour les signaux contrôlés, étapes asymétriques et refus visibles. */
import { useCallback, useState } from "react";
import { desktopApi, type JsonObject } from "./desktop-api";
import { asChoices, asList, asRefusals, isConfirmable } from "./contract";
import { countByClass, readPromotion, readRequirements } from "./gate";
import { policyValueText, readPolicyLines } from "./policy";
import { readIntegrations, readInvalidated, readSections } from "./resume";
import { blockingAlerts, readAlerts, readCounts, readHashes } from "./preview";
import { completedCount, panelAccess, readJourney, type PanelId } from "./journey";

type AgentProfile = { id: string; label: string; adapter: string; coverage: string; mode: string };
type Notice = { tone: "neutral" | "success" | "error"; title: string; detail: string };

const templates = ["software", "data", "research", "documentation", "game", "hardware"];

function isRecord(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asProfiles(value: unknown): AgentProfile[] {
  if (!isRecord(value) || !Array.isArray(value.profiles)) return [];
  return value.profiles.filter(isRecord).map((profile) => ({
    id: typeof profile.id === "string" ? profile.id : "",
    label: typeof profile.label === "string" ? profile.label : "Profil inconnu",
    adapter: typeof profile.adapter === "string" ? profile.adapter : "",
    coverage: typeof profile.coverage === "string" ? profile.coverage : "UNKNOWN",
    mode: typeof profile.mode === "string" ? profile.mode : "",
  })).filter((profile) => profile.id.length > 0);
}

function getHash(value: JsonObject | null, key = "preview_hash"): string | null {
  return value && typeof value[key] === "string" ? value[key] : null;
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : "Opération locale refusée.";
}

/** A panel whose journey step is blocked shows the Core's reason instead of its controls. */
function Locked({ reason }: { reason: string }) {
  return <p className="panel-locked"><b>ÉTAPE BLOQUÉE</b> {reason}</p>;
}

function Evidence({ label, state }: { label: string; state: string }) {
  return <span className={`evidence ${state === "READY" || state === "OBSERVED" ? "evidence-good" : ""}`}>{label} · {state}</span>;
}

export function DesktopConsole() {
  const [project, setProject] = useState<string | null>(null);
  const [scan, setScan] = useState<JsonObject | null>(null);
  const [journey, setJourney] = useState<JsonObject | null>(null);
  const [profiles, setProfiles] = useState<AgentProfile[]>([]);
  const [template, setTemplate] = useState("software");
  const [projectId, setProjectId] = useState("my-project");
  const [projectName, setProjectName] = useState("Mon projet");
  const [agentProfileId, setAgentProfileId] = useState("generic-mcp");
  const [initPreview, setInitPreview] = useState<JsonObject | null>(null);
  const [generation, setGeneration] = useState<JsonObject | null>(null);
  const [installPreview, setInstallPreview] = useState<JsonObject | null>(null);
  const [doctor, setDoctor] = useState<JsonObject | null>(null);
  const [projectDoctor, setProjectDoctor] = useState<JsonObject | null>(null);
  const [migrationStatus, setMigrationStatus] = useState<JsonObject | null>(null);
  const [memorySync, setMemorySync] = useState<JsonObject | null>(null);
  const [projectStatus, setProjectStatus] = useState<JsonObject | null>(null);
  const [projectDocumentation, setProjectDocumentation] = useState<JsonObject | null>(null);
  const [profileId, setProfileId] = useState("");
  const [profileName, setProfileName] = useState("");
  const [profileDomain, setProfileDomain] = useState("software");
  const [profileDescription, setProfileDescription] = useState("");
  const [profileRebindPreview, setProfileRebindPreview] = useState<JsonObject | null>(null);
  const [profileRebindConfirmed, setProfileRebindConfirmed] = useState(false);
  const [profileRecoveryPreview, setProfileRecoveryPreview] = useState<JsonObject | null>(null);
  const [profileRecoveryConfirmed, setProfileRecoveryConfirmed] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [capabilityId, setCapabilityId] = useState("project-check");
  const [capabilityName, setCapabilityName] = useState("Project check");
  const [capabilityKind, setCapabilityKind] = useState("CHECK");
  const [capabilityVersion, setCapabilityVersion] = useState("1.0.0");
  const [capabilityDescription, setCapabilityDescription] = useState("Contrôle déclaré du projet.");
  const [capabilityRunner, setCapabilityRunner] = useState("EVIDENCE_FIELDS");
  const [capabilityPolicy, setCapabilityPolicy] = useState("READ_ONLY");
  const [capabilityTimeout, setCapabilityTimeout] = useState("120");
  const [capabilityInputs, setCapabilityInputs] = useState("");
  const [capabilityOutputs, setCapabilityOutputs] = useState("verdict");
  const [capabilityArtifacts, setCapabilityArtifacts] = useState("");
  const [capabilityValidator, setCapabilityValidator] = useState("EVIDENCE_FIELDS");
  const [capabilityConfirmationRequired, setCapabilityConfirmationRequired] = useState(false);
  const [capabilityGateBacked, setCapabilityGateBacked] = useState(true);
  const [capabilityOptions, setCapabilityOptions] = useState<JsonObject | null>(null);
  const [capabilityPreview, setCapabilityPreview] = useState<JsonObject | null>(null);
  const [capabilityConfirmed, setCapabilityConfirmed] = useState(false);
  const [gateId, setGateId] = useState("");
  const [gateMode, setGateMode] = useState("ALL");
  const [gateMinimum, setGateMinimum] = useState("1");
  const [gatePolicyPreview, setGatePolicyPreview] = useState<JsonObject | null>(null);
  const [gatePolicyConfirmed, setGatePolicyConfirmed] = useState(false);
  const [gateStructureId, setGateStructureId] = useState("");
  const [gateWorkItemId, setGateWorkItemId] = useState("");
  const [gatePrimaryEvidenceId, setGatePrimaryEvidenceId] = useState("");
  const [gateRequirementEvidenceIds, setGateRequirementEvidenceIds] = useState("");
  const [gateStructurePreview, setGateStructurePreview] = useState<JsonObject | null>(null);
  const [gateStructureConfirmed, setGateStructureConfirmed] = useState(false);
  const [gateReport, setGateReport] = useState<JsonObject | null>(null);
  const [policyOptions, setPolicyOptions] = useState<JsonObject | null>(null);
  const [policyEdits, setPolicyEdits] = useState<Record<string, string>>({});
  const [policyPreview, setPolicyPreview] = useState<JsonObject | null>(null);
  const [policyConfirmed, setPolicyConfirmed] = useState(false);
  const [resumeOptions, setResumeOptions] = useState<JsonObject | null>(null);
  const [resumeSections, setResumeSections] = useState("");
  const [resumeIntegrations, setResumeIntegrations] = useState("");
  const [resumeBudget, setResumeBudget] = useState("");
  const [resumePreview, setResumePreview] = useState<JsonObject | null>(null);
  const [resumeConfirmed, setResumeConfirmed] = useState(false);
  const [mcpPreview, setMcpPreview] = useState<JsonObject | null>(null);
  const [initConfirmed, setInitConfirmed] = useState(false);
  const [stageConfirmed, setStageConfirmed] = useState(false);
  const [installConfirmed, setInstallConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice>({ tone: "neutral", title: "Prêt à observer", detail: "Choisissez un dossier : rien n’est écrit à cette étape." });

  const action = useCallback(async (title: string, work: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await work();
      setNotice({ tone: "success", title, detail: "L’opération a été contrôlée localement par VERA." });
    } catch (error) {
      setNotice({ tone: "error", title: "Action refusée", detail: errorText(error) });
    } finally {
      setBusy(false);
    }
  }, []);

  const selectProject = () => action("Projet associé", async () => {
    const result = await desktopApi.selectProject();
    const root = typeof result.root === "string" ? result.root : null;
    const report = isRecord(result.scan) ? result.scan : null;
    setProject(root);
    setScan(report);
    const agents = await desktopApi.agents();
    setProfiles(asProfiles(agents));
    setInitPreview(null);
    setGeneration(null);
    setInstallPreview(null);
    setDoctor(null);
    setProjectDoctor(null);
    setMigrationStatus(null);
    setMemorySync(null);
    setProjectStatus(null);
    setProjectDocumentation(null);
    setProfileRebindPreview(null);
    setProfileRebindConfirmed(false);
    setProfileRecoveryPreview(null);
    setProfileRecoveryConfirmed(false);
    setInitialized(false);
    setCapabilityOptions(null);
    setCapabilityPreview(null);
    setCapabilityConfirmed(false);
    setGatePolicyPreview(null);
    setGatePolicyConfirmed(false);
    setGateStructurePreview(null);
    setGateStructureConfirmed(false);
    setGateReport(null);
    setPolicyOptions(null);
    setPolicyEdits({});
    setPolicyPreview(null);
    setPolicyConfirmed(false);
    setResumeOptions(null);
    setResumeSections("");
    setResumeIntegrations("");
    setResumeBudget("");
    setResumePreview(null);
    setResumeConfirmed(false);
    setMcpPreview(null);
    setInitConfirmed(false);
    setStageConfirmed(false);
    setInstallConfirmed(false);
  });

  const scanProject = () => action("Scan mis à jour", async () => setScan(await desktopApi.scanProject()));
  const refreshJourney = () => action("Parcours relu", async () => setJourney(await desktopApi.wizardState()));
  const createInitializationPreview = () => action("Preview d’initialisation produit", async () => setInitPreview(await desktopApi.initializationPreview(template, projectId, projectName)));
  const applyInitialization = () => action("Initialisation project-local appliquée", async () => {
    const hash = getHash(initPreview);
    if (!hash) throw new Error("Aucun preview d’initialisation disponible.");
    await desktopApi.initializationApply(hash, initConfirmed);
    setInitPreview(null);
    setInitialized(true);
    setProjectStatus(await desktopApi.projectStatus());
  });
  const readProjectDocumentation = () => action("Documentation VERA compilée", async () => setProjectDocumentation(await desktopApi.projectDocumentation()));
  const createProfileRebindPreview = () => action("Preview de rebind Profile produit", async () => setProfileRebindPreview(await desktopApi.profileRebindPreview(profileId, profileName, profileDomain, profileDescription)));
  const applyProfileRebind = () => action("Project Profile rebondi", async () => { const hash = getHash(profileRebindPreview); if (!hash) throw new Error("Aucun preview de rebind Profile disponible."); await desktopApi.profileRebindApply(hash, profileRebindConfirmed); setProfileRebindPreview(null); setProfileRebindConfirmed(false); setProjectStatus(await desktopApi.projectStatus()); });
  const createProfileRecoveryPreview = () => action("Preview de reprise Profile produit", async () => setProfileRecoveryPreview(await desktopApi.profileRebindRecoveryPreview()));
  const applyProfileRecovery = () => action("Rebind Profile repris", async () => { const hash = getHash(profileRecoveryPreview); if (!hash) throw new Error("Aucun preview de reprise Profile disponible."); await desktopApi.profileRebindRecoveryApply(hash, profileRecoveryConfirmed); setProfileRecoveryPreview(null); setProfileRecoveryConfirmed(false); setDoctor(await desktopApi.doctor(agentProfileId)); setProjectStatus(await desktopApi.projectStatus()); });
  const readCapabilityOptions = () => action("Choix de contrat relus", async () => setCapabilityOptions(await desktopApi.capabilityOptions()));
  const createCapabilityPreview = () => action("Preview de contrat produit", async () => setCapabilityPreview(await desktopApi.capabilityPreview({
    identifier: capabilityId,
    name: capabilityName,
    description: capabilityDescription,
    kind: capabilityKind,
    version: capabilityVersion,
    runner: capabilityRunner,
    policy: capabilityPolicy,
    timeoutSeconds: capabilityTimeout.trim() === "" ? null : Number(capabilityTimeout),
    inputs: asList(capabilityInputs),
    outputs: asList(capabilityOutputs),
    artifacts: asList(capabilityArtifacts),
    validator: capabilityValidator,
    yieldsProof: false,
    confirmationRequired: capabilityConfirmationRequired,
    gateBacked: capabilityGateBacked,
  })));
  const applyCapability = () => action("Contrat de capability déclaré", async () => {
    const hash = getHash(capabilityPreview);
    if (!hash) throw new Error("Aucun preview de capability disponible.");
    await desktopApi.capabilityApply(hash, capabilityConfirmed);
    setCapabilityPreview(null);
    setCapabilityConfirmed(false);
    setProjectStatus(await desktopApi.projectStatus());
  });
  const readResumeOptions = () => action("Contrat de reprise relu", async () => {
    const payload = await desktopApi.resumeOptions();
    setResumeOptions(payload);
    setResumeSections(readSections(payload).map((item) => `${item.id}=${item.required ? "required" : "optional"}`).join(", "));
    setResumeIntegrations(readIntegrations(payload).enabled.join(", "));
    setResumePreview(null);
  });
  const createResumePreview = () => action("Preview de reprise produit", async () => setResumePreview(await desktopApi.resumePreview({
    template: null,
    sections: asList(resumeSections).map((entry) => {
      const [id, flag] = entry.split("=");
      return { id: (id ?? "").trim(), required: (flag ?? "required").trim() !== "optional" };
    }),
    maxResumeBytes: resumeBudget.trim() === "" ? null : Number(resumeBudget),
    integrations: asList(resumeIntegrations),
  })));
  const applyResumeEdit = () => action("Contrat de reprise déclaré", async () => {
    const hash = getHash(resumePreview);
    if (!hash) throw new Error("Aucun preview de reprise disponible.");
    await desktopApi.resumeApply(hash, resumeConfirmed);
    setResumePreview(null);
    setResumeConfirmed(false);
    setResumeOptions(await desktopApi.resumeOptions());
  });
  const readPolicyOptions = () => action("Policies relues", async () => { setPolicyOptions(await desktopApi.policyOptions()); setPolicyEdits({}); setPolicyPreview(null); });
  const createPolicyPreview = () => action("Preview de policies produit", async () => setPolicyPreview(await desktopApi.policyPreview(
    Object.fromEntries(Object.entries(policyEdits).map(([name, value]) => [name, readPolicyLines(policyOptions).find((line) => `${line.section}.${line.key}` === name)?.values === null ? asList(value) : value])),
  )));
  const applyPolicyEdit = () => action("Policies déclarées", async () => {
    const hash = getHash(policyPreview);
    if (!hash) throw new Error("Aucun preview de policies disponible.");
    await desktopApi.policyApply(hash, policyConfirmed);
    setPolicyPreview(null);
    setPolicyConfirmed(false);
    setPolicyOptions(await desktopApi.policyOptions());
    setPolicyEdits({});
  });
  const readGateReport = () => action("Gate relue", async () => setGateReport(await desktopApi.gateReport(gateId)));
  const createGatePolicyPreview = () => action("Preview de policy Gate produit", async () => setGatePolicyPreview(await desktopApi.gatePolicyPreview(gateId, gateMode, gateMode === "AT_LEAST" ? Number(gateMinimum) : null)));
  const applyGatePolicy = () => action("Policy Gate déclarée", async () => { const hash = getHash(gatePolicyPreview); if (!hash) throw new Error("Aucun preview de policy Gate disponible."); await desktopApi.gatePolicyApply(hash, gatePolicyConfirmed); setGatePolicyPreview(null); setGatePolicyConfirmed(false); });
  const createGateStructurePreview = () => action("Preview de structure Gate produit", async () => setGateStructurePreview(await desktopApi.gateStructurePreview(gateStructureId, gateWorkItemId, gatePrimaryEvidenceId, gateRequirementEvidenceIds.split(",").map((item) => item.trim()).filter(Boolean))));
  const applyGateStructure = () => action("Structure Gate déclarée", async () => { const hash = getHash(gateStructurePreview); if (!hash) throw new Error("Aucun preview de structure Gate disponible."); await desktopApi.gateStructureApply(hash, gateStructureConfirmed); setGateStructurePreview(null); setGateStructureConfirmed(false); });
  const readMcpPreview = () => action("Preview MCP compilé", async () => setMcpPreview(await desktopApi.mcpPreview(agentProfileId)));
  const generate = () => action("Preview de génération produit", async () => setGeneration(await desktopApi.generation(agentProfileId)));
  const stage = () => action("Runtime VERA préparé", async () => desktopApi.stage(agentProfileId, stageConfirmed));
  const createInstallationPreview = () => action("Preview d’intégration MCP produit", async () => setInstallPreview(await desktopApi.installationPreview(agentProfileId)));
  const applyInstallation = () => action("Configuration MCP project-local appliquée", async () => {
    const hash = getHash(installPreview, "previewHash");
    if (!hash) throw new Error("Aucun preview d’intégration disponible.");
    await desktopApi.installationApply(hash, installConfirmed);
    setInstallPreview(null);
  });
  const refreshProjectStatus = () => action("État du projet actualisé", async () => setProjectStatus(await desktopApi.projectStatus()));
  const runDoctor = () => action("Diagnostic local produit", async () => setDoctor(await desktopApi.doctor(agentProfileId)));
  const runProjectDoctor = () => action("Doctor projet exécuté", async () => setProjectDoctor(await desktopApi.projectDoctor()));
  const readMigrationStatus = () => action("Statut de migration observé", async () => setMigrationStatus(await desktopApi.migrationStatus()));
  const synchronizeMemory = () => action("Synchronisation mémoire contrôlée", async () => setMemorySync(await desktopApi.memorySync()));

  const selectedAgent = profiles.find((profile) => profile.id === agentProfileId);
  const observations = scan && Array.isArray(scan.observations) ? scan.observations.length : 0;
  const journeySteps = readJourney(journey);
  const journeyDone = completedCount(journeySteps);
  const access = (panel: PanelId) => panelAccess(journeySteps, panel);
  const journeyNext = journey && typeof journey.next_step === "string" ? journey.next_step : null;
  const coverageTools = projectStatus && isRecord(projectStatus.coverage) && Array.isArray(projectStatus.coverage.mcp_tools) ? projectStatus.coverage.mcp_tools.length : null;
  const vcsState = projectStatus && isRecord(projectStatus.vcs) && typeof projectStatus.vcs.status === "string" ? projectStatus.vcs.status : "UNKNOWN";

  return <div className="app-shell">
    <aside className="rail">
      <div className="brand"><img src="/vera-mark.png" alt="Symbole VERA" /><div><strong>VERA</strong><span>MMU · DESKTOP</span></div></div>
      <div className="rail-rule" />
      <p className="rail-label">Projet local</p>
      <div className="project-card"><span className="folder-symbol">⌁</span><div><b>{project ? "Projet associé" : "Aucun projet associé"}</b><small>{project ? "RACINE VALIDÉE" : "DIALOGUE NATIF REQUIS"}</small></div></div>
      <nav aria-label="Parcours d’intégration"><p className="rail-label">Parcours contrôlé</p><a href="#observe">01 · Observer</a><a href="#prepare">02 · Préparer</a><a href="#integrate">03 · Intégrer</a><a href="#verify">04 · Vérifier</a></nav>
      <div className="fail-card"><b>FAIL-CLOSED</b><p>Le WebView ne possède aucun accès système générique. VERA refuse les états ambigus.</p></div>
      <small className="version">v0.1.0 · LOCAL APP</small>
    </aside>
    <main>
      <header className="topbar"><div><span className="micro">POSTE DE CONTRÔLE</span><b>Installation MCP project-local</b></div><Evidence label="BRIDGE" state={project ? "READY" : "OFFLINE"} /></header>
      <div className="content">
        <section className="hero" id="observe"><div className="hero-copy"><p className="eyebrow">01 · AUCUNE ÉCRITURE INITIALE</p><h1>Installer avec des <em>règles visibles.</em></h1><p>Choisissez un projet. VERA l’observe sans lire le contenu métier, puis prépare les fichiers MCP nécessaires avant toute confirmation.</p><button className="primary" onClick={selectProject} disabled={busy}>{project ? "Choisir un autre projet" : "Choisir le dossier du projet"}</button></div><img className="hero-art" src="/vera-proof-orbit.png" alt="Fragments VERA convergeant vers un point de preuve" /></section>
        <section className="panel" id="journey"><div className="panel-top"><div><p className="eyebrow">Parcours en dix-huit étapes</p><h2>Savoir où l’on en est, sans le supposer</h2></div><Evidence label="ÉTAPES" state={journeySteps.length ? `${journeyDone}/18 FAITES` : "WAITING"} /></div><p>L’état de chaque étape est <b>dérivé du projet</b>, jamais retenu par cette fenêtre : rouvrir l’application sur un projet à moitié configuré retrouve exactement la même étape. Six étapes ne laissent aucune trace — scanner, détecter, proposer, prévisualiser, valider, diagnostiquer : VERA les déclare non observables plutôt que de prétendre les avoir vues.</p><button className="secondary" onClick={refreshJourney} disabled={!project || busy}>Relire le parcours</button>{journeyNext && <div className="metric"><b>{journeyNext}</b><span>prochaine étape</span></div>}{journeySteps.length > 0 && <ol className="journey">{journeySteps.map((step) => <li key={step.id} className={`journey-step journey-${step.state.toLowerCase()}`}><span className="journey-index">{String(step.index).padStart(2, "0")}</span><span className="journey-label">{step.label}</span><span className="journey-state">{step.state}</span>{step.reason && <small className="journey-reason">{step.reason}</small>}</li>)}</ol>}</section>
        <section className="two-columns" id="prepare"><div className="panel"><div className="panel-top"><div><p className="eyebrow">Observation</p><h2>Scanner sans toucher</h2></div><Evidence label="SCAN" state={scan ? "OBSERVED" : "WAITING"} /></div><p>Le scan identifie seulement des marqueurs structuraux réguliers, dans les quatorze catégories de la spécification. Il ne démarre aucun agent et ne modifie pas votre dossier.</p><div className="metric"><b>{observations}</b><span>observations VERA</span></div><button className="secondary" onClick={scanProject} disabled={!project || busy}>Actualiser le scan</button>{scan && <details><summary>Voir le ScanReport v2</summary><pre>{JSON.stringify(scan, null, 2)}</pre></details>}</div>
          <div className="panel"><div className="panel-top"><div><p className="eyebrow">Initialisation</p><h2>Préparer VERA</h2></div><Evidence label="ÉTAT" state={initialized ? "READY" : "PREVIEW"} /></div><p>Le preview propose uniquement `.vera-mmu/` : profil, playbook et profils d’agents. Rien n’est créé avant votre confirmation.</p><div className="field-grid"><label>Type de projet<select value={template} onChange={(event) => setTemplate(event.target.value)}>{templates.map((item) => <option key={item}>{item}</option>)}</select></label><label>Identifiant<input value={projectId} onChange={(event) => setProjectId(event.target.value)} /></label><label className="wide">Nom du projet<input value={projectName} onChange={(event) => setProjectName(event.target.value)} /></label></div><button className="secondary" onClick={createInitializationPreview} disabled={!project || busy}>Générer le preview</button>{initPreview && <div className="confirmation"><label><input type="checkbox" checked={initConfirmed} onChange={(event) => setInitConfirmed(event.target.checked)} /> J’ai vérifié les fichiers proposés.</label><button className="primary" onClick={applyInitialization} disabled={!initConfirmed || busy}>Confirmer l’initialisation</button><details><summary>Inspecter le preview</summary><pre>{JSON.stringify(initPreview, null, 2)}</pre></details></div>}</div></section>
        <section className="panel"><div className="panel-top"><div><p className="eyebrow">MCP Preview · §34 · étape 14</p><h2>Les chiffres du build, avant de le produire</h2></div><Evidence label="LECTURE" state={mcpPreview ? "COMPILED" : "WAITING"} /></div><p>Chaque nombre et chaque hachage vient du compilateur ; cet écran n’en recalcule aucun — une seconde mesure serait un second avis. <b>Trois des quatre alertes de §34 ne peuvent plus se déclencher</b> : les lots précédents les ont fermées à la déclaration. Elles sont rapportées impossibles avec la règle qui les a fermées, plutôt qu’affichées à zéro comme une rassurance.</p>{!access("integrate").open && <Locked reason={access("integrate").reason} />}<button className="secondary" onClick={readMcpPreview} disabled={!initialized || busy}>Compiler le preview</button>{mcpPreview && <div className="confirmation"><div className="action-grid">{Object.entries(readCounts(mcpPreview)).map(([key, value]) => <div key={key} className="metric"><b>{value === null ? "—" : value}</b><span>{key.replace(/_/g, " ")}</span></div>)}</div><ul className="journey">{readHashes(mcpPreview).map((item) => <li key={item.label} className="journey-step"><span className="journey-label">{item.label}</span><span className="journey-state">{item.value.slice(0, 16)}</span></li>)}</ul>{blockingAlerts(readAlerts(mcpPreview)).length > 0 && <p className="panel-locked"><b>GÉNÉRATION À REVOIR</b> {blockingAlerts(readAlerts(mcpPreview)).length} alerte(s) ERROR levée(s) par le Core.</p>}<ul className="journey">{readAlerts(mcpPreview).map((alert) => <li key={alert.id} className={`journey-step ${alert.status === "RAISED" ? "journey-blocked" : "journey-completed"}`}><span className="journey-label">{alert.severity} · {alert.id}</span><span className="journey-state">{alert.status}</span><small className="journey-reason">{alert.message}{alert.instances.length > 0 ? ` — ${alert.instances.join(", ")}` : ""}</small></li>)}</ul><details><summary>Inspecter le preview</summary><pre>{JSON.stringify(mcpPreview, null, 2)}</pre></details></div>}</section>
        <section className="panel integration" id="integrate"><div className="panel-top"><div><p className="eyebrow">Intégration MCP</p><h2>Associer l’agent, sans configuration cachée</h2></div><Evidence label="ÉCRITURE" state="CONFIRMED ONLY" /></div><p>Le profil d’agent choisit un adapter déclaré par VERA. L’interface ne fournit jamais un adapter ou une commande libre.</p>{!access("integrate").open && <Locked reason={access("integrate").reason} />}<div className="agent-row"><label>Agent Profile<select value={agentProfileId} onChange={(event) => setAgentProfileId(event.target.value)} disabled={profiles.length === 0}>{profiles.map((profile) => <option key={profile.id} value={profile.id}>{profile.label}</option>)}</select></label>{selectedAgent && <div className="coverage"><b>{selectedAgent.coverage}</b><span>{selectedAgent.adapter} · {selectedAgent.mode}</span></div>}</div><div className="action-grid"><div><h3>1. Générer</h3><p>Compile un `GenerationPreview/v1` déterministe.</p><button className="secondary" onClick={generate} disabled={!project || busy || !access("integrate").open}>Générer</button></div><div><h3>2. Préparer le runtime</h3><p>Le staging reste local au runtime VERA.</p><label className="check"><input type="checkbox" checked={stageConfirmed} onChange={(event) => setStageConfirmed(event.target.checked)} /> Confirmer le staging</label><button className="secondary" onClick={stage} disabled={!project || !stageConfirmed || busy}>Préparer</button></div><div><h3>3. Examiner puis installer</h3><p>Le bridge recalcule le preview avant l’écriture.</p><button className="secondary" onClick={createInstallationPreview} disabled={!project || busy}>Voir l’intégration</button></div></div>{generation && <details><summary>GenerationPreview/v1</summary><pre>{JSON.stringify(generation, null, 2)}</pre></details>}{installPreview && <div className="confirmation"><label><input type="checkbox" checked={installConfirmed} onChange={(event) => setInstallConfirmed(event.target.checked)} /> J’ai vérifié l’intégration project-local affichée.</label><button className="primary" onClick={applyInstallation} disabled={!installConfirmed || busy}>Confirmer l’installation MCP</button><details><summary>Inspecter le preview d’intégration</summary><pre>{JSON.stringify(installPreview, null, 2)}</pre></details></div>}</section>
        <section className="panel"><div className="panel-top"><div><p className="eyebrow">Project Profile</p><h2>Rebind contrôlé de l’identité</h2></div><Evidence label="ÉCRITURE" state="CONFIRMED ONLY" /></div><p>Seuls le nom et la description peuvent être modifiés ici. VERA sauvegarde le profil, journalise l’opération, aligne l’identité SQLite et refuse tout preview périmé. Une reprise est signalée par Doctor après interruption.</p><div className="field-grid"><label>Identifiant du projet<input value={profileId} onChange={(event) => setProfileId(event.target.value)} /></label><label>Nom du projet<input value={profileName} onChange={(event) => setProfileName(event.target.value)} /></label><label>Domaine<select value={profileDomain} onChange={(event) => setProfileDomain(event.target.value)}>{templates.map((item) => <option key={item}>{item}</option>)}</select></label><label className="wide">Description<input value={profileDescription} onChange={(event) => setProfileDescription(event.target.value)} /></label></div><button className="secondary" onClick={createProfileRebindPreview} disabled={!initialized || !profileId || !profileName || !profileDomain || busy}>Générer le preview</button>{profileRebindPreview && <div className="confirmation"><label><input type="checkbox" checked={profileRebindConfirmed} onChange={(event) => setProfileRebindConfirmed(event.target.checked)} /> J’ai vérifié le changement d’identité et son effet sur la mémoire locale.</label><button className="primary" onClick={applyProfileRebind} disabled={!profileRebindConfirmed || busy}>Confirmer le rebind</button><details><summary>Inspecter le preview</summary><pre>{JSON.stringify(profileRebindPreview, null, 2)}</pre></details></div>}<div className="action-grid"><div><h3>Reprise interrompue</h3><p>Doctor signale toute interruption ; aucune réparation n’est automatique.</p><button className="secondary" onClick={createProfileRecoveryPreview} disabled={!initialized || busy}>Examiner la reprise</button>{profileRecoveryPreview && <div className="confirmation"><label><input type="checkbox" checked={profileRecoveryConfirmed} onChange={(event) => setProfileRecoveryConfirmed(event.target.checked)} /> J’ai vérifié le journal de reprise affiché.</label><button className="primary" onClick={applyProfileRecovery} disabled={!profileRecoveryConfirmed || busy}>Confirmer la reprise</button><details><summary>Inspecter le preview de reprise</summary><pre>{JSON.stringify(profileRecoveryPreview, null, 2)}</pre></details></div>}</div></div></section>
        <section className="panel"><div className="panel-top"><div><p className="eyebrow">Contrat de capability · §32</p><h2>Le contrat entier, ou rien</h2></div><Evidence label="ÉCRITURE" state="CONFIRMED ONLY" /></div><p>Une capability est affichée comme un contrat complet : runner, entrées, sorties, timeout, policy, artefacts, validator, admissibilité de preuve et confirmation. <b>Il n’existe aucun champ de commande</b> — ni ici, ni dans le Core : un runner est choisi parmi les profils déclarés et ne reçoit que des paramètres typés (I008). Les listes proposées sont celles que le Core publie ; l’interface n’en invente aucune.</p>{!access("capabilities").open && <Locked reason={access("capabilities").reason} />}<button className="secondary" onClick={readCapabilityOptions} disabled={!initialized || busy}>Relire les choix du Core</button><div className="field-grid"><label>Identifiant<input value={capabilityId} onChange={(event) => setCapabilityId(event.target.value)} /></label><label>Nom<input value={capabilityName} onChange={(event) => setCapabilityName(event.target.value)} /></label><label>Type<select value={capabilityKind} onChange={(event) => setCapabilityKind(event.target.value)}>{(asChoices(capabilityOptions, "kinds").length ? asChoices(capabilityOptions, "kinds") : [capabilityKind]).map((item) => <option key={item}>{item}</option>)}</select></label><label>Version<input value={capabilityVersion} onChange={(event) => setCapabilityVersion(event.target.value)} /></label><label>Runner<select value={capabilityRunner} onChange={(event) => setCapabilityRunner(event.target.value)}>{(asChoices(capabilityOptions, "runners").length ? asChoices(capabilityOptions, "runners") : [capabilityRunner]).map((item) => <option key={item}>{item}</option>)}</select></label><label>Policy projet<select value={capabilityPolicy} onChange={(event) => setCapabilityPolicy(event.target.value)}>{(asChoices(capabilityOptions, "policies").length ? asChoices(capabilityOptions, "policies") : [capabilityPolicy]).map((item) => <option key={item}>{item}</option>)}</select></label><label>Timeout (secondes)<input value={capabilityTimeout} onChange={(event) => setCapabilityTimeout(event.target.value)} inputMode="numeric" /></label><label>Validator<select value={capabilityValidator} onChange={(event) => setCapabilityValidator(event.target.value)}>{(asChoices(capabilityOptions, "validators").length ? asChoices(capabilityOptions, "validators") : [capabilityValidator]).map((item) => <option key={item}>{item}</option>)}</select></label><label>Entrées (noms séparés par virgule)<input value={capabilityInputs} onChange={(event) => setCapabilityInputs(event.target.value)} /></label><label>Sorties (noms séparés par virgule)<input value={capabilityOutputs} onChange={(event) => setCapabilityOutputs(event.target.value)} /></label><label className="wide">Artefacts (chemins relatifs séparés par virgule)<input value={capabilityArtifacts} onChange={(event) => setCapabilityArtifacts(event.target.value)} /></label><label className="wide">Description<input value={capabilityDescription} onChange={(event) => setCapabilityDescription(event.target.value)} /></label></div><div className="action-grid"><label className="check"><input type="checkbox" checked={capabilityConfirmationRequired} onChange={(event) => setCapabilityConfirmationRequired(event.target.checked)} /> Confirmation requise à l’exécution</label><label className="check"><input type="checkbox" checked={capabilityGateBacked} onChange={(event) => setCapabilityGateBacked(event.target.checked)} /> Destinée à satisfaire une gate</label></div><p className="panel-locked"><b>RÉSEAU</b> La policy réseau vaut `DENY_NETWORK` et ne se choisit pas : c’est la seule que le Core admette. Une preuve ne naît pas d’une capability mais d’une evidence PASS validée puis admise.</p><button className="secondary" onClick={createCapabilityPreview} disabled={!initialized || busy || !access("capabilities").open}>Générer le contrat</button>{capabilityPreview && <div className="confirmation">{!isConfirmable(capabilityPreview) ? <><p className="panel-locked"><b>CONTRAT NON CONFIRMABLE</b> {asRefusals(capabilityPreview).length > 0 ? "Le Core refuse cette déclaration ; rien ne sera écrit." : "Ce preview n’est pas un contrat relu ; rien ne sera écrit."}</p><ul className="journey">{asRefusals(capabilityPreview).map((item) => <li key={item.code} className="journey-step journey-blocked"><span className="journey-state">{item.code}</span><small className="journey-reason">{item.message}</small></li>)}</ul></> : <><label><input type="checkbox" checked={capabilityConfirmed} onChange={(event) => setCapabilityConfirmed(event.target.checked)} /> J’ai vérifié le contrat entier et son absence du catalogue.</label><button className="primary" onClick={applyCapability} disabled={!capabilityConfirmed || busy}>Confirmer le contrat</button></>}<details><summary>Inspecter le contrat</summary><pre>{JSON.stringify(capabilityPreview, null, 2)}</pre></details></div>}</section>
        <section className="panel"><div className="panel-top"><div><p className="eyebrow">Structure de Gate</p><h2>Déclarer les dépendances, sans policy ni verdict</h2></div><Evidence label="ÉCRITURE" state="CONFIRMED ONLY" /></div><p>La structure lie uniquement des identifiants existants : work-item, evidence principale et exigences exactes. Elle ne décide aucune admission et ne scelle aucune policy.</p>{!access("gates").open && <Locked reason={access("gates").reason} />}<div className="field-grid"><label>Gate ID<input value={gateStructureId} onChange={(event) => setGateStructureId(event.target.value)} /></label><label>Work-item ID<input value={gateWorkItemId} onChange={(event) => setGateWorkItemId(event.target.value)} /></label><label>Evidence principale<input value={gatePrimaryEvidenceId} onChange={(event) => setGatePrimaryEvidenceId(event.target.value)} /></label><label className="wide">Evidences requises (IDs séparés par virgule)<input value={gateRequirementEvidenceIds} onChange={(event) => setGateRequirementEvidenceIds(event.target.value)} /></label></div><button className="secondary" onClick={createGateStructurePreview} disabled={!access("gates").open || !initialized || !gateStructureId || !gateWorkItemId || !gatePrimaryEvidenceId || busy}>Générer le preview</button>{gateStructurePreview && <div className="confirmation"><label><input type="checkbox" checked={gateStructureConfirmed} onChange={(event) => setGateStructureConfirmed(event.target.checked)} /> J’ai vérifié les endpoints et la structure proposés.</label><button className="primary" onClick={applyGateStructure} disabled={!gateStructureConfirmed || busy}>Confirmer la structure</button><details><summary>Inspecter le preview</summary><pre>{JSON.stringify(gateStructurePreview, null, 2)}</pre></details></div>}</section>
        <section className="panel"><div className="panel-top"><div><p className="eyebrow">Policies déclarées · étape 11</p><h2>Une règle, ou un vœu — jamais les deux</h2></div><Evidence label="ÉCRITURE" state="CONFIRMED ONLY" /></div><p>Chaque ligne indique ce qui l’applique réellement : <b>ENFORCED</b> nomme le module qui la lit, <b>DECLARED_ONLY</b> dit qu’aucun ne la lit. La policy réseau ne peut valoir que <code>deny</code> — le Core ne tient aucun chemin réseau —, <code>destructive.default</code> ne peut pas valoir <code>allow</code>, et <code>proven_requires</code> ne peut pas déclarer moins que ce que la promotion exige. Ces refus viennent du Core, pas de cet écran.</p>{!access("prepare").open && <Locked reason={access("prepare").reason} />}<button className="secondary" onClick={readPolicyOptions} disabled={!initialized || busy}>Relire les policies</button>{readPolicyLines(policyOptions).length > 0 && <div className="field-grid">{readPolicyLines(policyOptions).map((line) => { const name = `${line.section}.${line.key}`; const current = policyEdits[name] ?? policyValueText(line); return <label key={name} className={line.values === null ? "wide" : undefined}>{name} · {line.enforcement}{line.values === null ? <input value={current} onChange={(event) => setPolicyEdits({ ...policyEdits, [name]: event.target.value })} /> : <select value={current} onChange={(event) => setPolicyEdits({ ...policyEdits, [name]: event.target.value })}>{line.values.map((item) => <option key={item}>{item}</option>)}</select>}<small className="journey-reason">{line.reason}</small></label>; })}</div>}<button className="secondary" onClick={createPolicyPreview} disabled={!initialized || busy || Object.keys(policyEdits).length === 0}>Générer le preview</button>{policyPreview && <div className="confirmation">{!isConfirmable(policyPreview) ? <p className="panel-locked"><b>ÉDITION REFUSÉE</b> {String(policyPreview.blockers ?? "Ce preview n’est pas une édition relue.")}</p> : <><label><input type="checkbox" checked={policyConfirmed} onChange={(event) => setPolicyConfirmed(event.target.checked)} /> J’ai vérifié les lignes modifiées et ce qui les applique.</label><button className="primary" onClick={applyPolicyEdit} disabled={!policyConfirmed || busy}>Confirmer les policies</button></>}<details><summary>Inspecter le preview</summary><pre>{JSON.stringify(policyPreview, null, 2)}</pre></details></div>}</section>
        <section className="panel"><div className="panel-top"><div><p className="eyebrow">Reprise et intégrations · étapes 12 et 13</p><h2>Changer le contrat, c’est casser la reprise en cours</h2></div><Evidence label="ÉCRITURE" state="CONFIRMED ONLY" /></div><p>La barrière de reprise lie une session au hash exact du dossier qui l’a armée, et ce dossier est compilé depuis ces sections et depuis le hash du profil. Changer l’un ou l’autre rend tout accusé déjà armé impossible — c’est la garantie qui fonctionne, pas un défaut. VERA <b>nomme donc les gardes qu’une édition invalidera</b> avant d’écrire quoi que ce soit.</p>{!access("prepare").open && <Locked reason={access("prepare").reason} />}<button className="secondary" onClick={readResumeOptions} disabled={!initialized || busy}>Relire le contrat</button>{resumeOptions && <div className="field-grid"><label className="wide">Sections (id=required|optional, séparées par virgule)<input value={resumeSections} onChange={(event) => setResumeSections(event.target.value)} /></label><label className="wide">Intégrations activées (parmi {readIntegrations(resumeOptions).available.join(", ") || "aucune déclarée"})<input value={resumeIntegrations} onChange={(event) => setResumeIntegrations(event.target.value)} /></label><label>Budget de reprise (octets)<input value={resumeBudget} onChange={(event) => setResumeBudget(event.target.value)} inputMode="numeric" placeholder={String((isRecord(resumeOptions.max_resume_bytes) ? resumeOptions.max_resume_bytes.value : "") ?? "")} /></label></div>}<button className="secondary" onClick={createResumePreview} disabled={!initialized || busy || !resumeOptions}>Générer le preview</button>{resumePreview && <div className="confirmation">{!isConfirmable(resumePreview) ? <p className="panel-locked"><b>ÉDITION REFUSÉE</b> {String(resumePreview.blockers ?? "Ce preview n’est pas une édition relue.")}</p> : <>{(() => { const guards = readInvalidated(resumePreview); return guards === null ? <p className="panel-locked"><b>INVALIDATION INCONNUE</b> Le Core n’a pas dit ce que cette édition casserait.</p> : guards.length === 0 ? <p className="panel-locked"><b>AUCUNE REPRISE ARMÉE</b> Cette édition n’invalide aucun accusé en cours.</p> : <ul className="journey">{guards.map((guard) => <li key={guard.resumeContractHash} className="journey-step journey-blocked"><span className="journey-label">{guard.adapterId} · {guard.status}</span><span className="journey-state">{guard.resumeContractHash.slice(0, 12)}</span><small className="journey-reason">{guard.reason}</small></li>)}</ul>; })()}<label><input type="checkbox" checked={resumeConfirmed} onChange={(event) => setResumeConfirmed(event.target.checked)} /> J’ai vérifié le contrat et les reprises qu’il invalide.</label><button className="primary" onClick={applyResumeEdit} disabled={!resumeConfirmed || busy}>Confirmer le contrat</button></>}<details><summary>Inspecter le preview</summary><pre>{JSON.stringify(resumePreview, null, 2)}</pre></details></div>}</section>
        <section className="panel"><div className="panel-top"><div><p className="eyebrow">Gate déclarée · §33</p><h2>Ce qu’une gate peut fonder</h2></div><Evidence label="LECTURE" state={gateReport ? "DERIVED" : "WAITING"} /></div><p>Trois classes d’exigence, et elles ne diffèrent pas par une couleur : <b>validation technique</b> — un verdict rejouable ; <b>simple observation</b> — un fait enregistré dont le Core n’a dérivé aucun verdict ; <b>appréciation sémantique</b> — un jugement qu’aucune réexécution ne reproduit. Seule la première peut fonder une preuve, et c’est le Core qui refuse la promotion des deux autres, pas cet écran.</p>{!access("gates").open && <Locked reason={access("gates").reason} />}<div className="field-grid"><label>Gate ID<input value={gateId} onChange={(event) => setGateId(event.target.value)} /></label></div><button className="secondary" onClick={readGateReport} disabled={!initialized || !gateId || busy}>Relire la gate</button>{gateReport && <div className="confirmation"><div className="action-grid"><div className="metric"><b>{countByClass(readRequirements(gateReport)).TECHNICAL_VALIDATION}</b><span>validation technique</span></div><div className="metric"><b>{countByClass(readRequirements(gateReport)).SIMPLE_OBSERVATION}</b><span>simple observation</span></div><div className="metric"><b>{countByClass(readRequirements(gateReport)).SEMANTIC_APPRECIATION}</b><span>appréciation sémantique</span></div></div><ul className="journey">{readRequirements(gateReport).map((item) => <li key={item.evidenceId} className={`journey-step ${item.mayCreateProof ? "journey-completed" : "journey-blocked"}`}><span className="journey-index">{item.primary ? "★" : "·"}</span><span className="journey-label">{item.evidenceId} · {item.evidenceType}</span><span className="journey-state">{item.evidenceClass}</span><small className="journey-reason">{item.verdict} · {item.admission} — {item.reason}</small></li>)}</ul><p className="panel-locked"><b>PROMOTION</b> {readPromotion(gateReport).canSatisfyGate ? "[✓]" : "[ ]"} peut satisfaire la gate — {readPromotion(gateReport).satisfactionReason}<br />{readPromotion(gateReport).canCreateProof ? "[✓]" : "[ ]"} peut créer une proof — {readPromotion(gateReport).proofReason}</p><details><summary>Inspecter le rapport de gate</summary><pre>{JSON.stringify(gateReport, null, 2)}</pre></details></div>}</section>
        <section className="panel"><div className="panel-top"><div><p className="eyebrow">Policy de Gate</p><h2>Sceller une règle, sans verdict client</h2></div><Evidence label="ÉCRITURE" state="CONFIRMED ONLY" /></div><p>La Gate et ses evidences doivent déjà exister. Cette règle ne modifie ni admission ni résultat : l’évaluation reste calculée par le Core.</p>{!access("gates").open && <Locked reason={access("gates").reason} />}<div className="field-grid"><label>Gate ID<input value={gateId} onChange={(event) => setGateId(event.target.value)} /></label><label>Mode<select value={gateMode} onChange={(event) => setGateMode(event.target.value)}>{["ALL", "ANY", "AT_LEAST"].map((item) => <option key={item}>{item}</option>)}</select></label>{gateMode === "AT_LEAST" && <label>Seuil<input value={gateMinimum} onChange={(event) => setGateMinimum(event.target.value)} inputMode="numeric" /></label>}</div><button className="secondary" onClick={createGatePolicyPreview} disabled={!access("gates").open || !initialized || !gateId || busy}>Générer le preview</button>{gatePolicyPreview && <div className="confirmation"><label><input type="checkbox" checked={gatePolicyConfirmed} onChange={(event) => setGatePolicyConfirmed(event.target.checked)} /> J’ai vérifié cette policy et les exigences existantes.</label><button className="primary" onClick={applyGatePolicy} disabled={!gatePolicyConfirmed || busy}>Confirmer la policy</button><details><summary>Inspecter le preview</summary><pre>{JSON.stringify(gatePolicyPreview, null, 2)}</pre></details></div>}</section>
        <section className="panel doctor" id="verify"><div><p className="eyebrow">État dérivé, diagnostic & mémoire</p><h2>Constater, ne pas deviner</h2><p>La couverture et le statut VCS sont dérivés du Core après initialisation. Le doctor indique ce qui est présent localement ; il ne transforme pas une configuration en preuve hôte réelle. La synchronisation ne concerne que `.vera-mmu/` et suit la policy du projet.</p></div><div className="verify-actions">{initialized && <><button className="secondary" onClick={refreshProjectStatus} disabled={busy}>Actualiser l’état</button><div className="status-strip"><Evidence label="VCS" state={vcsState} /><span>{coverageTools === null ? "Couverture non chargée" : `${coverageTools} tools MCP déclarés`}</span></div></>}<button className="secondary" onClick={readProjectDocumentation} disabled={!initialized || busy}>Voir la documentation générée</button><button className="secondary" onClick={runProjectDoctor} disabled={!project || busy}>Doctor projet</button><button className="secondary" onClick={readMigrationStatus} disabled={!project || busy}>Statut migration</button><button className="secondary" onClick={runDoctor} disabled={!project || busy}>Doctor adapter</button><button className="secondary" onClick={synchronizeMemory} disabled={!project || busy}>Synchroniser la mémoire</button>{projectDoctor && <details><summary>Doctor projet (lecture seule)</summary><pre>{JSON.stringify(projectDoctor, null, 2)}</pre></details>}{migrationStatus && <details><summary>Migration Profile (lecture seule)</summary><pre>{JSON.stringify(migrationStatus, null, 2)}</pre></details>}{projectDocumentation && <details><summary>Documentation générée (lecture seule)</summary><pre>{JSON.stringify(projectDocumentation, null, 2)}</pre></details>}{doctor && <pre>{JSON.stringify(doctor, null, 2)}</pre>}{memorySync && <pre>{JSON.stringify(memorySync, null, 2)}</pre>}</div></section>
        <section className={`notice notice-${notice.tone}`} aria-live="polite"><b>{notice.title}</b><span>{notice.detail}</span></section>
        <footer>VERA-MMU · Core séparé de l’interface · Aucun réseau implicite · Aucun user-scope</footer>
      </div>
    </main>
  </div>;
}
