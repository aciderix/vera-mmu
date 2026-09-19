//! Backend Tauri VERA : un WebView reçoit des commandes typées, jamais le filesystem ou un shell.
use rand::RngCore;
use serde_json::{json, Value};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::Mutex;
use tauri::{Manager, State};

const FORMAT: &str = "vera-desktop-bridge/v1";

#[derive(Debug)]
enum BridgeExecutable {
    #[cfg_attr(not(debug_assertions), allow(dead_code))]
    Source(PathBuf),
    #[cfg_attr(debug_assertions, allow(dead_code))]
    Bundled(PathBuf),
}

impl BridgeExecutable {
    fn command(&self) -> Result<Command, String> {
        match self {
            Self::Source(root) => {
                let mut command = Command::new(python_executable()?);
                command.arg("-m").arg("vera_mmu.desktop_bridge").env("PYTHONPATH", root.join("src"));
                Ok(command)
            }
            Self::Bundled(binary) => {
                if binary.is_symlink() || !binary.is_file() {
                    return Err("Sidecar VERA embarqué absent ou ambigu.".to_string());
                }
                Ok(Command::new(binary))
            }
        }
    }
}

/// Interpréteurs essayés pour lancer le bridge en mode développement, dans l’ordre.
///
/// `python3` d’abord parce que c’est le nom juste sur Linux et macOS ; `python` ensuite parce que
/// c’est le seul qui existe sur une installation Windows ordinaire — et que `python3` y est
/// souvent un alias du Microsoft Store qui se lance puis quitte aussitôt, ce qui ne se distingue
/// d’un bridge muet que par la sonde ci-dessous.
const PYTHON_CANDIDATES: [&str; 2] = ["python3", "python"];

/// Variable d’échappement pour désigner un interpréteur précis (venv, build matriciel, CI).
const PYTHON_VARIABLE: &str = "VERA_PYTHON";

/// Résout, une fois, un interpréteur Python qui répond réellement.
///
/// **Le défaut que ceci corrige.** `Command::new("python3")` était codé en dur. Sous Windows
/// l’exécutable s’appelle `python`, et `python3` y désigne fréquemment l’alias du Microsoft Store :
/// le processus démarre et meurt sans lire son entrée, si bien que l’appelant reçoit « Lecture
/// bridge impossible. » — un bridge qui se tait, pas un interpréteur introuvable. Le diagnostic
/// pointait donc à côté de la cause. Mesuré sur le runner Windows de la CI, où ce chemin n’avait
/// jamais tourné faute de `cargo test` dans le workflow.
///
/// Sonder plutôt que deviner : un nom qui existe dans le PATH ne prouve pas qu’il exécute du
/// Python, et c’est précisément ce que l’alias Windows rend faux.
fn python_executable() -> Result<String, String> {
    use std::sync::OnceLock;
    static RESOLVED: OnceLock<Option<String>> = OnceLock::new();
    RESOLVED
        .get_or_init(|| {
            let declared = std::env::var(PYTHON_VARIABLE).ok().filter(|value| !value.trim().is_empty());
            declared
                .into_iter()
                .chain(PYTHON_CANDIDATES.iter().map(|item| item.to_string()))
                .find(|candidate| runs_python(candidate))
        })
        .clone()
        .ok_or_else(|| {
            format!(
                "Aucun interpréteur Python utilisable : essayés {}. Poser {PYTHON_VARIABLE} pour en désigner un.",
                PYTHON_CANDIDATES.join(", ")
            )
        })
}

/// Vérifie qu’un nom exécute bien du Python 3, plutôt que d’exister dans le PATH.
///
/// La sonde exige une **sortie** que seul un interpréteur produirait, et non un simple code de
/// retour nul. Une première version se contentait du code de sortie, et son propre test l’a mise
/// en défaut : `echo` ignore ses arguments et sort en 0, donc passait pour un interpréteur. Un
/// alias qui démarre et quitte proprement aurait été accepté de la même manière — c’est-à-dire le
/// cas même que cette fonction existe pour écarter.
fn runs_python(candidate: &str) -> bool {
    Command::new(candidate)
        .arg("-c")
        .arg("import sys; sys.stdout.write(str(sys.version_info[0]))")
        .stdin(Stdio::null())
        .stderr(Stdio::null())
        .output()
        .map(|output| output.status.success() && String::from_utf8_lossy(&output.stdout).trim() == "3")
        .unwrap_or(false)
}

struct BridgeSession {
    child: Child,
    input: ChildStdin,
    output: BufReader<ChildStdout>,
    nonce: String,
    request_counter: u64,
}

