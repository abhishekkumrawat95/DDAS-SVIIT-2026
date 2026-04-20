; installer.nsi – NSIS installer script for DDAS
; ═══════════════════════════════════════════════════════════════════════════
; Requires NSIS 3.x   →  https://nsis.sourceforge.io/
; Build:   makensis installer.nsi
; Output:  dist\DDAS-Setup.exe
; ═══════════════════════════════════════════════════════════════════════════

Unicode True

; ── Product metadata ────────────────────────────────────────────────────────
!define PRODUCT_NAME        "DDAS"
!define PRODUCT_FULL_NAME   "DDAS - Data Download Duplication Alert System"
!define PRODUCT_VERSION     "1.0.0"
!define PUBLISHER           "SVIIT Team 2026"
!define INSTALL_DIR         "$PROGRAMFILES64\${PRODUCT_NAME}"
!define UNINSTALLER_NAME    "Uninstall DDAS.exe"
!define MAIN_EXE            "DDAS-Launcher.exe"
!define REG_ROOT            "HKLM"
!define REG_APP_KEY         "Software\Microsoft\Windows\CurrentVersion\App Paths\${MAIN_EXE}"
!define REG_UNINSTALL_KEY   "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define DIST_DIR            "dist\DDAS"           ; relative to where makensis is invoked

; ── Compression ─────────────────────────────────────────────────────────────
; Faster build-time compression to avoid very long stalls on large payloads.
; Trade-off: installer size may be larger than SOLID LZMA.
SetCompressor /FINAL zlib
SetCompress auto

; ── General attributes ───────────────────────────────────────────────────────
Name "${PRODUCT_FULL_NAME}"
OutFile "dist\DDAS-Setup.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey ${REG_ROOT} "${REG_APP_KEY}" ""
RequestExecutionLevel admin
ShowInstDetails show
ShowUnInstDetails show
BrandingText "${PRODUCT_FULL_NAME} ${PRODUCT_VERSION}"

; ── Pages ────────────────────────────────────────────────────────────────────
Page license
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

; ── License page ─────────────────────────────────────────────────────────────
LicenseText "Please review the licence before installing ${PRODUCT_NAME}."
LicenseData "INSTALLATION_GUIDE.md"   ; shown as plain-text licence page

