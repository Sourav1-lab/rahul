import streamlit as st
import requests
import urllib3
import json
import time
import sqlite3

# ---------------- SSL WARNING OFF ----------------
urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# ---------------- CONFIG ----------------
BASE_URL = "https://panthers.accbazaar.shop"

HEADERS = {
    "X-API-Key": "panthers_SedeBGQP5haNegFjjsT4tr4Px2Op3vPj1q5jgw",
    "Content-Type": "application/json"
}

GAME_SERVICES = [
    "567slot_game",
    "Yono_vip",
    "mbmbet_game",
    "yonoslot_game",
    "789jackpot_game"
]

# ---------------- DATABASE ----------------

@st.cache_resource
def init_db():

    conn = sqlite3.connect(
        "database.db",
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        stats TEXT
    )
    """)

    conn.commit()

    return conn


conn = init_db()
cursor = conn.cursor()


def create_admin():

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        ("admin",)
    )

    admin = cursor.fetchone()

    if not admin:

        default_stats = json.dumps({
            g.split("_")[0]: 0
            for g in GAME_SERVICES
        })

        cursor.execute("""
        INSERT INTO users
        (username, password, role, stats)
        VALUES (?, ?, ?, ?)
        """, (
            "admin",
            "admin",
            "admin",
            default_stats
        ))

        conn.commit()


create_admin()


def load_db():

    cursor.execute("SELECT * FROM users")

    users = {}

    rows = cursor.fetchall()

    for row in rows:

        try:

            stats = json.loads(row["stats"])

        except:

            stats = {
                g.split("_")[0]: 0
                for g in GAME_SERVICES
            }

        users[row["username"]] = {
            "password": row["password"],
            "role": row["role"],
            "stats": stats
        }

    return users


def save_user(username, password, role, stats):

    cursor.execute("""
    INSERT OR REPLACE INTO users
    (username, password, role, stats)
    VALUES (?, ?, ?, ?)
    """, (
        username,
        password,
        role,
        json.dumps(stats)
    ))

    conn.commit()


# ---------------- API FUNCTIONS ----------------

def send_otp(phone, app_name):

    url = f"{BASE_URL}/v1/register/send_otp"

    retry = 0

    while retry <= 2:

        try:

            res = requests.post(
                url,
                headers=HEADERS,
                json={
                    "phone": str(phone),
                    "app_name": app_name
                },
                verify=False,
                timeout=20
            )

            data = res.json()

            if data.get("status") == "success":
                return data

            error_msg = data.get("message", "")

            if (
                "Auth Proxy Error" in error_msg
                and "403" in error_msg
            ):
                retry += 1
                time.sleep(1)
                continue

            return data

        except Exception as e:

            retry += 1

            if retry > 2:

                return {
                    "status": "error",
                    "message": str(e)
                }

            time.sleep(1)


def verify_otp(task_id, otp):

    url = f"{BASE_URL}/v1/register/verify_otp"

    try:

        payload = {
            "task_id": str(task_id),
            "otp": str(otp)
        }

        res = requests.post(
            url,
            headers=HEADERS,
            json=payload,
            verify=False,
            timeout=20
        )

        return res.json()

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Panther Ultimate Panel",
    layout="wide"
)

st.markdown("""
<style>

/* Main Buttons */
.stButton > button {

    border-radius: 12px;

    font-weight: 700;

    border: none;

    background:
    linear-gradient(
        135deg,
        #2563eb,
        #1d4ed8
    );

    color: white;
}

/* Success Row */
.success-box {

    padding: 8px;

    border-radius: 10px;

    border:
    1px solid rgba(0,255,120,0.18);

    margin-bottom: 10px;

    background:
    rgba(0,255,120,0.03);
}

/* Pending Row */
.pending-box {

    padding: 8px;

    border-radius: 10px;

    border:
    1px solid rgba(255,255,255,0.06);

    margin-bottom: 10px;
}

/* Counter */
.counter-box {

    padding: 12px;

    border-radius: 12px;

    border:
    1px solid rgba(255,255,255,0.08);

    margin-bottom: 14px;

    text-align: center;

    font-size: 14px;

    font-weight: 700;

    background:
    rgba(37,99,235,0.08);
}

/* Inputs */
.stTextInput input {

    border-radius: 10px;

    background: white;

    color: black;

    font-weight: 600;
}

/* Multiselect */
.stMultiSelect div {

    border-radius: 10px;
}

/* Better Labels */
label {

    font-weight: 600 !important;
}
label {

    font-weight: 600 !important;
}

div[data-testid="column"]:nth-child(4) button {

    background: #f59e0b !important;

    color: white !important;

    border: none !important;
}

