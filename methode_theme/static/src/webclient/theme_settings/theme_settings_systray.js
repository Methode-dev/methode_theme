  import { Component } from "@odoo/owl";
  import { registry } from "@web/core/registry";
  import { useService } from "@web/core/utils/hooks";
  import { ThemeSettingsDialog } from "@aura_backend_theme/webclient/theme_settings/theme_settings_dialog";

  // Aura opened this dialog from its own navbar (navbar.js:439), which we deleted.
  // The navbar belongs to methode_theme now, so the entry point does too.
  export class ThemeSettingsSystray extends Component {
      static template = "methode_theme.ThemeSettingsSystray";
      static props = {};

      setup() {
          this.dialog = useService("dialog");
      }

      openThemeSettings() {
          this.dialog.add(ThemeSettingsDialog, {});
      }
  }

  registry.category("systray").add(
      "methode_theme.theme_settings",
      { Component: ThemeSettingsSystray },
      { sequence: 50 },
  );