; ═══════════════════════════════════════════════════════════════════════════
;  INSTALL SECTION
; ═══════════════════════════════════════════════════════════════════════════
Section "Install ${PRODUCT_NAME}" SecMain

  SectionIn RO   ; mandatory section

  SetOutPath "$INSTDIR"

  ; ── Copy all files from the PyInstaller output folder ────────────────────
  File /r "${DIST_DIR}\*.*"

  ; ── Write uninstaller ────────────────────────────────────────────────────
  WriteUninstaller "$INSTDIR\${UNINSTALLER_NAME}"

  ; ── Registry: App Paths (lets Windows find the EXE) ─────────────────────
  WriteRegStr ${REG_ROOT} "${REG_APP_KEY}" "" "$INSTDIR\${MAIN_EXE}"
  WriteRegStr ${REG_ROOT} "${REG_APP_KEY}" "Path" "$INSTDIR"

  ; ── Registry: Add/Remove Programs entry ─────────────────────────────────
  WriteRegStr   ${REG_ROOT} "${REG_UNINSTALL_KEY}" "DisplayName"          "${PRODUCT_FULL_NAME}"
  WriteRegStr   ${REG_ROOT} "${REG_UNINSTALL_KEY}" "DisplayVersion"       "${PRODUCT_VERSION}"
  WriteRegStr   ${REG_ROOT} "${REG_UNINSTALL_KEY}" "Publisher"            "${PUBLISHER}"
  WriteRegStr   ${REG_ROOT} "${REG_UNINSTALL_KEY}" "InstallLocation"      "$INSTDIR"
  WriteRegStr   ${REG_ROOT} "${REG_UNINSTALL_KEY}" "UninstallString"      '"$INSTDIR\${UNINSTALLER_NAME}"'
  WriteRegStr   ${REG_ROOT} "${REG_UNINSTALL_KEY}" "QuietUninstallString" '"$INSTDIR\${UNINSTALLER_NAME}" /S'
  WriteRegDWORD ${REG_ROOT} "${REG_UNINSTALL_KEY}" "NoModify"             1
  WriteRegDWORD ${REG_ROOT} "${REG_UNINSTALL_KEY}" "NoRepair"             1

  ; ── Start Menu shortcuts (all users) ────────────────────────────────────
  ; Use $COMMONPROGRAMDATA so shortcuts appear for every user account.
  CreateDirectory "$COMMONPROGRAMDATA\Microsoft\Windows\Start Menu\Programs\${PRODUCT_NAME}"

  CreateShortCut  "$COMMONPROGRAMDATA\Microsoft\Windows\Start Menu\Programs\${PRODUCT_NAME}\DDAS Launcher.lnk" \
                  "$INSTDIR\${MAIN_EXE}" "" \
                  "$INSTDIR\${MAIN_EXE}" 0 \
                  SW_SHOWNORMAL "" \
                  "Launch DDAS application"

  CreateShortCut  "$COMMONPROGRAMDATA\Microsoft\Windows\Start Menu\Programs\${PRODUCT_NAME}\DDAS Dashboard.lnk" \
                  "$INSTDIR\DDAS-Dashboard.exe" "" \
                  "$INSTDIR\DDAS-Dashboard.exe" 0 \
                  SW_SHOWNORMAL "" \
                  "Open DDAS Dashboard"

  CreateShortCut  "$COMMONPROGRAMDATA\Microsoft\Windows\Start Menu\Programs\${PRODUCT_NAME}\DDAS Chatbot.lnk" \
                  "$INSTDIR\DDAS-Chatbot.exe" "" \
                  "$INSTDIR\DDAS-Chatbot.exe" 0 \
                  SW_SHOWNORMAL "" \
                  "Open DDAS Chatbot"

  CreateShortCut  "$COMMONPROGRAMDATA\Microsoft\Windows\Start Menu\Programs\${PRODUCT_NAME}\Uninstall DDAS.lnk" \
                  "$INSTDIR\${UNINSTALLER_NAME}" "" \
                  "$INSTDIR\${UNINSTALLER_NAME}" 0

  ; Desktop shortcut (current user only – each user can create their own)
  CreateShortCut  "$DESKTOP\DDAS Launcher.lnk" \
                  "$INSTDIR\${MAIN_EXE}" "" \
                  "$INSTDIR\${MAIN_EXE}" 0 \
                  SW_SHOWNORMAL "" \
                  "Launch DDAS"

  ; ── Grant all users write access to the DDAS data directory ─────────────
  ; This prevents 'Permission denied' errors when a non-admin user starts DDAS.
  CreateDirectory "$COMMONAPPDATA\DDAS"
  ExecWait 'icacls "$COMMONAPPDATA\DDAS" /grant Users:(OI)(CI)F /T /C /Q'

  ; ── Auto-start registry entry (system-wide, runs monitor on every boot) ──
  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Run" \
              "DDASMonitor" '"$INSTDIR\DDAS-Monitor.exe" monitor'

SectionEnd

; ── Optional: Windows Service ─────────────────────────────────────────────
Section /o "Install as Windows Service (auto-start on boot)" SecService

  ExecWait '"$INSTDIR\DDAS-Monitor.exe" install'
  ExecWait '"$INSTDIR\DDAS-Monitor.exe" start'
  DetailPrint "DDAS monitor service installed and started."

SectionEnd

; ═══════════════════════════════════════════════════════════════════════════
;  UNINSTALL SECTION
; ═══════════════════════════════════════════════════════════════════════════
Section "Uninstall"

  ; Stop and remove Windows service if it is installed
  ExecWait '"$INSTDIR\DDAS-Monitor.exe" stop'
  ExecWait '"$INSTDIR\DDAS-Monitor.exe" remove'

  ; Remove auto-start registry entry
  DeleteRegValue HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Run" "DDASMonitor"

  ; Remove Start Menu shortcuts (all-users path)
  RMDir /r "$COMMONPROGRAMDATA\Microsoft\Windows\Start Menu\Programs\${PRODUCT_NAME}"

  ; Remove Desktop shortcut
  Delete "$DESKTOP\DDAS Launcher.lnk"

  ; Remove registry keys
  DeleteRegKey ${REG_ROOT} "${REG_APP_KEY}"
  DeleteRegKey ${REG_ROOT} "${REG_UNINSTALL_KEY}"

  ; Remove installed files (keep user data in %PROGRAMDATA%\DDAS)
  RMDir /r "$INSTDIR"

  MessageBox MB_OK "DDAS has been uninstalled.$\nYour database and logs in %PROGRAMDATA%\DDAS were preserved."

SectionEnd