</style>
""", unsafe_allow_html=True)

db = load_db()

# ---------------- SESSION ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "multi_tasks" not in st.session_state:
    st.session_state.multi_tasks = {}

if "submitted_tasks" not in st.session_state:
    st.session_state.submitted_tasks = {}

# ---------------- LOGIN ----------------

if not st.session_state.logged_in:

    st.title("🔐 Tool Login")

    user_id = st.text_input("User ID")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button(
        "Login",
        use_container_width=True
    ):

        user_id = user_id.strip().lower()

        if (
            user_id in db
            and db[user_id]["password"] == password
        ):

            st.session_state.logged_in = True
            st.session_state.user = user_id
            st.session_state.role = db[user_id]["role"]

            st.rerun()

        else:

            st.error("Invalid Credentials")

# ---------------- MAIN APP ----------------

else:

    user = st.session_state.user
    role = st.session_state.role

    st.sidebar.title(f"👤 {user.upper()}")

    nav = st.sidebar.radio(
        "Menu",
        ["Registration Tool", "Admin Panel"]
        if role == "admin"
        else ["Registration Tool"]
    )

    # ---------------- ADMIN PANEL ----------------

    if nav == "Admin Panel":

        st.header("🛠 Admin Control Center")

        tab1, tab2 = st.tabs([
            "➕ Add User",
            "👥 Manage Users"
        ])

        with tab1:

            new_user = st.text_input(
                "New User ID"
            ).strip().lower()

            new_pass = st.text_input(
                "New Password"
            )

            if st.button("Create User"):

                if not new_user or not new_pass:

                    st.warning("Fill all fields")

                elif new_user in db:

                    st.error("User already exists")

                else:

                    stats = {
                        g.split("_")[0]: 0
                        for g in GAME_SERVICES
                    }

                    save_user(
                        new_user,
                        new_pass,
                        "user",
                        stats
                    )

                    st.success("User Created")

                    time.sleep(1)

                    st.rerun()

        with tab2:

            db = load_db()

            users = [
                u for u in db.keys()
                if db[u]["role"] != "admin"
            ]

            if users:

                target = st.selectbox(
                    "Select User",
                    users
                )

                new_password = st.text_input(
                    "Change Password",
                    value=db[target]["password"]
                )

                st.write("### 📊 Stats")

                updated_stats = {}

                cols = st.columns(
                    len(db[target]["stats"])
                )

                for i, key in enumerate(
                    db[target]["stats"]
                ):

                    updated_stats[key] = cols[i].number_input(
                        key,
                        value=int(
                            db[target]["stats"][key]
                        ),
                        min_value=0
                    )

                if st.button(
                    "💾 Save Changes",
                    use_container_width=True
                ):

                    save_user(
                        target,
                        new_password,
                        db[target]["role"],
                        updated_stats
                    )

                    st.success("Updated")

                    time.sleep(1)

                    st.rerun()

    # ---------------- REGISTRATION TOOL ----------------

    else:

        db = load_db()

        stats = db[user]["stats"]

        st.markdown(f"""
        <div style="margin-left: 8px;">

        ### 👋 Welcome, {user.upper()}

        ##### Premium Dashboard

        </div>
        """, unsafe_allow_html=True)


        st.info(
            " | ".join([
                f"{k}: {v}"
                for k, v in stats.items()
            ])
        )

        st.divider()

        st.subheader("📲 Send Multi OTP")

        c1, c2 = st.columns([2, 1])

        with c1:

            selected_games = st.multiselect(
                "Select Apps",
                GAME_SERVICES,
                default=[GAME_SERVICES[0]]
            )

        with c2:

            phone = st.text_input(
                "Phone Number"
            ).strip()

        # ---------- SEND OTP ----------

        if st.button(
            "🚀 SEND ALL OTPs",
            use_container_width=True
        ):

            if len(phone) != 10:

                st.warning("Invalid Phone Number")

            elif not selected_games:

                st.warning("Select Apps")

            else:

                st.session_state.multi_tasks = {}
                st.session_state.submitted_tasks = {}

                status_placeholder = st.empty()

                progress = st.progress(0)

                for i, game in enumerate(
                    selected_games
                ):

                    status_placeholder.markdown(
                        f"📤 Sending OTP to `{game}`..."
                    )

                    res = send_otp(phone, game)

                    if res.get("status") == "success":

                        st.session_state.multi_tasks[
                            game
                        ] = res.get("task_id")

                        st.toast(f"✅ {game} Sent")

                    else:

                        st.error(
                            f"{game}: {res.get('message')}"
                        )

                    progress.progress(
                        (i + 1) / len(selected_games)
                    )

                    time.sleep(1)

                status_placeholder.empty()

                st.rerun()

        # ---------------- VERIFY AREA ----------------

        if st.session_state.multi_tasks:

            st.divider()

            success_count = len(
                st.session_state.submitted_tasks
            )

            pending_count = (
                len(st.session_state.multi_tasks)
                - success_count
            )

            st.markdown(f"""
            <div class="counter-box">
            ✅ Success: {success_count}
            &nbsp;&nbsp;&nbsp;
            ⏳ Pending: {pending_count}
            </div>
            """, unsafe_allow_html=True)

            with st.container(border=True):

                st.markdown(
                    "### ⚡ Smart Multi OTP Submit"
                )

                cc1, cc2 = st.columns([3, 1])

                otp_input = cc1.text_input(
                    "Enter Multiple OTPs",
                    placeholder="1234 5678 9012"
                )

                if cc2.button(
                    "🚀 Quick Submit",
                    type="primary",
                    use_container_width=True
                ):

                    otp_list = [
                        x.strip()
                        for x in otp_input.replace(
                            ",",
                            " "
                        ).split()
                        if x.strip()
                    ]

                    for current_otp in otp_list:

                        pending_apps = [

                            name

                            for name in st.session_state.multi_tasks

                            if name not in
                            st.session_state.submitted_tasks
                        ]

                        if not pending_apps:
                            break

                        for game in pending_apps:

                            result = verify_otp(
                                st.session_state.multi_tasks[game],
                                current_otp
                            )

                            if result.get("status") == "success":

                                st.session_state.submitted_tasks[
                                    game
                                ] = current_otp

                                db = load_db()

                                short_key = game.split("_")[0]

                                db[user]["stats"][
                                    short_key
                                ] += 1

                                save_user(
                                    user,
                                    db[user]["password"],
                                    db[user]["role"],
                                    db[user]["stats"]
                                )

                                st.toast(
                                    f"✅ {game} Success"
                                )

                                break

                            time.sleep(0.3)

                    st.rerun()

# ---------- INDIVIDUAL VERIFY ----------

            for game_name, task_id in list(
                st.session_state.multi_tasks.items()
            ):

                done = (
                    game_name in
                    st.session_state.submitted_tasks
                )

                box_class = (
                    "success-box"
                    if done
                    else "pending-box"
                )

                st.markdown(
                    f'<div class="{box_class}">',
                    unsafe_allow_html=True
                )

                with st.container():

                    col1, col2, col3, col4 = st.columns(
                        [1.5, 2, 1, 1]
                    )

                    col1.write(f"**{game_name}**")

                    current_otp = st.session_state.submitted_tasks.get(
                        game_name,
                        ""
                    )

                    final_text = (
                        f"{current_otp} ✅"
                        if done
                        else current_otp
                    )

                    otp_box = col2.text_input(
                        "OTP",
                        value=final_text,
                        key=f"otp_box_{game_name}_{len(st.session_state.submitted_tasks)}",
                        label_visibility="collapsed",
                        disabled=done
                    )

                    if not done:

                        # ---------- VERIFY OTP ----------

                        if col3.button(
                            "Verify",
                            key=f"verify_{game_name}",
                            use_container_width=True
                        ):

                            result = verify_otp(
                                task_id,
                                otp_box
                            )

                            if result.get("status") == "success":

                                st.session_state.submitted_tasks[
                                    game_name
                                ] = otp_box

                                db = load_db()

                                short_key = game_name.split("_")[0]

                                db[user]["stats"][
                                    short_key
                                ] += 1

                                save_user(
                                    user,
                                    db[user]["password"],
                                    db[user]["role"],
                                    db[user]["stats"]
                                )

                                st.rerun()

                            else:

                                st.error(
                                    result.get(
                                        "message",
                                        "Invalid OTP"
                                    )
                                )

                        # ---------- RESEND OTP ----------

                        if col4.button(
                            "🔄 Resend",
                            key=f"resend_{game_name}",
                            use_container_width=True
                        ):

                            resend = send_otp(
                                phone,
                                game_name
                            )

                            if resend.get("status") == "success":

                                st.session_state.multi_tasks[
                                    game_name
                                ] = resend.get("task_id")

                                st.toast(
                                    f"🔄 {game_name} OTP Resent"
                                )

                                st.rerun()

                            else:

                                st.error(
                                    resend.get(
                                        "message",
                                        "Resend Failed"
                                    )
                                )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )
    # ---------------- LOGOUT ----------------

    if st.sidebar.button(
        "Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False

        st.rerun()