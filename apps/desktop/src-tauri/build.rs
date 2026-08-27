fn main() {
    println!("cargo:rustc-env=VERA_SIDECAR_TARGET={}", std::env::var("TARGET").expect("target triple"));
    tauri_build::try_build(
        tauri_build::Attributes::new().app_manifest(
            tauri_build::AppManifest::new().commands(&[
                "select_project",
                "scan_project",
                "initialization_preview",
                "initialization_apply",
                "agent_profiles",
                "generation_preview",
                "stage_adapter",
                "installation_preview",
                "installation_apply",
                "adapter_doctor",
            ]),
        ),
    )
    .expect("tauri build failed");
}
