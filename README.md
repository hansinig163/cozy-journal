# Cozy Journal - Pixel Art Login Page

A beautiful pixel art styled Streamlit login page with autumn theme, featuring:

- **Light orange & white plaid background** with animated shifting pattern
- **Pixelated autumn tree** created procedurally and encoded as base64 for compatibility
- **Falling leaf sprites** with CSS animations drifting gently across the screen
- **Pixel art styled UI elements** including fonts, buttons, and input fields
- **Optional ambient sounds** toggle for atmospheric experience
- **Responsive design** that works both locally and when deployed

## Features

✨ **Pixel Art Styling**: All UI elements use pixel art fonts (Orbitron) and custom CSS for retro aesthetics  
🍂 **Autumn Theme**: Warm orange/brown color palette with leaf animations  
🌳 **Procedural Tree**: Half-pixelated autumn tree generated with PIL and base64 encoded  
🎵 **Optional Audio**: Checkbox to enable ambient sounds  
📱 **Compatible**: Works locally and when deployed (base64 assets)  

## Installation & Usage

```bash
# Clone the repository
git clone https://github.com/hansinig163/cozy-journal.git
cd cozy-journal

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Screenshot

The login page features a beautiful pixel art design with:
- Animated plaid background pattern
- Pixelated autumn tree on the left side
- Falling leaf animations across the screen
- Retro-styled login form with username/password fields
- Success message with balloons animation

## Technical Details

- **Streamlit** for the web framework
- **Pillow (PIL)** for generating the pixelated tree image
- **Base64 encoding** for asset compatibility
- **CSS animations** for falling leaves and background effects
- **Orbitron font** from Google Fonts for pixel art typography

## Browser Compatibility

Works in all modern browsers with support for CSS3 animations and HTML5.