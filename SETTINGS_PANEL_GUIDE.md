# Settings Panel Implementation - VAJRA

## ✅ Completed Tasks

### 1. Settings Button Added to Top Bar (⚙️)
- **Location**: Top right corner, next to notification button (🔔)
- **Position**: Added to `ui/main_window.py` line 112-130
- **Styling**: Gray icon (#9CA3AF) that highlights on hover (#E5E7EB)
- **Action**: Click to display settings dropdown panel

### 2. Settings Panel Fully Implemented (`ui/settings_panel.py`)
- **Size**: 380px width, auto-height
- **Display**: Popup that appears below the ⚙️ button
- **Auto-hide**: Closes when focus is lost (click elsewhere)
- **Styling**: Consistent with VAJRA dark theme

## 📋 Available Settings

### Scan Settings
| Setting | Type | Default | Range |
|---------|------|---------|-------|
| Default Timeout (seconds) | SpinBox | 300s | 30s - 3600s |
| Enable Parallel Scanning | Checkbox | OFF | - |
| Max Threads | SpinBox | 4 | 1-16 |

### Output Settings
| Setting | Type | Default |
|---------|------|---------|
| Auto-generate HTML Reports | Checkbox | ✓ ON |
| Export JSON Data | Checkbox | ✓ ON |
| Output Directory | Display | /tmp/Vajra-results |

### UI Preferences
| Setting | Type | Default |
|---------|------|---------|
| Auto-scroll Output | Checkbox | ✓ ON |
| Show Notifications | Checkbox | ✓ ON |
| Theme | Combo | Dark (Default) |

### Tool Settings
| Setting | Type | Default |
|---------|------|---------|
| Nmap: Enable Aggressive Scan | Checkbox | OFF |
| HTTPX: Follow Redirects | Checkbox | ✓ ON |
| Screenshot Threads | SpinBox | 5 | 1-20 |

## 🎨 UI Layout Structure

```
⚙️ Settings Panel
├─ Header: "⚙️ Settings"
├─ [Divider]
├─ Scan Settings
│  ├─ Default Timeout (seconds): [300] ▲▼
│  ├─ ☐ Enable Parallel Scanning
│  └─ Max Threads: [4] ▲▼
├─ [Divider]
├─ Output Settings
│  ├─ ☑ Auto-generate HTML Reports
│  ├─ ☑ Export JSON Data
│  └─ Output Directory: /tmp/Vajra-results
├─ [Divider]
├─ UI Preferences
│  ├─ ☑ Auto-scroll Output
│  ├─ ☑ Show Notifications
│  └─ Theme: [Dark (Default) ▼]
├─ [Divider]
├─ Tool Settings
│  ├─ ☐ Nmap: Enable Aggressive Scan
│  ├─ ☑ HTTPX: Follow Redirects
│  └─ Screenshot Threads: [5] ▲▼
└─ [💾 Save Settings Button]
```

## 🔗 Integration Points

### Main Window Integration
```python
# From ui/main_window.py

# 1. Import
from ui.settings_panel import SettingsPanel

# 2. Create button in top bar
self.settings_btn = QPushButton("⚙️")
self.settings_btn.setFixedSize(32, 32)
top_layout.addWidget(self.settings_btn)

# 3. Initialize panel
self.settings_panel = SettingsPanel(self)

# 4. Connect signal
self.settings_btn.clicked.connect(
    lambda: self.settings_panel.show_below(self.settings_btn)
)
```

### Methods Used
- **`show_below(anchor_widget)`**: Positions panel below the settings button
- **`focusOutEvent(event)`**: Auto-hides panel when focus is lost

## 🎯 Usage Examples

### Access Settings from Anywhere
```python
# Get a setting value (in any module)
if self.parent().settings_panel.notify_check.isChecked():
    # Show notification...
    pass

# Set a setting value
self.parent().settings_panel.timeout_spin.setValue(600)
```

### Connect Settings to Modules (Future)
Each module can connect to settings changes:
```python
# In any module view class
def __init__(self, parent=None):
    super().__init__(parent)
    main_window = self.parent()
    
    # Monitor timeout setting
    main_window.settings_panel.timeout_spin.valueChanged.connect(
        self._on_timeout_changed
    )

def _on_timeout_changed(self, new_value):
    self.timeout = new_value
    self.notification_manager.show_toast(f"Timeout updated to {new_value}s")
```

## 📌 Settings Categories Breakdown

### Why These Settings?

**Scan Settings**
- Timeout: Different tools need different time allocations
- Parallel: For batch scanning multiple targets
- Threads: Balance between speed and system load

**Output Settings**
- Reports: Generate professional HTML reports for clients
- JSON: Machine-readable format for further processing
- Directory: Centralized result storage location

**UI Preferences**
- Auto-scroll: Follow output as tools run
- Notifications: Toast alerts for completion
- Theme: Future expansion (Light/Dark modes)

**Tool Settings**
- Nmap Aggressive: -A flag for detailed OS/version info
- HTTPX Redirects: Follow HTTP redirects to final page
- Screenshot Threads: Eyewitness thread count (high = fast but resource-heavy)

## 🚀 Future Enhancements

1. **Persistence**: Save settings to JSON config file
   ```python
   # Save on button click
   settings_data = {
       'timeout': self.timeout_spin.value(),
       'parallel': self.parallel_check.isChecked(),
       'threads': self.threads_spin.value(),
       # ... more settings
   }
   with open('config.json', 'w') as f:
       json.dump(settings_data, f)
   ```

2. **Module Integration**: Connect settings to actual module behavior
   ```python
   # In modules/whois.py, use setting from main window
   timeout = self.parent().parent().settings_panel.timeout_spin.value()
   ```

3. **Profiles**: Save/load different setting profiles
   - Aggressive Recon
   - Stealth Mode
   - Quick Scan
   - Detailed Analysis

4. **Advanced Settings**: Additional categories
   - Network Settings (proxies, user agents)
   - Database Integration (API keys, credentials)
   - Report Templates (custom branding)

## ✅ File Changes Summary

| File | Changes |
|------|---------|
| `ui/settings_panel.py` | Created with 250 lines of full implementation |
| `ui/main_window.py` | Added settings button (⚙️) and panel initialization |
| **Total UI Files** | 7 (main_window, notification, settings_panel, sidebar, tgtinput, worker, __init__) |

---

**Status**: ✅ Complete and Ready for Use

The settings panel is now visible in the UI next to the notifications button and includes all important configuration options for VAJRA's scanning and output behavior.
