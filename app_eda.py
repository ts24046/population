import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # 앱 개요
        st.markdown("""
        ---
        **Available Analyses**
        - **Population Trends EDA**: 한국의 지역별 연도별 인구 변화 분석
        """
        )

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("Population Trends EDA")

        # 1) file uploader
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            return
        df = pd.read_csv(uploaded)

        # 2) preprocessing
        # replace '-' → 0 for Sejong only
        mask = df['지역'] == '세종'
        df.loc[mask, :] = df.loc[mask, :].replace('-', 0)
        # convert specified columns to numeric
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.fillna(0, inplace=True)

        # 3) map Korean region names to English
        region_mapping = {
            '전국':  'National',
            '세종':  'Sejong',
            '서울':  'Seoul',
            '부산':  'Busan',
            '대구':  'Daegu',
            '인천':  'Incheon',
            '광주':  'Gwangju',
            '대전':  'Daejeon',
            '울산':  'Ulsan',
            '경기':  'Gyeonggi',
            '강원':  'Gangwon',
            '충북':  'Chungbuk',
            '충남':  'Chungnam',
            '전북':  'Jeonbuk',
            '전남':  'Jeonnam',
            '경북':  'Gyeongbuk',
            '경남':  'Gyeongnam',
            '제주':  'Jeju'
        }
        df['region_en'] = df['지역'].map(region_mapping).fillna(df['지역'])

        # 4) set up tabs
        tabs = st.tabs([
            "Basic Statistics",
            "Yearly Trends",
            "Regional Changes",
            "Top 100 Changes",
            "Area Chart"
        ])

        # Tab 1: Basic Statistics
        with tabs[0]:
            st.header("Basic Statistics")
            buf = io.StringIO()
            df.info(buf=buf)
            st.text(buf.getvalue())
            st.write(df.describe())

        # Tab 2: Yearly Trends + 2035 forecast
        with tabs[1]:
            st.header("Yearly Total Population Trend")
            total = (
                df[df['region_en'] == 'National']
                .groupby('연도')['인구']
                .sum()
                .reset_index()
            )
            # plot historical trend
            fig, ax = plt.subplots()
            ax.plot(total['연도'], total['인구'], marker='o', label='Actual')
            # forecast to 2035 based on last 3-year net change
            last3 = total.tail(3)
            net_changes = last3['인구'].diff().dropna()
            avg_change = net_changes.mean()
            years = list(total['연도']) + [2035]
            pops = list(total['인구']) + [total['인구'].iloc[-1] + avg_change * (2035 - total['연도'].iloc[-1])]
            ax.plot(years, pops, linestyle='--', marker='x', label='Forecast')
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.set_title("Total Population Trend (incl. 2035 Forecast)")
            ax.legend()
            st.pyplot(fig)

        # Tab 3: Regional Changes (last 5 years)
        with tabs[2]:
            st.header("Regional Population Change (Last 5 Years)")
            yrs = sorted(df['연도'].unique())
            recent, past = yrs[-1], yrs[-6]
            pivot = (
                df[df['region_en'] != 'National']
                .pivot(index='region_en', columns='연도', values='인구')
            )
            pivot['change'] = pivot[recent] - pivot[past]
            pivot = pivot.sort_values('change', ascending=False)
            # convert to thousands
            pivot['change_k'] = pivot['change'] / 1_000
            fig, ax = plt.subplots()
            sns.barplot(
                x='change_k',
                y=pivot.index,
                data=pivot.reset_index(),
                ax=ax
            )
            ax.set_xlabel("Change (thousands)")
            ax.set_ylabel("")
            ax.set_title("5-Year Population Change by Region")
            # annotate values
            for i, v in enumerate(pivot['change_k']):
                ax.text(v, i, f"{v:.1f}k", va='center')
            st.pyplot(fig)

        # Tab 4: Top 100 Yearly Changes
        with tabs[3]:
            st.header("Top 100 Yearly Population Increases")
            df_diff = df[df['region_en'] != 'National'].copy()
            df_diff['yearly_diff'] = df_diff.groupby('region_en')['인구'].diff()
            top100 = (
                df_diff.nlargest(100, 'yearly_diff')
                [['region_en', '연도', 'yearly_diff']]
                .rename(columns={'region_en': 'Region', '연도': 'Year', 'yearly_diff': 'Change'})
            )
            styled = (
                top100.style
                .background_gradient(subset=['Change'], cmap='Blues', axis=0)
                .format({"Change": "{:,.0f}"})
            )
            st.dataframe(styled)

        # Tab 5: Area Chart
        with tabs[4]:
            st.header("Cumulative Area Chart by Region")
            area_df = (
                df[df['region_en'] != 'National']
                .pivot(index='연도', columns='region_en', values='인구')
            )
            fig, ax = plt.subplots()
            area_df.plot.area(ax=ax)
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.set_title("Population by Region Over Time")
            st.pyplot(fig)

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()