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
                let mut command = Command::new("python3");
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

fn folder_dialog() -> Result<PathBuf, String> {
    let folder = rfd::FileDialog::new().set_title("Choisir le dossier du projet VERA").pick_folder().ok_or_else(|| "Sélection de projet annulée.".to_string())?;
    if folder.is_symlink() || !folder.is_dir() { return Err("Dossier sélectionné invalide ou symlinké.".to_string()); }
    folder.canonicalize().map_err(|_| "Dossier sélectionné introuvable.").map_err(str::to_string)
}

fn with_bridge<T>(state: &State<'_, AppState>, f: impl FnOnce(&mut BridgeSession) -> Result<T, String>) -> Result<T, String> {
    let mut guard = state.session.lock().map_err(|_| "État bridge verrouillé de façon ambiguë.".to_string())?;
    f(guard.as_mut().ok_or_else(|| "Aucun projet local associé.".to_string())?)
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
        .invoke_handler(tauri::generate_handler![select_project, scan_project, project_status, initialization_preview, initialization_apply, agent_profiles, generation_preview, stage_adapter, installation_preview, installation_apply, adapter_doctor, memory_sync])
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
        assert_eq!(result.get("format").and_then(Value::as_str), Some("vera-scan-report/v1"));
        assert_eq!(result.get("status").and_then(Value::as_str), Some("OBSERVED"));
        drop(bridge);
        fs::remove_dir_all(root).expect("temporary root cleanup");
    }

    #[test]
    fn debug_bridge_command_is_bound_to_the_vera_core_source() {
        let source = Path::new(env!("CARGO_MANIFEST_DIR")).ancestors().nth(3).expect("VERA root").to_path_buf();
        let command = BridgeExecutable::Source(source).command().expect("debug bridge command");
        #[cfg(debug_assertions)]
        {
            assert_eq!(command.get_program(), "python3");
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
