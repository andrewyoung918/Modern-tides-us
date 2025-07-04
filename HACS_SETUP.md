# HACS Setup Instructions

## Repository Configuration

### 1. GitHub Repository Settings

1. Go to https://github.com/ALArvi019/moderntides
2. Click the ⚙️ (Settings) button in the repository
3. In the "About" section, click the ⚙️ next to "About"
4. Add the following:

**Description:**
```
Modern Home Assistant integration for real-time tide information from Spanish maritime stations
```

**Topics:**
- `home-assistant`
- `hacs`
- `tide`
- `sensor`
- `camera`
- `integration`
- `custom-component`

### 2. Brands Repository (Optional but recommended)

To be included in the official Home Assistant brands:

1. Fork https://github.com/home-assistant/brands
2. Create directory: `custom_integrations/moderntides/`
3. Copy the following files to that directory:
   - `icon.png` (from images/icon.png)
   - `logo.png` (from images/logo.png)
   - `manifest.json` (copy content from brands_manifest.json)
4. Create a PR to the brands repository

### 3. Files Fixed

✅ **hacs.json** - Removed invalid keys (`domains`, `iot_class`)
✅ **brands_manifest.json** - Created for brands repository submission

### 4. Validation Status

After completing steps 1-2, all HACS validation errors should be resolved:

- ✅ Repository topics
- ✅ Repository description  
- ✅ HACS JSON validation
- ✅ Brands repository (if submitted)

### 5. Submit to HACS

Once all validations pass, you can submit your integration to HACS:
1. Go to https://github.com/hacs/default
2. Follow the submission process in their README
