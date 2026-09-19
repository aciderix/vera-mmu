//! Construit l’ACL Tauri depuis la **seule** liste qui fasse autorité : celle de `main.rs`.
//!
//! Tauri v2 refuse toute commande absente du manifeste d’application, et ce manifeste était tenu
//! à la main. Il listait dix commandes ; `generate_handler!` en enregistrait quarante-quatre.
//! **Trente-quatre étaient donc refusées à l’exécution** — le wizard, le parcours, le Doctor, le
//! Capability Builder, l’éditeur de policies, le Gate Builder, le MCP Preview, la taxonomie, le
//! Work Graph, la synchronisation mémoire : l’essentiel de l’application.
//!
//! Mesuré sur l’AppImage sous écran virtuel : `Command preselected_project not allowed by ACL`.
//! Le défaut était resté invisible parce que la fenêtre rendait toute erreur par un « Opération
//! locale refusée. » sans cause, parce qu’aucun test n’exerçait l’interface contre son backend, et
//! parce que `cargo test` ne tournait pas en CI. Trois silences superposés.
//!
//! Deux listes à tenir d’accord sont deux listes qui divergeront. Celle-ci est donc **dérivée** de
//! `generate_handler!`, et `tests::the_acl_authorises_every_registered_command` vérifie que la
//! dérivation lit bien ce qu’elle prétend lire.

use std::path::Path;

/// Extrait les noms de commandes de l’unique `generate_handler![...]` de `main.rs`.
///
/// Volontairement strict : toute forme inattendue fait échouer la construction plutôt que de
/// produire une ACL silencieusement partielle — c’est exactement ce qui vient d’être mesuré.
fn registered_commands(source: &str) -> Vec<String> {
    let start = source
        .find("generate_handler![")
        .expect("main.rs doit enregistrer ses commandes par generate_handler!");
    let rest = &source[start + "generate_handler![".len()..];
    let end = rest.find(']').expect("generate_handler! doit être fermé");
    let commands: Vec<String> = rest[..end]
        .split(',')
        .map(|item| item.trim().to_string())
        .filter(|item| !item.is_empty())
        .collect();
    assert!(!commands.is_empty(), "aucune commande extraite de generate_handler!");
    for command in &commands {
        assert!(
            command.chars().all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '_'),
            "nom de commande inattendu dans generate_handler! : {command}"
        );
    }
    commands
}

fn main() {
    println!("cargo:rustc-env=VERA_SIDECAR_TARGET={}", std::env::var("TARGET").expect("target triple"));
    // Sans cette ligne, ajouter une commande à `main.rs` ne régénérerait pas l’ACL : le défaut
    // reviendrait sous une autre forme, et plus discrètement encore.
    println!("cargo:rerun-if-changed=src/main.rs");

    let source = std::fs::read_to_string(Path::new("src").join("main.rs")).expect("src/main.rs lisible");
    // `commands(&[&str])` exige `'static` : les noms sont donc fuités volontairement, une fois,
    // dans un script de build qui se termine aussitôt après.
    let commands: &'static [&'static str] = Vec::leak(
        registered_commands(&source)
            .into_iter()
            .map(|command| &*String::leak(command))
            .collect::<Vec<&'static str>>(),
    );

    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(commands)),
    )
    .expect("tauri build failed");
}