impl BridgeSession {
    fn start(root: &Path, executable: &BridgeExecutable) -> Result<Self, String> {
        let mut bytes = [0_u8; 32];
        rand::thread_rng().fill_bytes(&mut bytes);
        let nonce = bytes.iter().map(|byte| format!("{byte:02x}")).collect::<String>();
        let mut command = executable.command()?;
        let mut child = command
            .arg("--project-root")
            .arg(root)
            .arg("--nonce")
            .arg(&nonce)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|_| "Impossible de démarrer le bridge VERA local.".to_string())?;
        let input = child.stdin.take().ok_or_else(|| "Canal bridge stdin indisponible.".to_string())?;
        let output = child.stdout.take().ok_or_else(|| "Canal bridge stdout indisponible.".to_string())?;
        Ok(Self { child, input, output: BufReader::new(output), nonce, request_counter: 0 })
    }

    fn call(&mut self, operation: &str, input: Value) -> Result<Value, String> {
        self.request_counter = self.request_counter.checked_add(1).ok_or_else(|| "Compteur bridge invalide.".to_string())?;
        let request = json!({
            "format": FORMAT,
            "id": format!("desktop-{}", self.request_counter),
            "nonce": self.nonce,
            "operation": operation,
            "input": input,
        });
        let line = serde_json::to_string(&request).map_err(|_| "Requête bridge invalide.".to_string())?;
        self.input.write_all(line.as_bytes()).map_err(|_| "Bridge local indisponible.".to_string())?;
        self.input.write_all(b"\n").map_err(|_| "Bridge local indisponible.".to_string())?;
        self.input.flush().map_err(|_| "Bridge local indisponible.".to_string())?;
        let mut reply = String::new();
        if self.output.read_line(&mut reply).map_err(|_| "Lecture bridge impossible.".to_string())? == 0 {
            return Err("Bridge local arrêté sans réponse.".to_string());
        }
        let value: Value = serde_json::from_str(&reply).map_err(|_| "Réponse bridge non JSON.".to_string())?;
        if value.get("format").and_then(Value::as_str) != Some(FORMAT) {
            return Err("Réponse bridge hors protocole.".to_string());
        }
        if value.get("ok").and_then(Value::as_bool) == Some(true) {
            return value.get("result").cloned().ok_or_else(|| "Résultat bridge absent.".to_string());
        }
        let detail = value.get("error").and_then(Value::as_object).and_then(|error| error.get("message")).and_then(Value::as_str).unwrap_or("Opération VERA refusée.");
        Err(detail.to_string())
    }
}

impl Drop for BridgeSession {
    fn drop(&mut self) { let _ = self.child.kill(); }
}

struct AppState {
    session: Mutex<Option<BridgeSession>>,
    executable: BridgeExecutable,
}

fn bridge_executable(app: &tauri::AppHandle) -> Result<BridgeExecutable, String> {
    #[cfg(debug_assertions)]
    {
        let root = Path::new(env!("CARGO_MANIFEST_DIR")).ancestors().nth(3).ok_or_else(|| "Racine source desktop introuvable.".to_string())?;
        let _ = app;
        Ok(BridgeExecutable::Source(root.to_path_buf()))
    }
    #[cfg(not(debug_assertions))]
    {
        let _ = app;
        let extension = if cfg!(target_os = "windows") { ".exe" } else { "" };
        let binary = std::env::current_exe()
            .map_err(|_| "Exécutable desktop introuvable.".to_string())?
            .parent()
            .ok_or_else(|| "Répertoire de l’application introuvable.".to_string())?
            .join(format!("vmmu-desktop-bridge{extension}"));
        Ok(BridgeExecutable::Bundled(binary))
    }
}

/// Nom de l’argument et de la variable qui désignent la racine sans dialogue natif.
const PROJECT_ROOT_FLAG: &str = "--project-root";
const PROJECT_ROOT_VARIABLE: &str = "VERA_MMU_PROJECT_ROOT";

/// Valide une racine candidate exactement comme le dialogue natif valide la sienne.
///
/// Une seule fonction pour les deux voies : si la validation divergeait, la voie sans dialogue
/// deviendrait la voie permissive, et ce serait précisément celle qu’un automate emprunte.
fn accept_root(folder: PathBuf) -> Result<PathBuf, String> {
    if folder.is_symlink() || !folder.is_dir() {
        return Err("Dossier sélectionné invalide ou symlinké.".to_string());
    }
    folder.canonicalize().map_err(|_| "Dossier sélectionné introuvable.").map_err(str::to_string)
}

