import streamlit as st
import base64
from io import BytesIO
from PIL import Image, ImageDraw

# Page configuration
st.set_page_config(
    page_title="Cozy Journal Login",
    page_icon="🍂",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for pixel art styling
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    /* Hide Streamlit's default elements */
    .stDeployButton {display: none;}
    .stDecoration {display: none;}
    header {display: none;}
    .stMainBlockContainer {padding: 0;}
    
    /* Main container styling */
    .stApp {
        background: repeating-linear-gradient(
            45deg,
            #FFB366 0px,
            #FFB366 20px,
            #FFFFFF 20px,
            #FFFFFF 40px
        );
        animation: plaidShift 20s linear infinite;
    }
    
    @keyframes plaidShift {
        0% { background-position: 0px 0px; }
        100% { background-position: 40px 40px; }
    }
    
    /* Falling leaves animation */
    .falling-leaves {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 1;
    }
    
    .leaf {
        position: absolute;
        width: 20px;
        height: 20px;
        background: #D2691E;
        transform-origin: center;
        animation: fall linear infinite;
        image-rendering: pixelated;
    }
    
    .leaf:before {
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        background: 
            linear-gradient(45deg, #D2691E 25%, transparent 25%),
            linear-gradient(-45deg, #D2691E 25%, transparent 25%),
            linear-gradient(45deg, transparent 75%, #D2691E 75%),
            linear-gradient(-45deg, transparent 75%, #D2691E 75%);
        background-size: 4px 4px;
        background-position: 0 0, 0 2px, 2px -2px, -2px 0px;
    }
    
    @keyframes fall {
        0% {
            transform: translateY(-100vh) rotate(0deg);
            opacity: 1;
        }
        100% {
            transform: translateY(100vh) rotate(360deg);
            opacity: 0;
        }
    }
    
    /* Login container */
    .login-container {
        position: relative;
        z-index: 10;
        display: flex;
        min-height: 100vh;
        align-items: center;
        justify-content: center;
    }
    
    .login-box {
        background: rgba(255, 255, 255, 0.95);
        border: 8px solid #8B4513;
        border-image: url("data:image/svg+xml,%3csvg width='100' height='100' xmlns='http://www.w3.org/2000/svg'%3e%3cdefs%3e%3cpattern id='checkerboard' patternUnits='userSpaceOnUse' width='8' height='8'%3e%3crect width='4' height='4' fill='%238B4513'/%3e%3crect x='4' y='4' width='4' height='4' fill='%238B4513'/%3e%3c/pattern%3e%3c/defs%3e%3crect width='100' height='100' fill='url(%23checkerboard)'/%3e%3c/svg%3e") 8;
        box-shadow: 0 0 20px rgba(0,0,0,0.3);
        padding: 40px;
        text-align: center;
        image-rendering: pixelated;
        font-family: 'Orbitron', monospace;
    }
    
    /* Tree container */
    .tree-container {
        position: fixed;
        left: 50px;
        top: 50%;
        transform: translateY(-50%);
        z-index: 5;
        image-rendering: pixelated;
    }
    
    /* Pixel art button styling */
    .stButton > button {
        background: linear-gradient(45deg, #D2691E 50%, #FF6347 50%);
        background-size: 8px 8px;
        border: 4px solid #8B4513;
        border-radius: 0;
        color: white;
        font-family: 'Orbitron', monospace;
        font-weight: bold;
        font-size: 16px;
        text-transform: uppercase;
        letter-spacing: 2px;
        padding: 12px 24px;
        image-rendering: pixelated;
        cursor: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect width="16" height="16" fill="brown"/></svg>') 8 8, auto;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #FF6347 50%, #D2691E 50%);
        transform: translate(2px, 2px);
        box-shadow: -2px -2px 0px #8B4513;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        background: white;
        border: 4px solid #8B4513;
        border-radius: 0;
        font-family: 'Orbitron', monospace;
        font-size: 16px;
        image-rendering: pixelated;
        padding: 12px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #D2691E;
        box-shadow: 0 0 0 2px #FFB366;
    }
    
    /* Labels */
    .stTextInput > label {
        font-family: 'Orbitron', monospace;
        font-weight: bold;
        color: #8B4513;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Title styling */
    h1 {
        font-family: 'Orbitron', monospace;
        color: #8B4513;
        text-shadow: 2px 2px 0px #FFB366;
        font-size: 3em;
        margin-bottom: 30px;
        image-rendering: pixelated;
    }
    
    </style>
    """, unsafe_allow_html=True)

# Generate pixelated autumn tree as base64
def create_pixel_tree():
    # Create a simple pixelated tree
    img = Image.new('RGBA', (200, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Tree trunk (brown pixels)
    trunk_color = (101, 67, 33, 255)
    for x in range(90, 110):
        for y in range(200, 280):
            if (x + y) % 4 == 0:  # Pixelated effect
                draw.point((x, y), trunk_color)
    
    # Tree leaves (autumn colors)
    leaf_colors = [
        (218, 165, 32, 255),   # goldenrod
        (255, 140, 0, 255),    # orange
        (220, 20, 60, 255),    # crimson
        (139, 69, 19, 255),    # saddle brown
    ]
    
    # Draw pixelated leaves
    import random
    random.seed(42)  # For consistent results
    for x in range(50, 150):
        for y in range(50, 200):
            # Create a rough circular canopy
            center_x, center_y = 100, 125
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            if distance < 60 and random.random() > 0.3:
                if (x + y) % 3 == 0:  # More pixelated effect
                    color = random.choice(leaf_colors)
                    draw.point((x, y), color)
    
    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# Generate falling leaves HTML
def create_falling_leaves():
    leaves_html = '<div class="falling-leaves">'
    import random
    random.seed(42)  # For consistent positioning
    
    for i in range(15):
        left = random.randint(0, 100)
        delay = random.randint(0, 20)
        duration = random.randint(8, 15)
        leaves_html += f'''
        <div class="leaf" style="
            left: {left}%; 
            animation-delay: {delay}s; 
            animation-duration: {duration}s;
        "></div>
        '''
    
    leaves_html += '</div>'
    return leaves_html

# Main login page
def main():
    load_css()
    
    # Add falling leaves
    st.markdown(create_falling_leaves(), unsafe_allow_html=True)
    
    # Create tree image
    tree_base64 = create_pixel_tree()
    
    # Add tree to the left side
    st.markdown(f'''
    <div class="tree-container">
        <img src="{tree_base64}" width="200" style="image-rendering: pixelated;">
    </div>
    ''', unsafe_allow_html=True)
    
    # Optional soft lofi music (using a free online stream)
    st.markdown('''
    <audio autoplay loop style="display: none;">
        <source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.wav" type="audio/wav">
        Your browser does not support the audio element.
    </audio>
    ''', unsafe_allow_html=True)
    
    # Main login container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        st.markdown("# 🍂 Cozy Journal")
        st.markdown("### Welcome Back")
        
        # Audio control toggle
        audio_enabled = st.checkbox("🎵 Enable ambient sounds", value=False)
        
        if audio_enabled:
            st.markdown('''
            <script>
                const audio = document.querySelector('audio');
                if (audio) {
                    audio.volume = 0.3;
                    audio.play();
                }
            </script>
            ''', unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                login_button = st.form_submit_button("🍁 Enter Journal", use_container_width=True)
            
            if login_button:
                if username and password:
                    st.success("🎃 Welcome to your cozy journal!")
                    st.balloons()
                else:
                    st.error("📝 Please fill in all fields")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()