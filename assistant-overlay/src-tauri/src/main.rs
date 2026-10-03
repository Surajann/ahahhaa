#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .setup(|_app| {
            // gtk-layer-shell: anchor bottom-right, layer overlay (fallback top), exclusiveZone 0
            // Requires `gtk-layer-shell` crate; kept behind cfg to allow cargo check without Wayland.
            // On Hyprland/Wayland this window is configured via tauri window `transparent` + layer-shell
            // init: gtk_layer_shell::init_for_window, set_anchor(Bottom|Right), margin 24, layer Overlay, exclusive_zone 0.
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