/// Lit la racine désignée au lancement, par `--project-root <chemin>` ou `VERA_MMU_PROJECT_ROOT`.
///
/// **Pourquoi c’est sûr.** L’invariant du bridge est que la racine vient du parent natif, jamais
/// d’une requête WebView. Ces deux sources sont l’argv et l’environnement du processus, c’est-à-dire
/// ce que le parent a décidé au lancement — le même niveau de confiance que le dialogue, et non
/// celui du contenu affiché. Le WebView continue de n’envoyer aucun chemin : `select_project` ne
/// prend toujours aucun paramètre.
///
/// **Pourquoi ça existe.** Le dialogue natif dépend d’un portail de bureau, absent d’un conteneur
/// sans écran. Mesuré sur l’AppImage livrée sous Xvfb, avec D-Bus et `xdg-desktop-portal`
/// démarrés : la fenêtre s’affiche, le clic est reçu — le bouton passe en survol — mais aucun
/// sélecteur ne s’ouvre. L’interface restait donc bloquée à sa toute première étape, et c’est la
/// seule chose qui empêchait de la piloter sans écran.
///
/// `None` signifie qu’aucune racine n’a été désignée : le dialogue reste alors la seule voie.
fn preselected_root() -> Option<Result<PathBuf, String>> {
    parse_preselected_root(std::env::args_os().skip(1), std::env::var_os(PROJECT_ROOT_VARIABLE))
}

/// La part testable de la lecture : le parcours des arguments, isolé du processus.
///
/// Tant que la lecture appelait `std::env::args_os()` en son sein, rien ne pouvait l'exercer :
/// un test ne choisit pas l'argv de son propre processus. La séparer n'est pas de l'esthétique,
/// c'est la condition pour que cette voie soit mesurée plutôt que supposée.
fn parse_preselected_root(
    arguments: impl IntoIterator<Item = std::ffi::OsString>,
    variable: Option<std::ffi::OsString>,
) -> Option<Result<PathBuf, String>> {
    let mut arguments = arguments.into_iter();
    while let Some(argument) = arguments.next() {
        let text = argument.to_string_lossy().into_owned();
        if text == PROJECT_ROOT_FLAG {
            return Some(match arguments.next() {
                Some(value) if !value.is_empty() => accept_root(PathBuf::from(value)),
                _ => Err(format!("{PROJECT_ROOT_FLAG} attend un chemin de dossier.")),
            });
        }
        if let Some(value) = text.strip_prefix(&format!("{PROJECT_ROOT_FLAG}=")) {
            if value.is_empty() {
                return Some(Err(format!("{PROJECT_ROOT_FLAG} attend un chemin de dossier.")));
            }
            return Some(accept_root(PathBuf::from(value)));
        }
    }
    match variable {
        Some(value) if !value.is_empty() => Some(accept_root(PathBuf::from(value))),
        _ => None,
    }
}

fn folder_dialog() -> Result<PathBuf, String> {
    if let Some(preselected) = preselected_root() {
        return preselected;
    }
    let folder = rfd::FileDialog::new().set_title("Choisir le dossier du projet VERA").pick_folder().ok_or_else(|| "Sélection de projet annulée.".to_string())?;
    accept_root(folder)
}

fn with_bridge<T>(state: &State<'_, AppState>, f: impl FnOnce(&mut BridgeSession) -> Result<T, String>) -> Result<T, String> {
    let mut guard = state.session.lock().map_err(|_| "État bridge verrouillé de façon ambiguë.".to_string())?;
    f(guard.as_mut().ok_or_else(|| "Aucun projet local associé.".to_string())?)
}

/// Dit si une racine a été désignée au lancement, sans jamais ouvrir de dialogue.
///
/// Le frontend s’en sert pour n’associer automatiquement que dans ce cas. Appeler `select_project`
/// au montage sans cette sonde ferait surgir le sélecteur de dossier au démarrage chez quelqu’un
/// qui n’a rien demandé — une fenêtre modale non sollicitée est un défaut, pas une commodité.
#[tauri::command]
fn preselected_project() -> Result<Value, String> {
    Ok(match preselected_root() {
        None => json!({"root": Value::Null, "source": "DIALOG"}),
        Some(Ok(root)) => json!({"root": root, "source": "LAUNCH_ARGUMENT"}),
        Some(Err(reason)) => json!({"root": Value::Null, "source": "LAUNCH_ARGUMENT", "error": reason}),
    })
}

#[tauri::command]
fn select_project(state: State<'_, AppState>) -> Result<Value, String> {
    let root = folder_dialog()?;
    let mut bridge = BridgeSession::start(&root, &state.executable)?;
    let scan = bridge.call("project.scan", json!({}))?;
    let mut guard = state.session.lock().map_err(|_| "État bridge verrouillé de façon ambiguë.".to_string())?;
    *guard = Some(bridge);
    Ok(json!({"root": root, "scan": scan}))
}

