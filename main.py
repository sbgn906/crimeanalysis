import streamlit as st
import pandas as pd
import plotly.express as px
from matplotlib import font_manager as fm
import os

# ✅ 한글 폰트 설정
font_path = "./fonts/NanumGothic.ttf"
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    plt_font = fm.FontProperties(fname=font_path).get_name()
    px.defaults.template = "plotly_white"
    px.defaults.font = plt_font
else:
    st.warning("⚠️ 폰트 파일이 누락되어 기본 글꼴로 대체됩니다.")

# ✅ 데이터 로딩
@st.cache_data
def load_data():
    df = pd.read_csv("경찰청_범죄 발생 지역별 통계_20231231.csv", encoding='cp949')  # 파일명은 사용자 파일명에 따라 수정
    return df

df = load_data()

# ✅ 전처리: 시/도 및 시/군/구 추출
df["시도"] = df["지역"].str.extract(r"(^[^ ]+)")
df["시군구"] = df["지역"].str.extract(r"(?:^[^ ]+ )?(.*)")

# ✅ 사이드바 필터
st.sidebar.title("📊 필터")
crime_main = st.sidebar.selectbox("범죄 대분류 선택", sorted(df["대분류"].unique()))
selected_province = st.sidebar.selectbox("지역 선택 (도/광역시)", ["전체"] + sorted(df["시도"].unique()))

# ✅ 필터링
filtered_df = df[df["대분류"] == crime_main]
if selected_province != "전체":
    filtered_df = filtered_df[filtered_df["시도"] == selected_province]

# ✅ 중분류별 발생 건수 그래프
sub_counts = filtered_df["중분류"].value_counts().reset_index()
sub_counts.columns = ["중분류", "건수"]

st.markdown(f"### ✅ '{crime_main}' 대분류 내 중분류별 발생 건수")
bar_fig = px.bar(
    sub_counts,
    x="건수",
    y="중분류",
    orientation="h",
    color="중분류",
    color_discrete_sequence=px.colors.qualitative.Set2,
    text="건수"
)
bar_fig.update_layout(showlegend=False)
st.plotly_chart(bar_fig, use_container_width=True)

# ✅ 지역별 비율 시각화 (상위 10개 + 기타)
region_counts = (
    filtered_df["지역"].value_counts()
    .reset_index()
    .rename(columns={"index": "지역", "지역": "건수"})
)

st.markdown("### 📍 선택한 지역의 발생 비율 (원형 차트)")

if len(region_counts) > 10:
    top10 = region_counts.iloc[:10]
    other_sum = region_counts.iloc[10:]["건수"].sum()
    pie_df = pd.concat([
        top10,
        pd.DataFrame([{"지역": "기타", "건수": other_sum}])
    ])
else:
    pie_df = region_counts

pie_fig = px.pie(
    pie_df,
    names="지역",
    values="건수",
    color_discrete_sequence=px.colors.qualitative.Set3,
    title=f"{crime_main} 지역별 발생 비율"
)
st.plotly_chart(pie_fig, use_container_width=True)

# ✅ 기타 클릭 시 나머지 지역 테이블 표시
if "기타" in pie_df["지역"].values:
    if st.checkbox("기타 지역 상세 보기"):
        st.markdown("#### 기타 지역 상세 정보")
        st.dataframe(region_counts.iloc[10:].reset_index(drop=True))

# ✅ 부가 설명
with st.expander("ℹ️ 그래프 해설 및 참고사항"):
    st.markdown(
        """
        - 상단의 그래프는 대분류 범죄 안의 중분류별 발생 건수를 보여줍니다.
        - 원형 차트는 상위 10개 지역 비율만을 시각화하며, 나머지는 '기타'로 묶였습니다.
        - '기타 지역 상세 보기'를 클릭하면 나머지 지역 정보를 표로 확인할 수 있습니다.
        - 선택한 지역이 좁을수록 보다 상세한 지역 분석이 가능합니다.
        """
    )
