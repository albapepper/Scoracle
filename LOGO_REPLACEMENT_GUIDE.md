# Logo Replacement Guide

## Overview
Replace the current logo (`frontend/public/scoracle-logo.png`) with the new stylized logo featuring two hands framing a geometric 'S' emblem.

## Steps to Process the Image

### Option 1: Online Tools (Easiest)
1. **Remove.bg** (https://www.remove.bg/)
   - Upload your image
   - It will automatically detect and remove the background
   - Download as PNG with transparency

2. **Photopea** (https://www.photopea.com/) - Free online Photoshop alternative
   - Open your image
   - Use Magic Wand tool to select the cream background
   - Delete the selection
   - Export as PNG with transparency enabled

### Option 2: Image Editing Software
**Photoshop:**
1. Open the image
2. Select the background using Magic Wand or Quick Selection tool
3. Delete or mask the background
4. Save as PNG-24 with transparency

**GIMP (Free):**
1. Open the image
2. Right-click layer → Add Alpha Channel
3. Select background with Fuzzy Select tool
4. Delete selection
5. Export as PNG

### Option 3: Command Line (if you have ImageMagick)
```bash
# Install ImageMagick first, then:
magick input.png -fuzz 10% -transparent "#F5F3ED" output.png
```
Replace `#F5F3ED` with the exact cream color from your image.

## File Requirements
- **Format**: PNG with transparency
- **Filename**: `scoracle-logo.png`
- **Location**: `frontend/public/scoracle-logo.png`
- **Recommended Size**: At least 200px height (will be scaled to 54px in header)
- **Background**: Fully transparent

## After Replacing
1. Replace `frontend/public/scoracle-logo.png` with your processed image
2. The header will automatically use the new logo
3. Test in both light and dark modes to ensure visibility

## Design Notes
Based on the description, the new logo features:
- Two stylized hands framing a circular emblem
- Geometric capital 'S' in dark green
- Golden-brown/mustard yellow hands with texture
- Cream/yellow circle with radiating lines
- Thick dark green outlines

The transparent background will allow the logo to blend seamlessly with the Anthropic-inspired theme's clean backgrounds.

