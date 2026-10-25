# Local Markdown: Client Quickstart & User Guide

Welcome to **Local Markdown**! This guide walks you through installing, running, and getting the most out of Local Markdown on your Windows computer.

---

## 1. What Local Markdown Does

Local Markdown takes your everyday office documents, spreadsheets, presentations, PDFs, and scanned photos, and transforms them into clean, structured Markdown text. This Markdown is formatted specifically for feeding into Large Language Models (LLMs like ChatGPT, Claude, Gemini, or local models) or vector search systems.

### Privacy & Offline Guarantee
- **100% Offline**: The app never connects to the internet.
- **Zero Cloud Services**: No files or data ever leave your device.
- **Non-Destructive**: Your original files are never altered, moved, or deleted.

---

## 2. Installing the Application

### Option A: Setup Installer (Recommended)
1. Double-click `LocalMarkdown-Setup-1.0.0-x64.exe`.
2. If Windows SmartScreen appears:
   - Click **More info**.
   - Click **Run anyway**. *(This happens because the app is freshly compiled and not signed with an enterprise certificate).*
3. Follow the setup prompts. The installer installs the application into your local user folder without needing administrator permissions.
4. Launch the app from your Desktop shortcut or Start menu.

### Option B: Portable Version (Zero Installation)
1. Extract `LocalMarkdown-Portable-1.0.0-x64.zip` to any folder on your computer or a USB drive.
2. Open the extracted folder and double-click `LocalMarkdown.exe`.

---

## 3. How to Convert Documents

```
+----------------------------------------------------------------------------------------------------+
| [M↓] Local Markdown                        [● 100% Offline & Private]   [🧹 Clear history]        |
+----------------------------------------------------------------------------------------------------+
| [+ Add files]  [▶ Convert All (2)]  [⏹ Stop]  [🔍 Try scan reading] | [📋 Copy]  [💾 Save]  [📦 ZIP] |
+----------------------------------------------------------------------------------------------------+
```

### Step 1: Add Your Files
You can add files in two ways:
- **Drag and Drop**: Drag files from File Explorer directly into the app window.
- **Browse**: Click the **+ Add files** button in the top left and select your documents.

**Supported File Types**:
- **Word**: `.docx`, `.doc`
- **PDF**: Digital PDFs and scanned documents
- **Excel**: `.xlsx`, `.xls`
- **PowerPoint**: `.pptx`, `.ppt`
- **Images**: `.png`, `.jpg`, `.jpeg`

---

### Step 2: Convert to Markdown
- Click the prominent green **▶ Convert All** button.
- The button will display the number of queued documents (e.g., `Convert All (3)`).
- During conversion, the status column will show progress:
  - `⟳ Converting...`: Currently being processed.
  - `✓ Ready to save`: Successfully converted.
  - `⚠ Review scan`: Converted with OCR; verify formatting if the original image was blurry.
  - `✕ Failed`: The file was corrupt or protected. Hover over the status to see the explanation.

---

### Step 3: Preview the Markdown
- Click on any completed file in the queue.
- The right-hand **Markdown Preview** pane will instantly display the extracted text, word count, character count, and formatting.

---

### Step 4: Export Your Markdown
You have three ways to export your results:
1. **Copy Markdown (`📋 Copy Markdown`)**:
   Copies the currently previewed Markdown text directly to your clipboard. A green `✓ Copied!` confirmation will appear.
2. **Save Markdown (`💾 Save Markdown`)**:
   Saves the selected document as a standalone `.md` file on your computer.
3. **Save all as ZIP (`📦 Save all as ZIP`)**:
   Exports all successfully converted documents into a single ZIP archive. The ZIP also includes a `conversion-summary.txt` report listing every converted document, its original format, and any notes.

---

## 4. Special Features

### Reading Scanned Pages ("Try scan reading")
If you have a scanned PDF (where the text is baked into an image rather than selectable digital text) or an image file:
1. Select the file in the queue.
2. Click **🔍 Try scan reading**.
3. Local Markdown will use its built-in, offline Tesseract OCR engine to read and extract the text.

### Stopping a Conversion
If you accidentally started converting a very large batch, click **⏹ Stop**. The app will safely finish any file currently writing and leave all finished files intact.

### Clearing History
Click **🧹 Clear history** in the top-right corner to clear the app's cache and reset the queue.
- **Your originals are untouched**: Clearing history only removes the app's temporary scratch files and saved preview records. Your original documents and any `.md` or `.zip` files you saved remain safe.

---

## 5. Security & Safety Notes

- **Macros are Blocked**: To keep your system safe, files containing VBA macros (like `.docm` or `.xlsm`) are automatically rejected.
- **Password Protection**: Encrypted or password-protected files cannot be read without the password and will be flagged as failed.
- **No Internet Required**: You can disconnect your Wi-Fi or pull your ethernet cable, and Local Markdown will function completely normally.
