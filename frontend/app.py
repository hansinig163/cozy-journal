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
    """Apply custom CSS styling to the app."""
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
    
    /* Pastel falling leaves background animation */
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
    
    .journal-card {
        background: linear-gradient(145deg, #fff8f0, #fef6ed);
        padding: 25px;
        border-radius: 25px;
        margin: 15px 0;
        box-shadow: 0 8px 25px rgba(218, 165, 127, 0.15);
        border: 2px solid #f2e8d5;
        position: relative;
        z-index: 1;
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
    }
    
    h1, h2, h3 {
        font-family: 'Comfortaa', cursive;
        color: #8b6914;
        font-weight: 500;
    }
    
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
    
    # Background music that continues throughout the app
    st.markdown("""
    <audio id="appMusic" autoplay loop style="display: none;">
        <!-- Peaceful background tone continues -->
    </audio>
    <script>
    // Continue peaceful background music throughout app
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    function createContinuousTone() {
        const oscillator1 = audioContext.createOscillator();
        const oscillator2 = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator1.frequency.setValueAtTime(220.00, audioContext.currentTime); // A3
        oscillator2.frequency.setValueAtTime(261.63, audioContext.currentTime); // C4
        
        oscillator1.type = 'sine';
        oscillator2.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.03, audioContext.currentTime);
        
        oscillator1.connect(gainNode);
        oscillator2.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator1.start();
        oscillator2.start();
        
        setTimeout(() => {
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 3);
        }, 4000);
        
        setTimeout(() => {
            oscillator1.stop();
            oscillator2.stop();
        }, 7000);
    }
    
    // Play gentle music periodically throughout the app
    if (!window.musicStarted) {
        window.musicStarted = true;
        setInterval(() => {
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
            createContinuousTone();
        }, 12000);
    }
    
    // Start music on any user interaction
    document.addEventListener('click', () => {
        if (audioContext.state === 'suspended') {
            audioContext.resume().then(() => {
                createContinuousTone();
            });
        }
    }, { once: false });
    </script>
    """, unsafe_allow_html=True)
    
    # Main title with fall emojis
    st.markdown('<div class="title">🍂 ☕ Cozy Journal ☕ 🍂</div>', unsafe_allow_html=True)
    
    if st.session_state.user is None:
        show_login_page()
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
    
    # Login form with pastel styling
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["☕ Login", "🌰 Sign Up"])
    
    with tab1:
        st.markdown("### 🍁 Welcome back, dear friend! 🍁")
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("", placeholder="👤 Enter your username", key="login_username")
            password = st.text_input("", placeholder="🔑 Enter your password", type="password", key="login_password")
            
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
            new_username = st.text_input("", placeholder="👤 Choose a cozy username", key="signup_username")
            new_password = st.text_input("", placeholder="🔑 Create a secure password", type="password", key="signup_password")
            confirm_password = st.text_input("", placeholder="🔑 Confirm your password", type="password", key="confirm_password")
            
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
    """Display the main journal dashboard for logged-in users."""
    # Music player indicator for dashboard
    st.markdown("""
    <div class="music-player">
        <span class="music-emoji">🎵</span>Cozy vibes...
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### 🌰 Welcome back, {st.session_state.user['username']}! ☕")
    
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.session_state.page = 'login'
            st.rerun()
    
    # Navigation tabs with fall emojis
    tab1, tab2, tab3 = st.tabs(["📖 My Cozy Entries", "✍️ Write New Memory", "🔍 Search & Export 🌰"])
    
    with tab1:
        show_entries_list()
    
    with tab2:
        show_new_entry_form()
    
    with tab3:
        show_search_and_export()

def show_entries_list():
    """Display list of user's journal entries."""
    entries = get_user_entries(st.session_state.user['id'])
    
    if not entries:
        st.markdown("""
        <div class="entry-card">
        <h4>📔 No entries yet!</h4>
        <p>Start writing your first journal entry in the "Write New Entry" tab! ✨</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"### You have {len(entries)} entries 📚")
    
    for entry in entries:
        with st.container():
            st.markdown(f"""
            <div class="entry-card">
            <h4>📝 {entry['title']}</h4>
            <small>Created: {entry['created_at'][:16]} | Updated: {entry['updated_at'][:16]}</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Show content preview
            preview = entry['content'][:200] + "..." if len(entry['content']) > 200 else entry['content']
            st.write(preview)
            
            col1, col2, col3 = st.columns([1, 1, 4])
            
            with col1:
                if st.button(f"✏️ Edit", key=f"edit_{entry['id']}"):
                    st.session_state.editing_entry = entry
            
            with col2:
                if st.button(f"🗑️ Delete", key=f"delete_{entry['id']}"):
                    if delete_journal_entry(entry['id']):
                        st.success("Entry deleted! 🗑️")
                        st.rerun()
                    else:
                        st.error("Failed to delete entry 😞")
            
            # Edit form if this entry is being edited
            if 'editing_entry' in st.session_state and st.session_state.editing_entry['id'] == entry['id']:
                with st.form(f"edit_form_{entry['id']}"):
                    new_title = st.text_input("Title", value=entry['title'])
                    new_content = st.text_area("Content", value=entry['content'], height=200)
                    
                    # Ensure new_title and new_content are always strings
                    safe_title = new_title if new_title is not None else ""
                    safe_content = new_content if new_content is not None else ""
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Save Changes"):
                            if update_journal_entry(entry['id'], safe_title, safe_content):
                                st.success("Entry updated! ✨")
                                del st.session_state.editing_entry
                                st.rerun()
                            else:
                                st.error("Failed to update entry 😞")
                    
                    with col_cancel:
                        if st.form_submit_button("❌ Cancel"):
                            del st.session_state.editing_entry
                            st.rerun()
            
            st.divider()

def show_new_entry_form():
    """Display form to create a new journal entry."""
    st.markdown("### ✍️ Write a new entry")
    
    with st.form("new_entry_form"):
        title = st.text_input("📝 Entry Title", placeholder="What's on your mind today?")
        content = st.text_area(
            "📖 Your thoughts...", 
            placeholder="Write your journal entry here. Share your thoughts, experiences, or anything you'd like to remember!",
            height=300
        )
        
        if st.form_submit_button("🌟 Save Entry"):
            if title and content:
                if create_journal_entry(st.session_state.user['id'], title, content):
                    st.success("Entry saved! ✨")
                    st.balloons()
                else:
                    st.error("Failed to save entry 😞")
            else:
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
