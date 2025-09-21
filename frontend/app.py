import streamlit as st
import sqlite3
import hashlib
import datetime
import json
from typing import List, Dict, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="Cozy Journal - Your Digital Sanctuary",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Database initialization
def init_database():
    """Initialize the database with required tables."""
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create journal entries table
    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            mood TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hash a password with salt."""
    salt = "cozy_journal_salt"
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def create_user(username: str, password: str) -> bool:
    """Create a new user account."""
    try:
        conn = sqlite3.connect('journal.db')
        c = conn.cursor()
        
        password_hash = hash_password(password)
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                 (username, password_hash))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username: str, password: str) -> Optional[int]:
    """Verify user credentials and return user ID if valid."""
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    
    password_hash = hash_password(password)
    c.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", 
             (username, password_hash))
    
    result = c.fetchone()
    conn.close()
    
    return result[0] if result else None

def add_journal_entry(user_id: int, title: str, content: str, mood: str) -> bool:
    """Add a new journal entry."""
    try:
        conn = sqlite3.connect('journal.db')
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO journal_entries (user_id, title, content, mood) 
            VALUES (?, ?, ?, ?)
        """, (user_id, title, content, mood))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_user_entries(user_id: int) -> List[Dict]:
    """Get all journal entries for a user."""
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT id, title, content, mood, date_created 
        FROM journal_entries 
        WHERE user_id = ? 
        ORDER BY date_created DESC
    """, (user_id,))
    
    entries = []
    for row in c.fetchall():
        entries.append({
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'mood': row[3],
            'date_created': row[4]
        })
    
    conn.close()
    return entries

def delete_entry(entry_id: int, user_id: int) -> bool:
    """Delete a journal entry."""
    try:
        conn = sqlite3.connect('journal.db')
        c = conn.cursor()
        
        c.execute("DELETE FROM journal_entries WHERE id = ? AND user_id = ?", 
                 (entry_id, user_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

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
        opacity: 0.15;
        font-size: 20px;
        animation: gentleFall 20s infinite linear;
        pointer-events: none;
        z-index: -1;
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
        transition: all 0.3s ease;
    }
    
    .entry-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(218, 165, 127, 0.2);
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
    
    /* Hide only sidebar elements, not main content */
    .css-1d391kg { display: none !important; }
    .css-1rs6os { display: none !important; }
    .css-17eq0hr { display: none !important; }
    
    /* Ensure main content is visible */
    .main .block-container { 
        padding-top: 2rem !important; 
        padding-bottom: 1rem !important;
        position: relative !important;
        z-index: 10 !important;
    }
    
    /* Ensure all content containers are visible */
    .stMarkdown, .stButton, .stTextInput, .stTextArea, .stTabs, .stForm {
        position: relative !important;
        z-index: 10 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def show_login_page():
    """Display the login/signup page with animations."""
    
    # Background music component
    st.markdown("""
    <div id="backgroundMusic"></div>
    <script>
    if (typeof window.backgroundMusicInitialized === 'undefined') {
        window.backgroundMusicInitialized = true;
        
        // Create audio context for rain sounds
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        function createRainSound() {
            const bufferSize = audioContext.sampleRate * 2;
            const noiseBuffer = audioContext.createBuffer(1, bufferSize, audioContext.sampleRate);
            const output = noiseBuffer.getChannelData(0);
            
            for (let i = 0; i < bufferSize; i++) {
                output[i] = Math.random() * 2 - 1;
            }
            
            const whiteNoise = audioContext.createBufferSource();
            whiteNoise.buffer = noiseBuffer;
            whiteNoise.loop = true;
            
            const bandpass = audioContext.createBiquadFilter();
            bandpass.type = 'bandpass';
            bandpass.frequency.value = 1000;
            
            const lowpass = audioContext.createBiquadFilter();
            lowpass.type = 'lowpass';
            lowpass.frequency.value = 800;
            
            const gainNode = audioContext.createGain();
            gainNode.gain.value = 0.3;
            
            whiteNoise.connect(bandpass);
            bandpass.connect(lowpass);
            lowpass.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            return whiteNoise;
        }
        
        // Start rain sound
        audioContext.resume().then(() => {
            const rainSound = createRainSound();
            rainSound.start();
        });
    }
    </script>
    """, unsafe_allow_html=True)
    
    # Music player display
    st.markdown("""
    <div class="music-player">
        <span class="music-emoji">🎵</span>
        Ambient Rain Sounds
    </div>
    """, unsafe_allow_html=True)
    
    # Main title with animation
    st.markdown('<h1 class="title">🍂 Cozy Journal ☕</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Your peaceful digital sanctuary for thoughts and memories</p>', unsafe_allow_html=True)
    
    # Login container
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Tab-based interface
        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                st.markdown("### Welcome Back!")
                
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                login_button = st.form_submit_button("Sign In", use_container_width=True)
                
                if login_button:
                    if username and password:
                        user_id = verify_user(username, password)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.session_state.username = username
                            st.session_state.logged_in = True
                            st.session_state.current_page = 'dashboard'
                            st.success("Welcome back! ☕")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.error("Please fill in all fields")
        
        with tab2:
            with st.form("signup_form"):
                st.markdown("### Join Our Cozy Community!")
                
                new_username = st.text_input("Choose Username", placeholder="Pick a unique username")
                new_password = st.text_input("Create Password", type="password", placeholder="Create a secure password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                signup_button = st.form_submit_button("Create Account", use_container_width=True)
                
                if signup_button:
                    if new_username and new_password and confirm_password:
                        if new_password == confirm_password:
                            if create_user(new_username, new_password):
                                st.success("Account created successfully! Please sign in.")
                            else:
                                st.error("Username already exists")
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.error("Please fill in all fields")
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_journal_dashboard():
    """Display the main dashboard with pixel art desk."""
    
    st.markdown("""
    <div class="pixel-desk-container">
        <h1 class="title">📚 Your Cozy Writing Desk</h1>
        
        <div class="pixel-desk">
            <div class="desk-wood"></div>
            <div class="coffee-cup">
                <div class="steam"></div>
                ☕
            </div>
            <div class="journal-book">📖</div>
            <div class="pen">✒️</div>
            <div class="plant">🌱</div>
        </div>
    </div>
    
    <style>
    .pixel-desk-container {
        text-align: center;
        margin: 20px 0;
        position: relative;
        z-index: 1;
    }
    
    .pixel-desk {
        background: linear-gradient(145deg, #8b6914, #a67c52);
        height: 150px;
        border-radius: 20px;
        position: relative;
        margin: 30px auto;
        max-width: 800px;
        box-shadow: 0 15px 35px rgba(139, 105, 20, 0.3);
        border: 3px solid #6b4e0f;
        display: flex;
        align-items: center;
        justify-content: space-around;
        padding: 20px;
    }
    
    .desk-wood::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            repeating-linear-gradient(
                90deg,
                transparent,
                transparent 2px,
                rgba(107, 78, 15, 0.1) 2px,
                rgba(107, 78, 15, 0.1) 4px
            );
        border-radius: 20px;
    }
    
    .coffee-cup {
        font-size: 3em;
        position: relative;
        animation: steamRise 3s infinite;
    }
    
    .steam {
        position: absolute;
        top: -20px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 0.3em;
        opacity: 0.6;
        animation: steamFloat 2s infinite;
    }
    
    .steam::before {
        content: '💨';
    }
    
    @keyframes steamFloat {
        0% { transform: translateX(-50%) translateY(0px); opacity: 0.6; }
        50% { transform: translateX(-45%) translateY(-10px); opacity: 0.3; }
        100% { transform: translateX(-50%) translateY(-20px); opacity: 0; }
    }
    
    @keyframes steamRise {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-2px); }
    }
    
    .journal-book, .pen, .plant {
        font-size: 2.5em;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .journal-book:hover, .pen:hover, .plant:hover {
        transform: translateY(-5px) scale(1.1);
        filter: brightness(1.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Quick stats
    entries = get_user_entries(st.session_state.user_id)
    total_entries = len(entries)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{total_entries}</div>
            <div class="metric-label">Total Entries</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        recent_entries = len([e for e in entries if 
                           datetime.datetime.strptime(e['date_created'], '%Y-%m-%d %H:%M:%S').date() == 
                           datetime.date.today()])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{recent_entries}</div>
            <div class="metric-label">Today</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        week_entries = len([e for e in entries if 
                          (datetime.date.today() - 
                           datetime.datetime.strptime(e['date_created'], '%Y-%m-%d %H:%M:%S').date()).days <= 7])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{week_entries}</div>
            <div class="metric-label">This Week</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if entries:
            moods = [e['mood'] for e in entries if e['mood']]
            if moods:
                mood_counts = {}
                for mood in moods:
                    mood_counts[mood] = mood_counts.get(mood, 0) + 1
                most_common_mood = max(mood_counts.items(), key=lambda x: x[1])[0]
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-number">{most_common_mood}</div>
                    <div class="metric-label">Common Mood</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("### ✨ What would you like to do?")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Write New Entry", use_container_width=True):
            st.session_state.current_page = 'new_entry'
            st.rerun()
    
    with col2:
        if st.button("📖 View All Entries", use_container_width=True):
            st.session_state.current_page = 'entries'
            st.rerun()
    
    with col3:
        if st.button("🌧️ Rainfall Reverie", use_container_width=True):
            st.session_state.current_page = 'rainfall'
            st.rerun()
    
    with col4:
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Recent entries preview
    if entries:
        st.markdown("### 📚 Recent Entries")
        for entry in entries[:3]:
            with st.container():
                st.markdown(f"""
                <div class="entry-card">
                    <h4>{entry['title']} {entry['mood'] if entry['mood'] else ''}</h4>
                    <p style="font-size: 0.9em; color: #a67c52; margin: 5px 0;">
                        {entry['date_created']}
                    </p>
                    <p>{entry['content'][:200]}{'...' if len(entry['content']) > 200 else ''}</p>
                </div>
                """, unsafe_allow_html=True)

def show_new_entry_form():
    """Display the form for creating a new journal entry."""
    st.markdown('<h1 class="title">📝 Write Your Heart Out</h1>', unsafe_allow_html=True)
    
    with st.form("new_entry_form"):
        title = st.text_input("Entry Title", placeholder="What's on your mind today?")
        
        mood_options = ["😊 Happy", "😔 Sad", "😤 Angry", "😰 Anxious", "😌 Peaceful", 
                       "🤔 Thoughtful", "😴 Tired", "🥳 Excited", "😮 Surprised", "💕 Loved"]
        mood = st.selectbox("How are you feeling?", [""] + mood_options)
        
        content = st.text_area(
            "Your thoughts...", 
            placeholder="Pour your heart out here... ☕\n\nWhat happened today? How did it make you feel? What are you grateful for?",
            height=300
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submit_button = st.form_submit_button("💾 Save Entry", use_container_width=True)
        with col2:
            if st.form_submit_button("🏠 Back to Dashboard", use_container_width=True):
                st.session_state.current_page = 'dashboard'
                st.rerun()
        
        if submit_button:
            if title and content:
                if add_journal_entry(st.session_state.user_id, title, content, mood):
                    st.success("Entry saved successfully! ✨")
                    st.balloons()
                    st.session_state.current_page = 'dashboard'
                    st.rerun()
                else:
                    st.error("Failed to save entry")
            else:
                st.error("Please fill in both title and content")

def show_entries_list():
    """Display all journal entries for the user."""
    st.markdown('<h1 class="title">📖 Your Journal Collection</h1>', unsafe_allow_html=True)
    
    entries = get_user_entries(st.session_state.user_id)
    
    if not entries:
        st.markdown("""
        <div class="entry-card" style="text-align: center;">
            <h3>📝 No entries yet!</h3>
            <p>Start your journaling journey by writing your first entry.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✍️ Write First Entry", use_container_width=True):
            st.session_state.current_page = 'new_entry'
            st.rerun()
    else:
        # Search and filter
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔍 Search entries", placeholder="Search by title or content...")
        with col2:
            if st.button("🏠 Back to Dashboard"):
                st.session_state.current_page = 'dashboard'
                st.rerun()
        
        # Filter entries based on search
        if search_term:
            filtered_entries = [e for e in entries if 
                              search_term.lower() in e['title'].lower() or 
                              search_term.lower() in e['content'].lower()]
        else:
            filtered_entries = entries
        
        st.markdown(f"### Found {len(filtered_entries)} entries")
        
        # Display entries
        for entry in filtered_entries:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="entry-card">
                        <h4>{entry['title']} {entry['mood'] if entry['mood'] else ''}</h4>
                        <p style="font-size: 0.9em; color: #a67c52; margin: 5px 0;">
                            📅 {entry['date_created']}
                        </p>
                        <p>{entry['content']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{entry['id']}"):
                        if delete_entry(entry['id'], st.session_state.user_id):
                            st.success("Entry deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete entry")

def show_rainfall_reverie():
    """Display the rainfall reverie page with ambient sounds and animations."""
    
    # Rain sound generation
    st.markdown("""
    <script>
    if (typeof window.rainSoundInitialized === 'undefined') {
        window.rainSoundInitialized = true;
        
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        function createRainSound() {
            const bufferSize = audioContext.sampleRate * 2;
            const noiseBuffer = audioContext.createBuffer(1, bufferSize, audioContext.sampleRate);
            const output = noiseBuffer.getChannelData(0);
            
            for (let i = 0; i < bufferSize; i++) {
                output[i] = Math.random() * 2 - 1;
            }
            
            const whiteNoise = audioContext.createBufferSource();
            whiteNoise.buffer = noiseBuffer;
            whiteNoise.loop = true;
            
            const bandpass = audioContext.createBiquadFilter();
            bandpass.type = 'bandpass';
            bandpass.frequency.value = 800;
            
            const lowpass = audioContext.createBiquadFilter();
            lowpass.type = 'lowpass';
            lowpass.frequency.value = 600;
            
            const gainNode = audioContext.createGain();
            gainNode.gain.value = 0.2;
            
            whiteNoise.connect(bandpass);
            bandpass.connect(lowpass);
            lowpass.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            return whiteNoise;
        }
        
        audioContext.resume().then(() => {
            const rainSound = createRainSound();
            rainSound.start();
        });
    }
    </script>
    """, unsafe_allow_html=True)
    
    # Main rainfall scene
    st.markdown("""
    <div class="rainfall-scene">
        <div class="window-frame">
            <div class="window-view">
                <div class="rain-overlay"></div>
                <div class="tree-silhouette"></div>
                <div class="falling-leaves"></div>
                <div class="ground"></div>
            </div>
        </div>
        
        <div class="indoor-scene">
            <div class="desk-setup">
                <div class="coffee-cup-pixel">
                    <div class="steam-animation">💨</div>
                    ☕
                </div>
                <div class="journal-open">📖</div>
                <div class="pen-writing">✒️</div>
                <div class="candle">🕯️</div>
            </div>
        </div>
        
        <div class="rainfall-controls">
            <h2>🌧️ Rainfall Reverie</h2>
            <p>Let the gentle rain soothe your thoughts as you write...</p>
        </div>
    </div>
    
    <style>
    .rainfall-scene {
        position: relative;
        min-height: 80vh;
        background: linear-gradient(135deg, #2c3e50, #34495e);
        border-radius: 25px;
        overflow: hidden;
        margin: 20px 0;
        box-shadow: 0 20px 40px rgba(44, 62, 80, 0.3);
    }
    
    .window-frame {
        position: absolute;
        top: 20px;
        left: 20px;
        width: 60%;
        height: 70%;
        background: linear-gradient(145deg, #8b6914, #a67c52);
        border-radius: 20px;
        padding: 20px;
        box-shadow: inset 0 4px 8px rgba(0, 0, 0, 0.3);
    }
    
    .window-view {
        width: 100%;
        height: 100%;
        background: linear-gradient(to bottom, #87CEEB, #98FB98);
        border-radius: 15px;
        position: relative;
        overflow: hidden;
    }
    
    .rain-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: repeating-linear-gradient(
            90deg,
            transparent 0px,
            transparent 2px,
            rgba(255, 255, 255, 0.1) 2px,
            rgba(255, 255, 255, 0.1) 4px
        );
        animation: rainFall 0.5s linear infinite;
    }
    
    @keyframes rainFall {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100%); }
    }
    
    .tree-silhouette {
        position: absolute;
        bottom: 20%;
        left: 10%;
        width: 80px;
        height: 120px;
        background: #2d5016;
        border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
    }
    
    .tree-silhouette::before {
        content: '';
        position: absolute;
        bottom: -30px;
        left: 50%;
        transform: translateX(-50%);
        width: 20px;
        height: 50px;
        background: #4a4a4a;
        border-radius: 2px;
    }
    
    .falling-leaves {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        animation: leavesFalling 15s infinite linear;
        font-size: 20px;
        opacity: 0.8;
    }
    
    .falling-leaves::before {
        content: '🍂 🍁 🌿 🍂 🍁 🌿';
        position: absolute;
        top: -50px;
        left: 0;
        width: 100%;
        animation: gentleDrift 12s infinite linear;
    }
    
    @keyframes gentleDrift {
        0% { 
            transform: translateY(-50px) translateX(0px) rotate(0deg); 
            opacity: 0; 
        }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { 
            transform: translateY(400px) translateX(50px) rotate(360deg); 
            opacity: 0; 
        }
    }
    
    .ground {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 20%;
        background: linear-gradient(to bottom, #9ACD32, #6B8E23);
    }
    
    .indoor-scene {
        position: absolute;
        bottom: 20px;
        right: 20px;
        width: 35%;
        height: 60%;
    }
    
    .desk-setup {
        background: linear-gradient(145deg, #8b6914, #a67c52);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 15px 35px rgba(139, 105, 20, 0.4);
        border: 3px solid #6b4e0f;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-around;
        height: 100%;
    }
    
    .coffee-cup-pixel {
        font-size: 3em;
        position: relative;
        animation: steamRise 3s infinite ease-in-out;
    }
    
    .steam-animation {
        position: absolute;
        top: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 0.4em;
        animation: steamFloat 2s infinite ease-in-out;
    }
    
    @keyframes steamFloat {
        0% { transform: translateX(-50%) translateY(0px); opacity: 0.8; }
        50% { transform: translateX(-45%) translateY(-15px); opacity: 0.4; }
        100% { transform: translateX(-50%) translateY(-30px); opacity: 0; }
    }
    
    .journal-open, .pen-writing, .candle {
        font-size: 2em;
        margin: 10px 0;
        animation: gentleBob 4s infinite ease-in-out;
    }
    
    .pen-writing {
        animation-delay: 0.5s;
    }
    
    .candle {
        animation-delay: 1s;
    }
    
    @keyframes gentleBob {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-3px); }
    }
    
    .rainfall-controls {
        position: absolute;
        top: 20px;
        right: 20px;
        background: rgba(255, 248, 240, 0.9);
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        backdrop-filter: blur(10px);
        border: 2px solid #f2e8d5;
        max-width: 300px;
    }
    
    .rainfall-controls h2 {
        color: #8b6914;
        font-family: 'Caveat', cursive;
        margin-bottom: 10px;
    }
    
    .rainfall-controls p {
        color: #a67c52;
        font-family: 'Comfortaa', cursive;
        font-size: 14px;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Control buttons
    st.markdown("### 🎮 Reverie Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Write in the Rain", use_container_width=True):
            st.session_state.current_page = 'new_entry'
            st.rerun()
    
    with col2:
        if st.button("📖 Read Past Entries", use_container_width=True):
            st.session_state.current_page = 'entries'
            st.rerun()
    
    with col3:
        if st.button("🏠 Back to Dashboard", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    # Ambient text
    st.markdown("""
    <div class="entry-card" style="text-align: center; margin-top: 20px;">
        <h4>🌧️ The Art of Rainy Day Reflection</h4>
        <p style="font-style: italic; color: #a67c52;">
        There's something magical about the sound of rain that makes our thoughts flow more freely. 
        Let this gentle rainfall be the soundtrack to your inner voice, washing away the noise 
        of the day and leaving space for what truly matters.
        </p>
        <p style="font-size: 0.9em; color: #8b6914;">
        Take a moment. Breathe. Let the rain carry your worries away. ☕
        </p>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application logic."""
    # Initialize database
    init_database()
    
    # Apply custom CSS
    apply_custom_css()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'login'
    
    # Page routing
    if not st.session_state.logged_in:
        show_login_page()
    else:
        # Hidden navigation for JavaScript interaction
        with st.sidebar:
            st.markdown("### Navigation")
            if st.button("🏠 Dashboard", key="nav_dashboard"):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            if st.button("📝 New Entry", key="nav_new_entry"):
                st.session_state.current_page = 'new_entry'
                st.rerun()
            if st.button("📖 View Entries", key="nav_entries"):
                st.session_state.current_page = 'entries'
                st.rerun()
            if st.button("🌧️ Rainfall Reverie", key="nav_rainfall"):
                st.session_state.current_page = 'rainfall'
                st.rerun()
            if st.button("🚪 Sign Out", key="nav_logout"):
                st.session_state.clear()
                st.rerun()
        
        # Main content based on current page
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

if __name__ == "__main__":
    main()