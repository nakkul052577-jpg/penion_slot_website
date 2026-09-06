import sqlite3, time, uuid
from pathlib import Path
import streamlit as st
DB_PATH = Path(__file__).resolve().parents[1] / 'database.db'
def db():
    c=sqlite3.connect(DB_PATH, timeout=10); c.row_factory=sqlite3.Row; return c
def init():
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS buzzer_rooms(room_id TEXT PRIMARY KEY,status TEXT,created_at REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS buzzer_players(room_id TEXT,player_id TEXT,name TEXT,joined_at REAL,PRIMARY KEY(room_id,player_id))")
        c.execute("CREATE TABLE IF NOT EXISTS buzzer_presses(room_id TEXT,player_id TEXT,name TEXT,press_order INTEGER,pressed_at REAL,PRIMARY KEY(room_id,player_id))")
def show_buzzer():
    init(); st.subheader('リアル早押し')
    st.session_state.setdefault('buzzer_id',uuid.uuid4().hex); st.session_state.setdefault('buzzer_room',None)
    if not st.session_state.buzzer_room:
        if st.button('新しい部屋を作成',use_container_width=True):
            rid=uuid.uuid4().hex[:6].upper()
            with db() as c:c.execute("INSERT INTO buzzer_rooms VALUES(?,?,?)",(rid,'waiting',time.time()))
            st.session_state.buzzer_room=rid; st.rerun()
        rid=st.text_input('部屋番号').strip().upper()
        if st.button('部屋に参加',use_container_width=True):
            with db() as c: ok=c.execute('SELECT 1 FROM buzzer_rooms WHERE room_id=?',(rid,)).fetchone()
            if ok: st.session_state.buzzer_room=rid; st.rerun()
            else: st.error('部屋がありません')
        return
    rid=st.session_state.buzzer_room; name=st.text_input('自分の名前',key='buzzer_name')
    if st.button('参加・名前を更新',use_container_width=True) and name.strip():
        with db() as c:c.execute('INSERT OR REPLACE INTO buzzer_players VALUES(?,?,?,?)',(rid,st.session_state.buzzer_id,name.strip(),time.time()))
    with db() as c:
        room=c.execute('SELECT * FROM buzzer_rooms WHERE room_id=?',(rid,)).fetchone(); players=c.execute('SELECT * FROM buzzer_players WHERE room_id=? ORDER BY joined_at',(rid,)).fetchall(); presses=c.execute('SELECT * FROM buzzer_presses WHERE room_id=? ORDER BY press_order',(rid,)).fetchall()
    st.markdown(f'### 部屋番号：`{rid}`'); st.write('参加メンバー')
    for p in players: st.write('・'+p['name'])
    if room['status']=='waiting':
        if st.button('ゲーム開始',use_container_width=True):
            with db() as c:c.execute("UPDATE buzzer_rooms SET status='playing' WHERE room_id=?",(rid,))
            st.rerun()
    else:
        mine=any(p['player_id']==st.session_state.buzzer_id for p in presses)
        if not mine and st.button('早押し！',use_container_width=True):
            with db() as c:
                n=c.execute('SELECT COUNT(*) FROM buzzer_presses WHERE room_id=?',(rid,)).fetchone()[0]
                c.execute('INSERT OR IGNORE INTO buzzer_presses VALUES(?,?,?,?,?)',(rid,st.session_state.buzzer_id,name.strip(),n+1,time.time()))
            st.rerun()
        for p in presses: st.write(f"**{p['press_order']}位**　{p['name']}")
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=1000,key='buzzer_refresh')
    except ImportError: st.caption('リアルタイム更新には streamlit-autorefresh を追加してください。')
