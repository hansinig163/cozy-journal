import streamlit as st
import sqlite3
import hashlib
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import streamlit.components.v1 as components

# ================================
# DATABASE SETUP AND CONNECTION
# ================================

def init_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect('journal.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create journal entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection."""
    return sqlite3.connect('journal.db')

# ================================
# AUTHENTICATION FUNCTIONS
# ================================

def hash_password(password: str, salt: bytes) -> str:
    """Hash a password using PBKDF2 with the given salt."""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex()

def create_user(username: str, password: str) -> bool:
    """Create a new user account."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            return False
        
        # Generate salt and hash password
        salt = os.urandom(32)
        password_hash = hash_password(password, salt)
        
        # Insert new user
        cursor.execute(
            'INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)',
            (username, salt.hex(), password_hash)
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user and return user data if successful."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, username, salt, password_hash FROM users WHERE username = ?',
            (username,)
        )
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            return None
        
        user_id, username, salt_hex, stored_hash = user_data
        salt = bytes.fromhex(salt_hex)
        
        # Verify password
        password_hash = hash_password(password, salt)
        if password_hash == stored_hash:
            return {'id': user_id, 'username': username}
        
        return None
    except Exception:
        return None

# ================================
# JOURNAL ENTRY FUNCTIONS
# ================================

def create_journal_entry(user_id: int, title: str, content: str) -> bool:
    """Create a new journal entry."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO journal_entries (user_id, title, content) VALUES (?, ?, ?)',
            (user_id, title, content)
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_user_entries(user_id: int, search_term: str = "") -> List[Dict[str, Any]]:
    """Get all journal entries for a user, optionally filtered by search term."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if search_term:
            cursor.execute('''
                SELECT id, title, content, created_at, updated_at 
                FROM journal_entries 
                WHERE user_id = ? AND (title LIKE ? OR content LIKE ?)
                ORDER BY updated_at DESC
            ''', (user_id, f'%{search_term}%', f'%{search_term}%'))
        else:
            cursor.execute('''
                SELECT id, title, content, created_at, updated_at 
                FROM journal_entries 
                WHERE user_id = ?
                ORDER BY updated_at DESC
            ''', (user_id,))
        
        entries = []
        for row in cursor.fetchall():
            entries.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'created_at': row[3],
                'updated_at': row[4]
            })
        
        conn.close()
        return entries
    except Exception:
        return []

def update_journal_entry(entry_id: int, title: str, content: str) -> bool:
    """Update an existing journal entry."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE journal_entries 
            SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (title, content, entry_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def delete_journal_entry(entry_id: int) -> bool:
    """Delete a journal entry."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM journal_entries WHERE id = ?', (entry_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

# ================================
# UI COMPONENTS AND STYLING
# ================================

def apply_custom_css():
    """Apply custom CSS styling with animations to the app."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@300;400;500;600&display=swap');
    
    .main {
        background: linear-gradient(135deg, #faf7f2, #f7f3eb, #f4efe4);
        font-family: 'Comfortaa', cursive;
        position: relative;
        min-height: 100vh;
    }
    
    .stApp {
        background: linear-gradient(135deg, #faf7f2, #f7f3eb, #f4efe4);
        position: relative;
    }
    
    .stApp::before {
        content: '🍂 🍁 🌰 ☕ 🍂 🍁 🌰 ☕';
        position: fixed;
        top: -50px;
        left: 0;
        width: 100%;
        height: 100vh;
        opacity: 0.3;
        font-size: 20px;
        animation: gentleFall 20s infinite linear;
        pointer-events: none;
        z-index: 0;
    }
    
    @keyframes gentleFall {
        0% { transform: translateY(-100px) rotate(0deg); }
        100% { transform: translateY(100vh) rotate(360deg); }
    }
    
    .title {
        color: #8b6914;
        font-size: 3em;
        font-weight: 600;
        text-align: center;
        margin-bottom: 25px;
        text-shadow: 2px 2px 6px rgba(218, 165, 127, 0.3);
        font-family: 'Caveat', cursive;
    }
    
    .subtitle {
        color: #a67c52;
        font-size: 1.3em;
        text-align: center;
        margin-bottom: 30px;
        font-weight: 400;
        font-family: 'Comfortaa', cursive;
    }
    
    .login-container {
        background: linear-gradient(145deg, #fff8f0, #fef6ed);
        padding: 40px;
        border-radius: 30px;
        box-shadow: 0 15px 35px rgba(218, 165, 127, 0.2);
        text-align: center;
        margin: 30px auto;
        max-width: 450px;
        border: 3px solid #f2e8d5;
        position: relative;
        z-index: 1;
        backdrop-filter: blur(10px);
    }
    
    .login-container::before {
        content: '☕ 🍂 ☕';
        position: absolute;
        top: -15px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(145deg, #fff8f0, #fef6ed);
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 18px;
        border: 2px solid #f2e8d5;
    }
    
    .entry-card {
        background: linear-gradient(145deg, #fff8f0, #fef6ed);
        padding: 20px;
        border-radius: 20px;
        margin: 15px 0;
        box-shadow: 0 6px 20px rgba(218, 165, 127, 0.12);
        border: 2px solid #f2e8d5;
        position: relative;
        z-index: 1;
    }
    
    .stTextInput > div > div > input {
        background: linear-gradient(145deg, #fefcf8, #fbf8f2) !important;
        border: 2px solid #e8d5b7 !important;
        border-radius: 20px !important;
        padding: 12px 20px !important;
        font-family: 'Comfortaa', cursive !important;
        color: #8b6914 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #d4af8c !important;
        box-shadow: 0 0 15px rgba(218, 165, 127, 0.3) !important;
    }
    
    .stTextArea > div > div > textarea {
        background: linear-gradient(145deg, #fefcf8, #fbf8f2) !important;
        border: 2px solid #e8d5b7 !important;
        border-radius: 20px !important;
        padding: 15px 20px !important;
        font-family: 'Comfortaa', cursive !important;
        color: #8b6914 !important;
        font-size: 16px !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #d4af8c !important;
        box-shadow: 0 0 15px rgba(218, 165, 127, 0.3) !important;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #f5c99b, #f2b885) !important;
        color: #8b6914 !important;
        border: 2px solid #e8d5b7 !important;
        border-radius: 25px !important;
        padding: 12px 30px !important;
        font-family: 'Comfortaa', cursive !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 6px 20px rgba(245, 201, 155, 0.4) !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #f2b885, #eea969) !important;
        box-shadow: 0 8px 25px rgba(238, 169, 105, 0.5) !important;
        transform: translateY(-2px) !important;
        border-color: #d4af8c !important;
    }
    
    .stTabs > div > div > div > div {
        background: linear-gradient(145deg, #fff8f0, #fef6ed) !important;
        border-radius: 20px 20px 0 0 !important;
        border: 2px solid #e8d5b7 !important;
        border-bottom: none !important;
        color: #8b6914 !important;
        font-family: 'Comfortaa', cursive !important;
        font-weight: 600 !important;
    }
    
    .stTabs > div > div > div > div[data-baseweb="tab-highlight"] {
        background: linear-gradient(45deg, #f5c99b, #f2b885) !important;
        border-radius: 20px 20px 0 0 !important;
    }
    
    .music-player {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(145deg, #fff8f0, #fef6ed);
        padding: 10px 20px;
        border-radius: 25px;
        box-shadow: 0 6px 20px rgba(218, 165, 127, 0.2);
        font-family: 'Comfortaa', cursive;
        color: #8b6914;
        font-size: 14px;
        font-weight: 500;
        border: 2px solid #f2e8d5;
        z-index: 1000;
    }
    
    .music-emoji {
        display: inline-block;
        animation: musicBounce 2s infinite;
        margin-right: 8px;
    }
    
    @keyframes musicBounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-5px); }
        60% { transform: translateY(-3px); }
    }
    
    h1, h2, h3 {
        font-family: 'Comfortaa', cursive;
        color: #8b6914;
        font-weight: 500;
    }
    
    .css-1d391kg { display: none !important; }
    .css-1rs6os { display: none !important; }
    .css-17eq0hr { display: none !important; }
    .css-1y4p8pa { display: none !important; }
    .css-12oz5g7 { display: none !important; }
    .css-1dp5vir { display: none !important; }
    
    .main .block-container { 
        padding-top: 2rem !important; 
        padding-bottom: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    /* Custom input styling */
    .stTextInput > div > div > input {
        background: linear-gradient(145deg, #fefcf8, #fbf8f2) !important;
        border: 2px solid #e8d5b7 !important;
        border-radius: 20px !important;
        padding: 12px 20px !important;
        font-family: 'Comfortaa', cursive !important;
        color: #8b6914 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #d4af8c !important;
        box-shadow: 0 0 15px rgba(218, 165, 127, 0.3) !important;
    }
    
    .stTextArea > div > div > textarea {
        background: linear-gradient(145deg, #fefcf8, #fbf8f2) !important;
        border: 2px solid #e8d5b7 !important;
        border-radius: 20px !important;
        padding: 15px 20px !important;
        font-family: 'Comfortaa', cursive !important;
        color: #8b6914 !important;
        font-size: 16px !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #d4af8c !important;
        box-shadow: 0 0 15px rgba(218, 165, 127, 0.3) !important;
    }
    
    /* Pastel orange login button */
    .stButton > button {
        background: linear-gradient(45deg, #f5c99b, #f2b885) !important;
        color: #8b6914 !important;
        border: 2px solid #e8d5b7 !important;
        border-radius: 25px !important;
        padding: 12px 25px !important;
        font-family: 'Comfortaa', cursive !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 6px 20px rgba(218, 165, 127, 0.25) !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #f2b885, #efab6e) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(218, 165, 127, 0.4) !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(145deg, #faf7f2, #f7f3eb);
        border-radius: 20px;
        padding: 5px;
        border: 2px solid #e8d5b7;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #a67c52;
        border-radius: 15px;
        font-family: 'Comfortaa', cursive;
        font-weight: 500;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(145deg, #f5c99b, #f2b885);
        color: #8b6914;
        font-weight: 600;
    }
    
    /* Form styling */
    .stForm {
        background: linear-gradient(145deg, #fefcf8, #fbf8f2);
        border-radius: 25px;
        padding: 25px;
        border: 2px solid #e8d5b7;
        margin: 15px 0;
    }
    
    /* Music player container */
    .music-player {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(145deg, #fff8f0, #fef6ed);
        border-radius: 50px;
        padding: 10px 15px;
        border: 2px solid #e8d5b7;
        box-shadow: 0 8px 25px rgba(218, 165, 127, 0.2);
        z-index: 1000;
        font-size: 12px;
        color: #8b6914;
        font-family: 'Comfortaa', cursive;
    }
    
    .music-emoji {
        animation: musicBounce 2s infinite;
        display: inline-block;
        margin-right: 8px;
    }
    
    @keyframes musicBounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-5px); }
        60% { transform: translateY(-3px); }
    }
    </style>
    """, unsafe_allow_html=True)

def create_animated_login_page():
    """Create an animated login page with pastel falling leaves and background music."""
    animation_html = """
    <div style="width: 100%; height: 300px; position: relative; overflow: hidden; border-radius: 25px; background: linear-gradient(to bottom, #fefcf8, #f7f3eb); border: 2px solid #e8d5b7;">
        <canvas id="leavesCanvas" width="400" height="300" style="display: block; margin: 0 auto;"></canvas>
    </div>
    
    <!-- Background Music -->
    <audio id="bgMusic" autoplay loop volume="0.3">
        <source src="data:audio/mpeg;base64,/+MYxAAEaAIEeUAQAgBgNgP/////KQQ/////Lvrg+lcWYHgtjadzsbTq+yREu495tq9c6v/7zGMYxA..." type="audio/mpeg">
        <!-- Fallback: using a peaceful tone generator -->
    </audio>
    
    <script>
    // Create peaceful background music using Web Audio API
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    function createPeacefulTone() {
        const oscillator1 = audioContext.createOscillator();
        const oscillator2 = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator1.frequency.setValueAtTime(174.61, audioContext.currentTime); // F3
        oscillator2.frequency.setValueAtTime(220.00, audioContext.currentTime); // A3
        
        oscillator1.type = 'sine';
        oscillator2.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.05, audioContext.currentTime);
        
        oscillator1.connect(gainNode);
        oscillator2.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator1.start();
        oscillator2.start();
        
        // Fade in and out
        setTimeout(() => {
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 2);
        }, 3000);
        
        setTimeout(() => {
            oscillator1.stop();
            oscillator2.stop();
        }, 5000);
    }
    
    // Play music intermittently
    setInterval(() => {
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
        createPeacefulTone();
    }, 8000);
    
    // Initial music start (requires user interaction)
    document.addEventListener('click', () => {
        if (audioContext.state === 'suspended') {
            audioContext.resume().then(() => {
                createPeacefulTone();
            });
        }
    }, { once: true });
    
    const canvas = document.getElementById('leavesCanvas');
    const ctx = canvas.getContext('2d');
    
    // Pastel tree with soft colors
    function drawTree() {
        // Tree trunk - soft brown
        ctx.fillStyle = '#c4a484';
        ctx.fillRect(180, 180, 40, 120);
        
        // Tree crown - soft beige/cream
        ctx.fillStyle = '#e8d5b7';
        ctx.beginPath();
        ctx.arc(200, 150, 80, 0, Math.PI * 2);
        ctx.fill();
        
        // Add soft texture to the crown
        ctx.fillStyle = '#dac09a';
        ctx.beginPath();
        ctx.arc(180, 130, 25, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.beginPath();
        ctx.arc(220, 140, 30, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.beginPath();
        ctx.arc(200, 170, 20, 0, Math.PI * 2);
        ctx.fill();
        
        // Add small branches - very soft brown
        ctx.strokeStyle = '#b8a082';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(200, 180);
        ctx.lineTo(170, 160);
        ctx.moveTo(200, 180);
        ctx.lineTo(230, 160);
        ctx.moveTo(200, 190);
        ctx.lineTo(175, 175);
        ctx.moveTo(200, 190);
        ctx.lineTo(225, 175);
        ctx.stroke();
    }
    
    // Pastel leaf class with soft colors
    class PastelLeaf {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * -100;
            this.vx = (Math.random() - 0.5) * 1;
            this.vy = Math.random() * 1.5 + 0.5;
            this.rotation = Math.random() * Math.PI * 2;
            this.rotationSpeed = (Math.random() - 0.5) * 0.1;
            this.size = Math.random() * 6 + 3;
            this.color = ['#f5c99b', '#f2b885', '#efab6e', '#e8d5b7', '#dac09a'][Math.floor(Math.random() * 5)];
            this.windInfluence = Math.random() * 0.2 + 0.05;
        }
        
        update(mouseX, mouseY) {
            // Gentle wind effect from mouse
            const distanceToMouse = Math.sqrt((this.x - mouseX) ** 2 + (this.y - mouseY) ** 2);
            const maxDistance = 80;
            
            if (distanceToMouse < maxDistance) {
                const windStrength = (maxDistance - distanceToMouse) / maxDistance;
                this.vx += (mouseX - this.x) * 0.0005 * windStrength * this.windInfluence;
            }
            
            this.x += this.vx;
            this.y += this.vy;
            this.rotation += this.rotationSpeed;
            
            // Reset leaf if it goes off screen
            if (this.y > canvas.height + 10) {
                this.y = Math.random() * -100;
                this.x = Math.random() * canvas.width;
                this.vx = (Math.random() - 0.5) * 1;
            }
            
            // Keep leaves within horizontal bounds
            if (this.x < -10) this.x = canvas.width + 10;
            if (this.x > canvas.width + 10) this.x = -10;
        }
        
        draw() {
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.rotation);
            
            // Soft leaf shape
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.ellipse(0, 0, this.size, this.size * 0.6, 0, 0, Math.PI * 2);
            ctx.fill();
            
            // Very soft leaf stem
            ctx.strokeStyle = '#c4a484';
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.lineTo(0, this.size * 0.2);
            ctx.stroke();
            
            ctx.restore();
        }
    }
    
    // Create gentle pastel leaves
    const leaves = [];
    for (let i = 0; i < 12; i++) {
        leaves.push(new PastelLeaf());
    }
    
    let mouseX = canvas.width / 2;
    let mouseY = canvas.height / 2;
    
    // Mouse tracking
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mouseX = e.clientX - rect.left;
        mouseY = e.clientY - rect.top;
    });
    
    // Gentle animation loop
    function animate() {
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw soft sky gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, '#fefcf8');
        gradient.addColorStop(0.5, '#f7f3eb');
        gradient.addColorStop(1, '#f4efe4');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw pastel tree
        drawTree();
        
        // Update and draw leaves gently
        leaves.forEach(leaf => {
            leaf.update(mouseX, mouseY);
            leaf.draw();
        });
        
        requestAnimationFrame(animate);
    }
    
    animate();
    </script>
    """
    return animation_html

# ================================
# MAIN APPLICATION LOGIC
# ================================

def main():
    """Main application function."""
    # Initialize database
    init_database()
    
    # Apply custom styling
    apply_custom_css()
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    
    # Simple title
    st.title("🍂 Cozy Journal 🍂")
    
    # Simple check for user login
    if st.session_state.user is None:
        st.markdown("### Welcome to your Cozy Journal! ☕")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.success("Welcome back!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        
        with tab2:
            with st.form("signup"):
                new_username = st.text_input("New Username")
                new_password = st.text_input("New Password", type="password")
                if st.form_submit_button("Sign Up"):
                    if create_user(new_username, new_password):
                        st.success("Account created! Please login.")
                    else:
                        st.error("Username already exists")
    else:
        # Handle different pages
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'dashboard'
            
        # Hidden navigation buttons for JavaScript interaction
        with st.sidebar:
            st.markdown("### Navigation (Hidden)")
            if st.button("Dashboard", key="nav_dashboard"):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            if st.button("New Entry", key="nav_new_entry"):
                st.session_state.current_page = 'new_entry'
                st.rerun()
            if st.button("View Entries", key="nav_entries"):
                st.session_state.current_page = 'entries'
                st.rerun()
            if st.button("Rainfall Reverie", key="nav_rainfall"):
                st.session_state.current_page = 'rainfall'
                st.rerun()
            if st.button("Back to Dashboard", key="nav_back_dashboard"):
                st.session_state.current_page = 'dashboard'
                st.rerun()
                
        # Page routing
        if st.session_state.current_page == 'dashboard':
            show_journal_dashboard()
        elif st.session_state.current_page == 'new_entry':
            show_new_entry_form()
        elif st.session_state.current_page == 'entries':
            show_entries_list()
        elif st.session_state.current_page == 'rainfall':
            show_rainfall_reverie()
        else:
            show_journal_dashboard()

def show_login_page():
    """Display the login/signup page with animation and pastel styling."""
    st.markdown('<div class="subtitle">☕ Welcome to your cozy autumn journal 🍂</div>', unsafe_allow_html=True)
    
    # Show animated tree with gentle falling leaves
    components.html(create_animated_login_page(), height=320)
    
    # Add music player indicator
    st.markdown("""
    <div class="music-player">
        <span class="music-emoji">🎵</span>Lo-fi vibes playing...
    </div>
    """, unsafe_allow_html=True)
    
    # Registration section
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown("### 🌰 New to our cozy community? 🌰")
    
    # Instructions for new users
    st.markdown("### 🌰 Join our cozy community! �")
    st.markdown("Use the **Sign Up** tab above to create your account! 🌱")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">☕ Welcome to your cozy autumn journal 🍂</div>', unsafe_allow_html=True)
    
    # Show animated tree with gentle falling leaves
    components.html(create_animated_login_page(), height=320)
    
    # Add music player indicator
    st.markdown("""
    <div class="music-player">
        <span class="music-emoji">🎵</span>Lo-fi vibes playing...
    </div>
    """, unsafe_allow_html=True)
    
    # Login form with pastel styling
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["☕ Login", "🌰 Sign Up"])
    
    with tab1:
        st.markdown("### 🍁 Welcome back, dear friend! 🍁")
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username", placeholder="👤 Enter your username", key="login_username", label_visibility="hidden")
            password = st.text_input("Password", placeholder="🔑 Enter your password", type="password", key="login_password", label_visibility="hidden")
            
            # Pastel orange login button with coffee emoji
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                login_btn = st.form_submit_button("☕ Enter Your Cozy Journal 🍂")
            
            if login_btn and username and password:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.user = user
                    st.success("Welcome back! �✨")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Hmm, that doesn't seem right... 🤔 Try again!")
    
    with tab2:
        st.markdown("### 🌰 Join our cozy reading nook! 🌰")
        with st.form("signup_form", clear_on_submit=True):
            new_username = st.text_input("Username", placeholder="👤 Choose a cozy username", key="signup_username", label_visibility="hidden")
            new_password = st.text_input("Password", placeholder="🔑 Create a secure password", type="password", key="signup_password", label_visibility="hidden")
            confirm_password = st.text_input("Confirm Password", placeholder="🔑 Confirm your password", type="password", key="confirm_password", label_visibility="hidden")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                signup_btn = st.form_submit_button("🌱 Create Your Journal ☕")
            
            if signup_btn and new_username and new_password:
                if new_password != confirm_password:
                    st.error("Oops! Passwords don't match 🤭")
                elif len(new_password) < 4:
                    st.error("Password needs to be longer, sweetie! 🔐✨")
                elif create_user(new_username, new_password):
                    st.success("Welcome to the family! Please login 🎊☕")
                    st.balloons()
                else:
                    st.error("That username is taken, hun! �")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Cute instructions with fall emojis
    st.markdown("""
    <div class="entry-card">
    <h4>🍂 How to use your Cozy Journal 🍂</h4>
    <div style="text-align: left; padding: 10px;">
    ☕ <strong>Create account or login</strong> to start your journaling journey<br><br>
    🍁 <strong>Write entries</strong> with beautiful titles and heartfelt content<br><br>
    🔍 <strong>Search memories</strong> through your personal collection<br><br>
    ✏️ <strong>Edit & organize</strong> your thoughts anytime you want<br><br>
    💾 <strong>Export everything</strong> as a cozy JSON backup<br><br>
    🌰 <strong>Enjoy the peaceful vibes</strong> with soft music & falling leaves
    </div>
    </div>
    """, unsafe_allow_html=True)

def show_journal_dashboard():
    """Display the main journal dashboard with pixel art wooden desk."""
    # Hide default streamlit elements for full screen experience
    st.markdown("""
    <style>
    .main > div {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Full screen pixel art desk background
    desk_html = f"""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -1;
        background: linear-gradient(45deg, #8B4513 0%, #A0522D 25%, #CD853F 50%, #DEB887 75%, #F5DEB3 100%);
        background-image: 
            repeating-linear-gradient(90deg, rgba(139, 69, 19, 0.1) 0px, transparent 2px, transparent 8px, rgba(139, 69, 19, 0.1) 10px),
            repeating-linear-gradient(0deg, rgba(160, 82, 45, 0.1) 0px, transparent 2px, transparent 8px, rgba(160, 82, 45, 0.1) 10px);
        background-size: 20px 20px;
    "></div>
    
    <!-- Welcome header with logout -->
    <div style="position: absolute; top: 20px; right: 30px; z-index: 1000;">
        <div style="background: rgba(255, 248, 240, 0.95); padding: 10px 20px; border-radius: 20px; border: 2px solid #D2B48C; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <span style="color: #8B4513; font-family: 'Comfortaa', cursive; font-size: 16px; font-weight: 600;">
                🌰 Welcome, {st.session_state.user['username']}! ☕
            </span>
        </div>
    </div>
    
    <!-- Music player indicator -->
    <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
        <div style="background: rgba(255, 248, 240, 0.95); padding: 8px 15px; border-radius: 25px; border: 2px solid #D2B48C; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <span style="color: #8B4513; font-family: 'Comfortaa', cursive; font-size: 12px;">
                <span style="animation: musicBounce 2s infinite;">🎵</span> Cozy vibes...
            </span>
        </div>
    </div>
    
    <!-- Main desk surface with book menu -->
    <div style="
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 20px;
        position: relative;
    ">
        <div style="
            position: relative;
            width: 800px;
            height: 600px;
            background: rgba(160, 82, 45, 0.3);
            border-radius: 15px;
            border: 3px solid #8B4513;
            box-shadow: inset 0 0 50px rgba(139, 69, 19, 0.3), 0 10px 30px rgba(0,0,0,0.3);
        ">
            
            <!-- Decorative desk items -->
            <!-- Coffee cup (top left) -->
            <div style="position: absolute; top: 50px; left: 80px; font-size: 48px; filter: drop-shadow(3px 3px 6px rgba(0,0,0,0.3));">
                ☕
            </div>
            
            <!-- Plant (top right) -->
            <div style="position: absolute; top: 60px; right: 100px; font-size: 40px; filter: drop-shadow(3px 3px 6px rgba(0,0,0,0.3));">
                🌱
            </div>
            
            <!-- Lamp (bottom left) -->
            <div style="position: absolute; bottom: 80px; left: 60px; font-size: 44px; filter: drop-shadow(3px 3px 6px rgba(0,0,0,0.3));">
                🕯️
            </div>
            
            <!-- Acorns decoration (bottom right) -->
            <div style="position: absolute; bottom: 70px; right: 80px; font-size: 32px; filter: drop-shadow(3px 3px 6px rgba(0,0,0,0.3));">
                🌰🌰
            </div>
            
            <!-- Fall leaves scattered -->
            <div style="position: absolute; top: 120px; left: 200px; font-size: 28px; opacity: 0.8; transform: rotate(-15deg);">🍁</div>
            <div style="position: absolute; top: 180px; right: 250px; font-size: 24px; opacity: 0.7; transform: rotate(25deg);">🍂</div>
            <div style="position: absolute; bottom: 150px; left: 180px; font-size: 26px; opacity: 0.8; transform: rotate(-30deg);">🍁</div>
            <div style="position: absolute; bottom: 200px; right: 200px; font-size: 22px; opacity: 0.7; transform: rotate(45deg);">🍂</div>
            
            <!-- Central book menu -->
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 280px;
                height: 200px;
                background: linear-gradient(145deg, #D2691E, #CD853F, #DEB887);
                border-radius: 15px;
                border: 4px solid #8B4513;
                box-shadow: 
                    0 8px 25px rgba(0,0,0,0.4),
                    inset 0 2px 0 rgba(255,255,255,0.3),
                    inset 0 -2px 0 rgba(139,69,19,0.3);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                cursor: pointer;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            " onmouseover="this.style.transform='translate(-50%, -50%) scale(1.05)'; this.style.boxShadow='0 12px 35px rgba(0,0,0,0.5)'" 
               onmouseout="this.style.transform='translate(-50%, -50%) scale(1)'; this.style.boxShadow='0 8px 25px rgba(0,0,0,0.4)'">
                
                <!-- Book spine detail -->
                <div style="
                    position: absolute;
                    left: -8px;
                    top: 10px;
                    bottom: 10px;
                    width: 8px;
                    background: linear-gradient(180deg, #8B4513, #A0522D);
                    border-radius: 4px 0 0 4px;
                "></div>
                
                <!-- Book title -->
                <div style="
                    color: #4A2C2A;
                    font-family: 'Caveat', cursive;
                    font-size: 28px;
                    font-weight: 700;
                    text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
                    margin-bottom: 20px;
                ">
                    � My Cozy Journal
                </div>
                
                <!-- Menu options as book pages -->
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div id="newEntryBtn" style="
                        background: rgba(255, 248, 240, 0.9);
                        color: #8B4513;
                        padding: 6px 14px;
                        border-radius: 12px;
                        border: 2px solid #D2B48C;
                        font-family: 'Comfortaa', cursive;
                        font-size: 15px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        text-align: center;
                        min-width: 180px;
                    " onmouseover="this.style.background='rgba(242, 184, 133, 0.9)'; this.style.transform='translateY(-2px)'"
                       onmouseout="this.style.background='rgba(255, 248, 240, 0.9)'; this.style.transform='translateY(0)'">
                        ✍️ Write New Memory
                    </div>
                    
                    <div id="viewEntriesBtn" style="
                        background: rgba(255, 248, 240, 0.9);
                        color: #8B4513;
                        padding: 6px 14px;
                        border-radius: 12px;
                        border: 2px solid #D2B48C;
                        font-family: 'Comfortaa', cursive;
                        font-size: 15px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        text-align: center;
                        min-width: 180px;
                    " onmouseover="this.style.background='rgba(242, 184, 133, 0.9)'; this.style.transform='translateY(-2px)'"
                       onmouseout="this.style.background='rgba(255, 248, 240, 0.9)'; this.style.transform='translateY(0)'">
                        📚 View Saved Entries
                    </div>
                    
                    <div id="rainfallBtn" style="
                        background: rgba(230, 240, 255, 0.9);
                        color: #2C5F7A;
                        padding: 6px 14px;
                        border-radius: 12px;
                        border: 2px solid #87CEEB;
                        font-family: 'Comfortaa', cursive;
                        font-size: 15px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        text-align: center;
                        min-width: 180px;
                    " onmouseover="this.style.background='rgba(176, 196, 222, 0.9)'; this.style.transform='translateY(-2px)'"
                       onmouseout="this.style.background='rgba(230, 240, 255, 0.9)'; this.style.transform='translateY(0)'">
                        🌧️ Rainfall Reverie
                    </div>
                </div>
            </div>
            
            <!-- Settings icon (top center) -->
            <div style="position: absolute; top: 30px; left: 50%; transform: translateX(-50%); font-size: 32px; cursor: pointer; filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3));">
                ⚙️
            </div>
            
            <!-- To-do list icon (middle left) -->
            <div style="position: absolute; top: 50%; left: 30px; transform: translateY(-50%); font-size: 36px; cursor: pointer; filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3));">
                📝
            </div>
            
            <!-- Search/export icon (middle right) -->
            <div style="position: absolute; top: 50%; right: 30px; transform: translateY(-50%); font-size: 36px; cursor: pointer; filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3));">
                🔍
            </div>
        </div>
    </div>
    
    <script>
    // Handle menu clicks
    document.getElementById('newEntryBtn').addEventListener('click', function() {{
        // Trigger the hidden navigation button
        const navBtn = window.parent.document.querySelector('[data-testid="stSidebar"] button[data-baseweb="button"]:nth-of-type(2)');
        if (navBtn) navBtn.click();
    }});
    
    document.getElementById('viewEntriesBtn').addEventListener('click', function() {{
        // Trigger the hidden navigation button
        const navBtn = window.parent.document.querySelector('[data-testid="stSidebar"] button[data-baseweb="button"]:nth-of-type(3)');
        if (navBtn) navBtn.click();
    }});
    
    document.getElementById('rainfallBtn').addEventListener('click', function() {{
        // Trigger the hidden navigation button
        const navBtn = window.parent.document.querySelector('[data-testid="stSidebar"] button[data-baseweb="button"]:nth-of-type(4)');
        if (navBtn) navBtn.click();
    }});
    </script>
    """
    
    # Display the desk
    components.html(desk_html, height=700)
    
    # Navigation logic with invisible buttons
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    
    with col2:
        if st.button("✍️ Write New Entry", key="desk_new_entry"):
            st.session_state.current_page = 'new_entry'
            st.rerun()
    
    with col3:
        if st.button("📚 View Entries", key="desk_view_entries"):
            st.session_state.current_page = 'view_entries'
            st.rerun()
    
    with col4:
        if st.button("🔍 Search & Export", key="desk_search"):
            st.session_state.current_page = 'search_export'
            st.rerun()
            
    with col5:
        if st.button("🚪 Logout", key="desk_logout"):
            st.session_state.user = None
            st.session_state.current_page = 'login'
            st.rerun()
    
    # Handle page navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'desk'
    
    if st.session_state.current_page == 'new_entry':
        st.markdown("---")
        show_new_entry_form()
        if st.button("🏠 Back to Desk"):
            st.session_state.current_page = 'desk'
            st.rerun()
            
    elif st.session_state.current_page == 'view_entries':
        st.markdown("---")
        show_entries_list()
        if st.button("🏠 Back to Desk"):
            st.session_state.current_page = 'desk'
            st.rerun()
            
    elif st.session_state.current_page == 'search_export':
        st.markdown("---")
        show_search_and_export()
        if st.button("🏠 Back to Desk"):
            st.session_state.current_page = 'desk'
            st.rerun()

def show_entries_list():
    """Display list of user's journal entries with cozy styling."""
    # Back button
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("🏠 Back to Menu"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    entries = get_user_entries(st.session_state.user['id'])
    
    st.markdown("""
    <div style="background: rgba(255, 248, 240, 0.95); padding: 30px; border-radius: 20px; border: 3px solid #D2B48C; margin: 20px 0;">
    <h3 style="color: #8B4513; font-family: 'Caveat', cursive; text-align: center; font-size: 2.5em; margin-bottom: 25px;">
    📚 Your Saved Memories 📚
    </h3>
    </div>
    """, unsafe_allow_html=True)
    
    if not entries:
        st.markdown("""
        <div style="background: rgba(255, 248, 240, 0.9); padding: 25px; border-radius: 15px; border: 2px solid #D2B48C; text-align: center; margin: 20px 0;">
        <h4 style="color: #8B4513; font-family: 'Comfortaa', cursive;">📔 No memories yet!</h4>
        <p style="color: #A0522D; font-family: 'Comfortaa', cursive;">Start writing your first journal entry to capture this moment! ✨</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0;">
    <span style="color: #8B4513; font-family: 'Comfortaa', cursive; font-size: 18px; font-weight: 600;">
    You have {len(entries)} precious memories �
    </span>
    </div>
    """, unsafe_allow_html=True)
    
    for entry in entries:
        with st.container():
            st.markdown(f"""
            <div style="background: rgba(255, 248, 240, 0.9); padding: 20px; border-radius: 15px; border: 2px solid #D2B48C; margin: 15px 0; box-shadow: 0 4px 15px rgba(139, 69, 19, 0.1);">
            <h4 style="color: #8B4513; font-family: 'Caveat', cursive; font-size: 1.8em; margin-bottom: 10px;">📝 {entry['title']}</h4>
            <small style="color: #A0522D; font-family: 'Comfortaa', cursive;">
            Created: {entry['created_at'][:16]} | Updated: {entry['updated_at'][:16]}
            </small>
            </div>
            """, unsafe_allow_html=True)
            
            # Show content preview with cozy styling
            preview = entry['content'][:200] + "..." if len(entry['content']) > 200 else entry['content']
            st.markdown(f"""
            <div style="background: rgba(250, 245, 235, 0.8); padding: 15px; border-radius: 10px; border-left: 4px solid #D2B48C; margin: 10px 0; font-family: 'Comfortaa', cursive; color: #654321;">
            {preview}
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 4])
            
            with col1:
                if st.button(f"✏️ Edit", key=f"edit_{entry['id']}"):
                    st.session_state.editing_entry = entry
            
            with col2:
                if st.button(f"🗑️ Delete", key=f"delete_{entry['id']}"):
                    if delete_journal_entry(entry['id']):
                        st.success("Memory deleted! 🗑️")
                        st.rerun()
                    else:
                        st.error("Failed to delete memory 😞")
            
            # Edit form if this entry is being edited
            if 'editing_entry' in st.session_state and st.session_state.editing_entry['id'] == entry['id']:
                st.markdown("""
                <div style="background: rgba(245, 235, 220, 0.95); padding: 20px; border-radius: 15px; border: 2px solid #CD853F; margin: 15px 0;">
                <h4 style="color: #8B4513; font-family: 'Caveat', cursive; text-align: center; font-size: 1.5em;">✏️ Edit Your Memory</h4>
                </div>
                """, unsafe_allow_html=True)
                
                with st.form(f"edit_form_{entry['id']}"):
                    new_title = st.text_input("Title", value=entry['title'], label_visibility="hidden")
                    new_content = st.text_area("Content", value=entry['content'], height=200, label_visibility="hidden")
                    
                    # Ensure values are strings
                    safe_title = new_title if new_title is not None else ""
                    safe_content = new_content if new_content is not None else ""
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Save Changes", use_container_width=True):
                            if update_journal_entry(entry['id'], safe_title, safe_content):
                                st.success("Memory updated! ✨")
                                del st.session_state.editing_entry
                                st.rerun()
                            else:
                                st.error("Failed to update memory 😞")
                    
                    with col_cancel:
                        if st.form_submit_button("❌ Cancel", use_container_width=True):
                            del st.session_state.editing_entry
                            st.rerun()
            
            st.markdown("---")

def show_rainfall_reverie():
    """Display the peaceful rainfall scene with reading atmosphere."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@300;400;500;600;700&family=Caveat:wght@400;500;600;700&display=swap');
    
    @keyframes rainDrop {
        0% { transform: translateY(-100px); opacity: 0.8; }
        100% { transform: translateY(100vh); opacity: 0; }
    }
    
    @keyframes leafFloat {
        0% { transform: translateY(-20px) translateX(0px) rotate(0deg); opacity: 0.8; }
        50% { transform: translateY(50px) translateX(10px) rotate(180deg); opacity: 0.6; }
        100% { transform: translateY(120px) translateX(-5px) rotate(360deg); opacity: 0; }
    }
    
    @keyframes steamRise {
        0% { transform: translateY(0px) scale(1); opacity: 0.6; }
        100% { transform: translateY(-30px) scale(1.3); opacity: 0; }
    }
    
    .rain-drop {
        position: absolute;
        background: linear-gradient(to bottom, rgba(173, 216, 230, 0.6), rgba(135, 206, 235, 0.4));
        width: 2px;
        height: 15px;
        border-radius: 50%;
        animation: rainDrop linear infinite;
    }
    
    .leaf-drift {
        position: absolute;
        font-size: 16px;
        animation: leafFloat 4s ease-in-out infinite;
        pointer-events: none;
    }
    
    .coffee-steam {
        position: absolute;
        color: rgba(255, 255, 255, 0.6);
        font-size: 14px;
        animation: steamRise 3s ease-out infinite;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main rainfall scene
    scene_html = f"""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -2;
        background: linear-gradient(to bottom, #4A5D6B 0%, #6B7B8C 50%, #8B9DAF 100%);
        overflow: hidden;
    ">
        <!-- Room interior with window -->
        <div style="
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 40%;
            background: linear-gradient(to bottom, #3E2723 0%, #5D4037 50%, #8D6E63 100%);
            border-top: 4px solid #2E1A0A;
        ">
            <!-- Window frame -->
            <div style="
                position: absolute;
                top: -60%;
                left: 20%;
                width: 60%;
                height: 80%;
                background: rgba(240, 248, 255, 0.1);
                border: 8px solid #4A2C2A;
                border-radius: 12px;
                box-shadow: inset 0 0 50px rgba(0,0,0,0.3);
            ">
                <!-- Window cross frame -->
                <div style="
                    position: absolute;
                    top: 48%;
                    left: 0;
                    right: 0;
                    height: 4%;
                    background: #4A2C2A;
                "></div>
                <div style="
                    position: absolute;
                    top: 0;
                    bottom: 0;
                    left: 48%;
                    width: 4%;
                    background: #4A2C2A;
                "></div>
            </div>
            
            <!-- Outdoor scene through window -->
            <div style="
                position: absolute;
                top: -60%;
                left: 20%;
                width: 60%;
                height: 80%;
                background: linear-gradient(to bottom, #4A5D6B 0%, #5A6B7A 100%);
                border-radius: 4px;
                overflow: hidden;
            ">
                <!-- Trees outside -->
                <div style="position: absolute; bottom: 20%; left: 10%; font-size: 60px; opacity: 0.7;">🌲</div>
                <div style="position: absolute; bottom: 25%; left: 25%; font-size: 45px; opacity: 0.6;">🌳</div>
                <div style="position: absolute; bottom: 30%; right: 15%; font-size: 55px; opacity: 0.7;">🌲</div>
                <div style="position: absolute; bottom: 20%; right: 30%; font-size: 40px; opacity: 0.6;">🌳</div>
                
                <!-- Rain animation -->
                <div class="rain-drop" style="left: 10%; animation-delay: 0s; animation-duration: 1s;"></div>
                <div class="rain-drop" style="left: 20%; animation-delay: 0.2s; animation-duration: 1.2s;"></div>
                <div class="rain-drop" style="left: 30%; animation-delay: 0.4s; animation-duration: 0.8s;"></div>
                <div class="rain-drop" style="left: 40%; animation-delay: 0.1s; animation-duration: 1.1s;"></div>
                <div class="rain-drop" style="left: 50%; animation-delay: 0.3s; animation-duration: 0.9s;"></div>
                <div class="rain-drop" style="left: 60%; animation-delay: 0.5s; animation-duration: 1.3s;"></div>
                <div class="rain-drop" style="left: 70%; animation-delay: 0.2s; animation-duration: 1s;"></div>
                <div class="rain-drop" style="left: 80%; animation-delay: 0.4s; animation-duration: 1.1s;"></div>
                <div class="rain-drop" style="left: 90%; animation-delay: 0.1s; animation-duration: 0.9s;"></div>
            </div>
            
            <!-- Indoor desk surface -->
            <div style="
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                height: 50%;
                background: linear-gradient(145deg, #8B4513, #A0522D, #CD853F);
                background-image: 
                    repeating-linear-gradient(90deg, rgba(139, 69, 19, 0.2) 0px, transparent 2px, transparent 10px, rgba(139, 69, 19, 0.2) 12px),
                    repeating-linear-gradient(0deg, rgba(160, 82, 45, 0.2) 0px, transparent 2px, transparent 10px, rgba(160, 82, 45, 0.2) 12px);
                border-radius: 15px 15px 0 0;
                border: 3px solid #654321;
            ">
                <!-- Journal book on desk -->
                <div style="
                    position: absolute;
                    top: 30%;
                    left: 35%;
                    transform: translateX(-50%);
                    width: 200px;
                    height: 140px;
                    background: linear-gradient(145deg, #D2691E, #CD853F, #DEB887);
                    border-radius: 8px;
                    border: 3px solid #8B4513;
                    box-shadow: 0 8px 25px rgba(0,0,0,0.4);
                    cursor: pointer;
                    transition: transform 0.3s ease;
                " onmouseover="this.style.transform='translateX(-50%) scale(1.05)'"
                   onmouseout="this.style.transform='translateX(-50%) scale(1)'"
                   id="journalBook">
                    <!-- Book spine -->
                    <div style="
                        position: absolute;
                        left: -6px;
                        top: 6px;
                        bottom: 6px;
                        width: 6px;
                        background: linear-gradient(180deg, #8B4513, #A0522D);
                        border-radius: 3px 0 0 3px;
                    "></div>
                    
                    <!-- Book title -->
                    <div style="
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        color: #4A2C2A;
                        font-family: 'Caveat', cursive;
                        font-size: 20px;
                        font-weight: 700;
                        text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
                        text-align: center;
                    ">
                        📖<br>My Cozy<br>Journal
                    </div>
                </div>
                
                <!-- Coffee cup with steam -->
                <div style="
                    position: absolute;
                    top: 25%;
                    right: 25%;
                    font-size: 48px;
                    filter: drop-shadow(3px 3px 6px rgba(0,0,0,0.4));
                ">
                    ☕
                    <!-- Steam animation -->
                    <div class="coffee-steam" style="top: -10px; left: 20px; animation-delay: 0s;">~</div>
                    <div class="coffee-steam" style="top: -15px; left: 25px; animation-delay: 1s;">~</div>
                    <div class="coffee-steam" style="top: -20px; left: 18px; animation-delay: 2s;">~</div>
                </div>
                
                <!-- Warm lamp -->
                <div style="
                    position: absolute;
                    top: 20%;
                    left: 15%;
                    font-size: 40px;
                    filter: drop-shadow(3px 3px 6px rgba(0,0,0,0.4));
                ">
                    🕯️
                </div>
                
                <!-- Cozy book stack -->
                <div style="
                    position: absolute;
                    bottom: 25%;
                    right: 15%;
                    font-size: 32px;
                    filter: drop-shadow(3px 3px 6px rgba(0,0,0,0.4));
                ">
                    📚
                </div>
            </div>
        </div>
        
        <!-- Falling leaves inside -->
        <div class="leaf-drift" style="top: 10%; left: 15%; animation-delay: 0s;">🍁</div>
        <div class="leaf-drift" style="top: 5%; left: 60%; animation-delay: 2s;">🍂</div>
        <div class="leaf-drift" style="top: 8%; left: 80%; animation-delay: 4s;">🍁</div>
        <div class="leaf-drift" style="top: 12%; right: 20%; animation-delay: 1s;">🍂</div>
        <div class="leaf-drift" style="top: 15%; right: 70%; animation-delay: 3s;">🍁</div>
    </div>
    
    <!-- Navigation buttons -->
    <div style="
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        gap: 20px;
        z-index: 1000;
    ">
        <button id="backToMenuBtn" style="
            background: linear-gradient(145deg, #8B4513, #A0522D);
            color: #FFF8DC;
            border: none;
            padding: 12px 24px;
            border-radius: 12px;
            font-family: 'Comfortaa', cursive;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            border: 2px solid #D2B48C;
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(0,0,0,0.4)'"
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(0,0,0,0.3)'">
            🏠 Back to Main Menu
        </button>
        
        <button id="readJournalBtn" style="
            background: linear-gradient(145deg, #4682B4, #5F9EA0);
            color: #FFF8DC;
            border: none;
            padding: 12px 24px;
            border-radius: 12px;
            font-family: 'Comfortaa', cursive;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            border: 2px solid #B0C4DE;
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(0,0,0,0.4)'"
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(0,0,0,0.3)'">
            📚 Read Journal
        </button>
    </div>
    
    <!-- Welcome message -->
    <div style="
        position: fixed;
        top: 30px;
        left: 50%;
        transform: translateX(-50%);
        text-align: center;
        z-index: 1000;
    ">
        <div style="
            background: rgba(255, 248, 240, 0.95);
            padding: 15px 25px;
            border-radius: 20px;
            border: 2px solid #D2B48C;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        ">
            <h2 style="
                color: #2C5F7A;
                font-family: 'Caveat', cursive;
                font-size: 2.2em;
                margin: 0;
                text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
            ">🌧️ Rainfall Reverie 🌧️</h2>
            <p style="
                color: #4A5D6B;
                font-family: 'Comfortaa', cursive;
                margin: 5px 0 0 0;
                font-size: 14px;
                font-style: italic;
            ">A peaceful place to reflect and read...</p>
        </div>
    </div>
    
    <script>
    // Rain sound generation
    let audioContext;
    let rainGainNode;
    let isRainPlaying = false;
    
    function initRainAudio() {{
        if (!audioContext) {{
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            rainGainNode = audioContext.createGain();
            rainGainNode.connect(audioContext.destination);
            rainGainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        }}
    }}
    
    function createRainSound() {{
        if (!audioContext) return;
        
        // Generate white noise for rain
        const bufferSize = audioContext.sampleRate * 2;
        const noiseBuffer = audioContext.createBuffer(1, bufferSize, audioContext.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        
        for (let i = 0; i < bufferSize; i++) {{
            output[i] = Math.random() * 2 - 1;
        }}
        
        const whiteNoise = audioContext.createBufferSource();
        whiteNoise.buffer = noiseBuffer;
        whiteNoise.loop = true;
        
        // Filter for rain-like sound
        const bandpass = audioContext.createBiquadFilter();
        bandpass.type = 'bandpass';
        bandpass.frequency.setValueAtTime(1000, audioContext.currentTime);
        bandpass.Q.setValueAtTime(0.5, audioContext.currentTime);
        
        const lowpass = audioContext.createBiquadFilter();
        lowpass.type = 'lowpass';
        lowpass.frequency.setValueAtTime(3000, audioContext.currentTime);
        
        whiteNoise.connect(bandpass);
        bandpass.connect(lowpass);
        lowpass.connect(rainGainNode);
        
        whiteNoise.start();
        
        return whiteNoise;
    }}
    
    function startRain() {{
        if (isRainPlaying) return;
        
        initRainAudio();
        if (audioContext.state === 'suspended') {{
            audioContext.resume().then(() => {{
                createRainSound();
                isRainPlaying = true;
            }});
        }} else {{
            createRainSound();
            isRainPlaying = true;
        }}
    }}
    
    // Start rain sound on any user interaction
    document.addEventListener('click', startRain, {{ once: true }});
    document.addEventListener('keydown', startRain, {{ once: true }});
    
    // Navigation handlers
    document.getElementById('backToMenuBtn').addEventListener('click', function() {{
        // Trigger back to dashboard
        const navBtn = window.parent.document.querySelector('[data-testid="stSidebar"] button[data-baseweb="button"]:nth-of-type(5)');
        if (navBtn) navBtn.click();
    }});
    
    document.getElementById('readJournalBtn').addEventListener('click', function() {{
        // Trigger view entries
        const navBtn = window.parent.document.querySelector('[data-testid="stSidebar"] button[data-baseweb="button"]:nth-of-type(3)');
        if (navBtn) navBtn.click();
    }});
    
    document.getElementById('journalBook').addEventListener('click', function() {{
        // Trigger view entries when clicking the book
        const navBtn = window.parent.document.querySelector('[data-testid="stSidebar"] button[data-baseweb="button"]:nth-of-type(3)');
        if (navBtn) navBtn.click();
    }});
    </script>
    """
    
    components.html(scene_html, height=800)

def show_new_entry_form():
    """Display form to create a new journal entry with cozy styling."""
    # Back button
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("🏠 Back to Menu"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    st.markdown("""
    <div style="background: rgba(255, 248, 240, 0.95); padding: 30px; border-radius: 20px; border: 3px solid #D2B48C; margin: 20px 0;">
    <h3 style="color: #8B4513; font-family: 'Caveat', cursive; text-align: center; font-size: 2.5em; margin-bottom: 25px;">
    ✍️ Write a New Memory ✍️
    </h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("new_entry_form", clear_on_submit=True):
        title = st.text_input(
            "Entry Title", 
            placeholder="📝 What's on your mind today?",
            label_visibility="hidden"
        )
        content = st.text_area(
            "Your thoughts", 
            placeholder="📖 Write your journal entry here. Share your thoughts, experiences, or anything you'd like to remember!\n\nTake your time... let your thoughts flow like autumn leaves in the wind... 🍂",
            height=300,
            label_visibility="hidden"
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submitted = st.form_submit_button("🌟 Save Memory", use_container_width=True)
        
        if submitted and title and content:
            if create_journal_entry(st.session_state.user['id'], title, content):
                st.success("Memory saved! ✨")
                st.balloons()
            else:
                st.error("Failed to save memory 😞")
        elif submitted:
            st.error("Please fill in both title and content! 📝")

def show_search_and_export():
    """Display search functionality and export option."""
    st.markdown("### 🔍 Search & Export")
    
    # Search section
    search_term = st.text_input("🔍 Search your entries", placeholder="Search by title or content...")
    
    if search_term:
        entries = get_user_entries(st.session_state.user['id'], search_term)
        st.markdown(f"Found {len(entries)} entries matching '{search_term}'")
        
        for entry in entries:
            st.markdown(f"""
            <div class="entry-card">
            <h5>📝 {entry['title']}</h5>
            <small>{entry['created_at'][:16]}</small>
            <p>{entry['content'][:150]}{'...' if len(entry['content']) > 150 else ''}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Export section
    st.markdown("### 💾 Export Your Entries")
    st.write("Download all your journal entries as a JSON file for backup or migration.")
    
    if st.button("📦 Export All Entries"):
        entries = get_user_entries(st.session_state.user['id'])
        if entries:
            export_data = {
                'user': st.session_state.user['username'],
                'exported_at': datetime.now().isoformat(),
                'total_entries': len(entries),
                'entries': entries
            }
            
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="💾 Download Journal.json",
                data=json_str,
                file_name=f"{st.session_state.user['username']}_journal_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
            
            st.success("Export ready! Click the download button above 📥")
        else:
            st.info("No entries to export yet! Start writing some entries first 📝")

if __name__ == "__main__":
    main()