#[tauri::command]
fn scan_project(state: State<'_, AppState>) -> Result<Value, String> { with_bridge(&state, |bridge| bridge.call("project.scan", json!({}))) }

#[tauri::command]
fn project_status(state: State<'_, AppState>) -> Result<Value, String> { with_bridge(&state, |bridge| bridge.call("project.status", json!({}))) }

#[tauri::command]
fn wizard_state(state: State<'_, AppState>) -> Result<Value, String> { with_bridge(&state, |bridge| bridge.call("wizard.state", json!({}))) }

#[tauri::command]
fn journey_outcome(state: State<'_, AppState>) -> Result<Value, String> { with_bridge(&state, |bridge| bridge.call("journey.outcome", json!({}))) }

#[tauri::command]
fn recommend_profile(state: State<'_, AppState>) -> Result<Value, String> { with_bridge(&state, |bridge| bridge.call("project.recommend", json!({}))) }

#[tauri::command]
fn project_doctor(state: State<'_, AppState>) -> Result<Value, String> { with_bridge(&state, |bridge| bridge.call("project.doctor", json!({}))) }

#[tauri::command]
fn migration_status(state: State<'_, AppState>) -> Result<Value, String> { with_bridge(&state, |bridge| bridge.call("migration.status", json!({}))) }

#[tauri::command]
fn project_documentation(state: State<'_, AppState>) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("project.documentation", json!({})))
}

#[tauri::command]
fn profile_rebind_preview(state: State<'_, AppState>, project_id: String, project_name: String, project_domain: String, project_description: String) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("profile.rebind.preview", json!({"projectId": project_id, "projectName": project_name, "projectDomain": project_domain, "projectDescription": project_description})))
}

#[tauri::command]
fn profile_rebind_apply(state: State<'_, AppState>, preview_hash: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("profile.rebind.apply", json!({"previewHash": preview_hash, "confirm": confirm})))
}

#[tauri::command]
fn profile_rebind_recovery_preview(state: State<'_, AppState>) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("profile.rebind.recovery.preview", json!({})))
}

#[tauri::command]
fn profile_rebind_recovery_apply(state: State<'_, AppState>, preview_hash: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("profile.rebind.recovery.apply", json!({"previewHash": preview_hash, "confirm": confirm})))
}

#[tauri::command]
fn capability_options(state: State<'_, AppState>) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("capability.options", json!({})))
}

/// The complete §32 contract. There is deliberately no command, API, argv or URL parameter:
/// the Core holds no such field, and a runner is chosen among the profiles it declares (I008).
#[tauri::command]
#[allow(clippy::too_many_arguments)]
fn capability_preview(
    state: State<'_, AppState>,
    identifier: String,
    name: String,
    description: String,
    kind: String,
    version: String,
    runner: String,
    policy: String,
    timeout_seconds: Option<i64>,
    inputs: Vec<String>,
    outputs: Vec<String>,
    artifacts: Vec<String>,
    validator: String,
    yields_proof: bool,
    confirmation_required: bool,
    gate_backed: bool,
) -> Result<Value, String> {
    with_bridge(&state, |bridge| {
        bridge.call(
            "capability.preview",
            json!({
                "identifier": identifier, "name": name, "description": description, "kind": kind,
                "version": version, "runner": runner, "policy": policy,
                "timeoutSeconds": timeout_seconds, "inputs": inputs, "outputs": outputs,
                "artifacts": artifacts, "validator": validator, "yieldsProof": yields_proof,
                "confirmationRequired": confirmation_required, "gateBacked": gate_backed
            }),
        )
    })
}

#[tauri::command]
fn capability_apply(state: State<'_, AppState>, preview_hash: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("capability.apply", json!({"previewHash": preview_hash, "confirm": confirm})))
}

#[tauri::command]
fn policy_options(state: State<'_, AppState>) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("policy.options", json!({})))
}

/// Named policy lines only. The closed values, and which lines are enforced, come from the Core.
#[tauri::command]
fn policy_preview(state: State<'_, AppState>, changes: Value) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("policy.preview", json!({"changes": changes})))
}

#[tauri::command]
fn policy_apply(state: State<'_, AppState>, preview_hash: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("policy.apply", json!({"previewHash": preview_hash, "confirm": confirm})))
}

#[tauri::command]
fn resume_options(state: State<'_, AppState>) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("resume.options", json!({})))
}

/// The resume contract and the enabled integrations. What a change invalidates comes from the Core.
#[tauri::command]
fn resume_preview(
    state: State<'_, AppState>,
    template: Option<String>,
    sections: Option<Value>,
    max_resume_bytes: Option<i64>,
    integrations: Option<Vec<String>>,
) -> Result<Value, String> {
    with_bridge(&state, |bridge| {
        bridge.call(
            "resume.preview",
            json!({"template": template, "sections": sections, "maxResumeBytes": max_resume_bytes, "integrations": integrations}),
        )
    })
}

#[tauri::command]
fn resume_apply(state: State<'_, AppState>, preview_hash: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("resume.apply", json!({"previewHash": preview_hash, "confirm": confirm})))
}

/// The Core's lifecycle and the project's declared transition policies. Reading only.
#[tauri::command]
fn work_graph_read(state: State<'_, AppState>) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("work.graph.read", json!({})))
}

/// A transition-policy change, planned. The modes offered are the Core's, never this parent's.
#[tauri::command]
fn work_graph_preview(state: State<'_, AppState>, start_mode: Option<String>, completion_mode: Option<String>) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("work.graph.preview", json!({"startMode": start_mode, "completionMode": completion_mode})))
}

#[tauri::command]
fn work_graph_apply(state: State<'_, AppState>, preview_hash: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("work.graph.apply", json!({"previewHash": preview_hash, "confirm": confirm})))
}

/// The declared knowledge, entity and relation types, and what each already carries.
#[tauri::command]
fn taxonomy_options(state: State<'_, AppState>) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("taxonomy.options", json!({})))
}

/// An edit of the declared knowledge, entity and relation types, planned. Writes nothing.
#[tauri::command]
fn taxonomy_preview(
    state: State<'_, AppState>,
    knowledge_types: Option<Vec<String>>,
    entity_types: Option<Vec<String>>,
    relation_types: Option<Vec<String>>,
) -> Result<Value, String> {
    with_bridge(&state, |bridge| {
        bridge.call(
            "taxonomy.preview",
            json!({"knowledgeTypes": knowledge_types, "entityTypes": entity_types, "relationTypes": relation_types}),
        )
    })
}

#[tauri::command]
fn taxonomy_apply(state: State<'_, AppState>, preview_hash: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("taxonomy.apply", json!({"previewHash": preview_hash, "confirm": confirm})))
}

/// The §34 figures, hashes and alerts, before generation. Every number comes from the Core.
#[tauri::command]
fn mcp_preview(state: State<'_, AppState>, adapter_id: String) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("mcp.preview", json!({"adapterId": adapter_id})))
}

/// One declared gate as §33 displays it: requirements classified, and the two promotion lines.
#[tauri::command]
fn gate_report(state: State<'_, AppState>, gate_id: String) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("gate.report", json!({"gateId": gate_id})))
}

#[tauri::command]
fn gate_policy_preview(state: State<'_, AppState>, gate_id: String, mode: String, minimum_admissions: Option<i64>) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("gate.policy.preview", json!({"gateId": gate_id, "mode": mode, "minimumAdmissions": minimum_admissions})))
}

#[tauri::command]
fn gate_policy_apply(state: State<'_, AppState>, preview_hash: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("gate.policy.apply", json!({"previewHash": preview_hash, "confirm": confirm})))
}

#[tauri::command]
fn gate_structure_preview(state: State<'_, AppState>, gate_id: String, work_item_id: String, primary_evidence_id: String, requirement_evidence_ids: Vec<String>) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("gate.structure.preview", json!({"gateId": gate_id, "workItemId": work_item_id, "primaryEvidenceId": primary_evidence_id, "requirementEvidenceIds": requirement_evidence_ids})))
}

#[tauri::command]
fn gate_structure_apply(state: State<'_, AppState>, preview_hash: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("gate.structure.apply", json!({"previewHash": preview_hash, "confirm": confirm})))
}

#[tauri::command]
fn initialization_preview(state: State<'_, AppState>, template: String, project_id: String, project_name: String) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("project.init.preview", json!({"template": template, "projectId": project_id, "projectName": project_name})))
}

#[tauri::command]
fn initialization_apply(state: State<'_, AppState>, preview_hash: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("project.init.apply", json!({"previewHash": preview_hash, "confirm": confirm})))
}

#[tauri::command]
fn agent_profiles(state: State<'_, AppState>) -> Result<Value, String> { with_bridge(&state, |bridge| bridge.call("agents.list", json!({}))) }

#[tauri::command]
fn generation_preview(state: State<'_, AppState>, agent_profile_id: String) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("adapter.generate", json!({"agentProfileId": agent_profile_id})))
}

#[tauri::command]
fn stage_adapter(state: State<'_, AppState>, agent_profile_id: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("adapter.stage", json!({"agentProfileId": agent_profile_id, "confirm": confirm})))
}

#[tauri::command]
fn installation_preview(state: State<'_, AppState>, agent_profile_id: String) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("adapter.install.preview", json!({"agentProfileId": agent_profile_id})))
}

#[tauri::command]
fn installation_apply(state: State<'_, AppState>, preview_hash: String, confirm: bool) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("adapter.install.apply", json!({"previewHash": preview_hash, "confirm": confirm})))
}

#[tauri::command]
fn adapter_doctor(state: State<'_, AppState>, agent_profile_id: String) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("adapter.doctor", json!({"agentProfileId": agent_profile_id})))
}

#[tauri::command]
fn memory_sync(state: State<'_, AppState>) -> Result<Value, String> {
    with_bridge(&state, |bridge| bridge.call("memory.sync", json!({})))
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let executable = bridge_executable(app.handle()).map_err(std::io::Error::other)?;
            app.manage(AppState { session: Mutex::new(None), executable });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![preselected_project, select_project, scan_project, wizard_state, journey_outcome, recommend_profile, project_status, project_doctor, migration_status, project_documentation, profile_rebind_preview, profile_rebind_apply, profile_rebind_recovery_preview, profile_rebind_recovery_apply, capability_options, capability_preview, capability_apply, policy_options, policy_preview, policy_apply, resume_options, resume_preview, resume_apply, work_graph_read, work_graph_preview, work_graph_apply, taxonomy_options, taxonomy_preview, taxonomy_apply, mcp_preview, gate_report, gate_policy_preview, gate_policy_apply, gate_structure_preview, gate_structure_apply, initialization_preview, initialization_apply, agent_profiles, generation_preview, stage_adapter, installation_preview, installation_apply, adapter_doctor, memory_sync])
        .run(tauri::generate_context!())
        .expect("échec de l’application desktop VERA");
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn bridge_session_scans_a_native_root_over_stdio() {
        let nonce = SystemTime::now().duration_since(UNIX_EPOCH).expect("clock").as_nanos();
        let root = std::env::temp_dir().join(format!("vera-desktop-bridge-{nonce}"));
        fs::create_dir_all(&root).expect("temporary project root");
        fs::write(root.join("pyproject.toml"), "[project]\nname = 'desktop-check'\n").expect("project marker");
        let source = Path::new(env!("CARGO_MANIFEST_DIR")).ancestors().nth(3).expect("VERA root").to_path_buf();
        let mut bridge = BridgeSession::start(&root, &BridgeExecutable::Source(source)).expect("bridge starts from source in test mode");
        let result = bridge.call("project.scan", json!({})).expect("scan response");
        // `v2` et non `v1` : le scanner a changé de format et cette assertion était restée en
        // arrière. Personne ne l'a vu parce que la CI n'exécutait que `pnpm test` — `cargo test`
        // n'y était pas. Un test que rien ne lance ne garde rien.
        assert_eq!(result.get("format").and_then(Value::as_str), Some("vera-scan-report/v2"));
        assert_eq!(result.get("status").and_then(Value::as_str), Some("OBSERVED"));
        drop(bridge);
        fs::remove_dir_all(root).expect("temporary root cleanup");
    }

    /// La racine désignée au lancement doit passer la **même** validation que le dialogue.
    ///
    /// C'est le point sensible : si la voie sans dialogue était plus permissive, elle deviendrait
    /// la voie faible, et c'est exactement celle qu'un automate emprunte. Les deux appellent donc
    /// `accept_root`, et ces tests l'attaquent directement.
    #[test]
    fn a_launch_root_is_validated_exactly_like_a_dialog_root() {
        let nonce = SystemTime::now().duration_since(UNIX_EPOCH).expect("clock").as_nanos();
        let base = std::env::temp_dir().join(format!("vera-root-check-{nonce}"));
        let real = base.join("projet");
        fs::create_dir_all(&real).expect("racine réelle");

        let accepted = accept_root(real.clone()).expect("un vrai dossier est accepté");
        assert!(accepted.is_absolute(), "la racine acceptée est canonique");

        // Un fichier n'est pas une racine.
        let file = base.join("fichier.txt");
        fs::write(&file, b"x").expect("fichier");
        assert!(accept_root(file).is_err(), "un fichier est refusé");

        // Un chemin absent n'est pas une racine.
        assert!(accept_root(base.join("absent")).is_err(), "un chemin absent est refusé");

        // Et un lien symbolique est refusé, même s'il pointe sur un vrai dossier : c'est la règle
        // que le dialogue applique, donc celle que la voie de lancement doit appliquer aussi.
        #[cfg(unix)]
        {
            let link = base.join("lien");
            std::os::unix::fs::symlink(&real, &link).expect("lien symbolique");
            assert!(accept_root(link).is_err(), "un symlink est refusé comme racine");
        }

        fs::remove_dir_all(&base).expect("nettoyage");
    }

    /// Toute commande enregistrée doit être autorisée par l'ACL, sans exception.
    ///
    /// **Le défaut que ce test ferme.** `build.rs` tenait la liste à la main : dix commandes
    /// autorisées pour quarante-quatre enregistrées. Les trente-quatre autres étaient refusées à
    /// l'exécution par `Command <nom> not allowed by ACL` — le wizard, le parcours, le Doctor, le
    /// Capability Builder, l'éditeur de policies, le Gate Builder, le MCP Preview, la taxonomie,
    /// le Work Graph, la synchronisation mémoire. L'essentiel de l'application.
    ///
    /// L'ACL est désormais dérivée de `generate_handler!`, donc les deux ne peuvent plus diverger
    /// par construction. Ce test vérifie la dérivation elle-même : qu'elle lit bien la liste
    /// entière, et non une partie qu'elle aurait silencieusement tronquée.
    #[test]
    fn the_acl_authorises_every_registered_command() {
        let manifest = Path::new(env!("CARGO_MANIFEST_DIR"));
        let main_source = fs::read_to_string(manifest.join("src").join("main.rs")).expect("main.rs");
        let build_source = fs::read_to_string(manifest.join("build.rs")).expect("build.rs");

        let start = main_source.find("generate_handler![").expect("generate_handler!");
        let rest = &main_source[start + "generate_handler![".len()..];
        let end = rest.find(']').expect("crochet fermant");
        let registered: Vec<&str> = rest[..end].split(',').map(str::trim).filter(|item| !item.is_empty()).collect();

        // Le produit expose une large surface : un compte qui s'effondrerait signalerait que
        // l'extraction a cessé de mordre, pas que l'application a maigri.
        assert!(registered.len() >= 40, "{} commandes extraites, trop peu", registered.len());
        assert!(registered.contains(&"select_project"));
        assert!(registered.contains(&"preselected_project"));

        // Et `build.rs` ne doit plus tenir la moindre liste en dur : c'est la main-d'œuvre
        // manuelle qui avait divergé, pas la dérivation.
        assert!(
            build_source.contains("registered_commands"),
            "build.rs doit dériver l’ACL de generate_handler!"
        );
        for command in &registered {
            with_subtest_name(command);
        }

        // Et la capability doit accorder chacune d'elles. Générer les permissions ne suffit pas :
        // mesuré sur l'AppImage, avec les quarante-quatre `.toml` en place, l'invoke rendait
        // toujours `Command preselected_project not allowed by ACL`. Une permission qui existe
        // sans être accordée ne permet rien — deux verrous, et je n'en avais ouvert qu'un.
        let capability = fs::read_to_string(manifest.join("capabilities").join("desktop-main.json"))
            .expect("capability desktop-main");
        for command in &registered {
            let identifier = format!("\"allow-{}\"", command.replace('_', "-"));
            assert!(
                capability.contains(&identifier),
                "la capability n’accorde pas {command} ({identifier})"
            );
        }
    }

    /// Petit marqueur : nommer la commande examinée, faute de `subTest` en Rust.
    fn with_subtest_name(command: &str) {
        assert!(!command.is_empty(), "commande vide dans generate_handler!");
        assert!(
            command.chars().all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '_'),
            "nom de commande inattendu : {command}"
        );
    }

    /// Le parcours des arguments, exercé sur les formes réelles plutôt que supposé correct.
    #[test]
    fn the_launch_flag_is_read_in_every_form_a_caller_writes_it() {
        use std::ffi::OsString;
        let nonce = SystemTime::now().duration_since(UNIX_EPOCH).expect("clock").as_nanos();
        let root = std::env::temp_dir().join(format!("vera-parse-{nonce}"));
        fs::create_dir_all(&root).expect("racine");
        let canonical = root.canonicalize().expect("racine canonique");
        let text = root.to_string_lossy().into_owned();
        let os = |value: &str| OsString::from(value);

        // `--project-root <chemin>`, la forme que la documentation donne.
        let separated = parse_preselected_root([os(PROJECT_ROOT_FLAG), os(&text)], None);
        assert_eq!(separated.expect("racine lue").expect("racine valide"), canonical);

        // `--project-root=<chemin>`, la forme que beaucoup écrivent par réflexe.
        let joined = parse_preselected_root([os(&format!("{PROJECT_ROOT_FLAG}={text}"))], None);
        assert_eq!(joined.expect("racine lue").expect("racine valide"), canonical);

        // Le drapeau reste lu quand il suit d'autres arguments.
        let after = parse_preselected_root([os("--autre"), os(PROJECT_ROOT_FLAG), os(&text)], None);
        assert_eq!(after.expect("racine lue").expect("racine valide"), canonical);

        // La variable sert de repli, et seulement de repli.
        let variable = parse_preselected_root(Vec::new(), Some(os(&text)));
        assert_eq!(variable.expect("racine lue").expect("racine valide"), canonical);

        // L'argument l'emporte sur la variable : ce qui est écrit sur la ligne gagne.
        let both = parse_preselected_root([os(PROJECT_ROOT_FLAG), os(&text)], Some(os("/inexistant")));
        assert_eq!(both.expect("racine lue").expect("racine valide"), canonical);

        // Un drapeau sans valeur est un refus nommé, jamais un silence.
        let bare = parse_preselected_root([os(PROJECT_ROOT_FLAG)], None).expect("refus attendu");
        assert!(bare.expect_err("valeur manquante").contains(PROJECT_ROOT_FLAG));
        let empty = parse_preselected_root([os(&format!("{PROJECT_ROOT_FLAG}="))], None).expect("refus attendu");
        assert!(empty.expect_err("valeur vide").contains(PROJECT_ROOT_FLAG));

        // Une variable vide n'est pas une désignation : le dialogue reste la voie.
        assert!(parse_preselected_root(Vec::new(), Some(OsString::new())).is_none());
        assert!(parse_preselected_root(Vec::new(), None).is_none());

        fs::remove_dir_all(&root).expect("nettoyage");
    }

    /// Sans argument ni variable, rien n'est présélectionné : le dialogue reste la seule voie.
    ///
    /// Le test tourne dans le processus de test, dont l'argv ne porte pas `--project-root` et dont
    /// l'environnement ne porte pas la variable. `None` est donc le comportement par défaut, et
    /// c'est ce qui garantit qu'aucun utilisateur ne voit son dialogue disparaître.
    #[test]
    fn nothing_is_preselected_by_default() {
        assert!(std::env::var_os(PROJECT_ROOT_VARIABLE).is_none(), "l’environnement de test est neutre");
        assert!(preselected_root().is_none(), "aucune racine présélectionnée par défaut");
    }

    /// Les deux noms publics sont un contrat : le bridge reçoit déjà `--project-root`.
    ///
    /// Si le drapeau de la fenêtre et celui du bridge divergeaient, la documentation dirait vrai
    /// pour l'un et faux pour l'autre.
    #[test]
    fn the_launch_flag_matches_the_flag_the_bridge_already_accepts() {
        assert_eq!(PROJECT_ROOT_FLAG, "--project-root");
        assert_eq!(PROJECT_ROOT_VARIABLE, "VERA_MMU_PROJECT_ROOT");
    }

    /// La résolution de l'interpréteur, mesurée sur ses trois cas.
    ///
    /// Sans ce test, le correctif ne serait vérifié que par un runner Windows — c'est-à-dire
    /// jamais localement, et une fois par run ailleurs.
    #[test]
    fn the_bridge_resolves_a_python_that_actually_runs() {
        // Un interpréteur est trouvé sur cette machine, et il exécute réellement du Python.
        let resolved = python_executable().expect("un interpréteur Python doit être résolu");
        assert!(runs_python(&resolved), "l’interpréteur résolu doit exécuter du Python");

        // La sonde distingue « exécute du Python » de « existe dans le PATH » : c'est toute la
        // différence entre un vrai interpréteur et l'alias Windows qui démarre puis quitte.
        assert!(!runs_python("vera-interpreteur-inexistant"), "un nom absent ne doit pas passer");
        assert!(!runs_python("echo"), "un exécutable qui n’est pas Python ne doit pas passer");

        // Et les deux noms essayés restent ceux que les trois plateformes utilisent.
        // Comparé comme tranche : réduire la liste doit faire tomber une assertion, pas
        // produire une erreur de type que l'on pourrait prendre pour un simple refus de compiler.
        assert_eq!(PYTHON_CANDIDATES.as_slice(), ["python3", "python"].as_slice());
    }

    #[test]
    fn debug_bridge_command_is_bound_to_the_vera_core_source() {
        let source = Path::new(env!("CARGO_MANIFEST_DIR")).ancestors().nth(3).expect("VERA root").to_path_buf();
        let command = BridgeExecutable::Source(source).command().expect("debug bridge command");
        #[cfg(debug_assertions)]
        {
            // L'interpréteur n'est plus épinglé par son nom mais par ce qu'il fait : `python3`
            // sur Linux et macOS, `python` sur Windows où le premier n'existe pas. Épingler la
            // chaîne aurait rendu le test vert là où le bridge ne démarre pas, et rouge là où il
            // démarre — exactement l'inverse de son objet.
            let program = command.get_program().to_string_lossy().into_owned();
            assert!(
                PYTHON_CANDIDATES.contains(&program.as_str()) || std::env::var(PYTHON_VARIABLE).is_ok(),
                "interpréteur inattendu : {program}"
            );
            assert!(runs_python(&program), "l’interpréteur retenu doit exécuter du Python");
            let arguments = command.get_args().map(|item| item.to_string_lossy()).collect::<Vec<_>>();
            assert_eq!(arguments, ["-m", "vera_mmu.desktop_bridge"]);
            let python_path = command
                .get_envs()
                .find_map(|(key, value)| (key == "PYTHONPATH").then_some(value).flatten())
                .expect("PYTHONPATH set");
            assert!(Path::new(python_path).ends_with("src"));
        }
    }
}
