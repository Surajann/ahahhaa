#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .setup(|_app| {
            // gtk-layer-shell setup would go here (anchor bottom-right, layer overlay, exclusiveZone 0)
            // Kept minimal for build without gtk-layer-shell crate in CI
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
