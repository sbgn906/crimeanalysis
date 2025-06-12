import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.ensemble import IsolationForest  # ✅ 추가

st.set_page_config(layout="wide")
st.title("📊 지역별 범죄 통계 시각화 대시보드")

# -----------------------
# 데이터 로딩 및 전처리
# -----------------------
@st.cache_data
def load_data():
    df = pd.read_csv("경찰청_범죄 발생 지역별 통계_20231231.csv", encoding='cp949')
    df = df.melt(id_vars=['범죄대분류', '범죄중분류'], var_name='지역', value_name='발생건수')
    df = df.dropna(subset=['발생건수'])
    df['발생건수'] = pd.to_numeric(df['발생건수'], errors='coerce').fillna(0).astype(int)

    def extract_do(region):
        for prefix in ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
                       "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]:
            if region.startswith(prefix):
                return prefix
        return "기타"
    
    df['도'] = df['지역'].apply(extract_do)
    return df

df = load_data()

# -----------------------
# 사이드바 필터
# -----------------------
with st.sidebar:
    st.header("🔍 필터")

    selected_main = st.selectbox("대분류 선택", sorted(df['범죄대분류'].unique()))

    all_do = ['전체'] + sorted(df['도'].unique())
    selected_do = st.selectbox("광역단체(도/광역시) 선택", all_do)

    # ✅ 이상치 탐지 옵션
    detect_outliers = st.checkbox("⚠️ 이상치 탐지 활성화", value=False)

    st.markdown("**세부 지역 선택**")

    toggle_all = st.checkbox("모든 지역 선택", value=True, key="toggle_all")

    if selected_do == '전체':
        selected_dos = []
        for do_name in sorted(df['도'].unique()):
            if st.checkbox(f"{do_name}", key=f"do_{do_name}", value=toggle_all):
                selected_dos.append(do_name)
        selected_subregions = df[df['도'].isin(selected_dos)]['지역'].unique().tolist()
    else:
        all_regions = sorted(df[df['도'] == selected_do]['지역'].unique())
        selected_subregions = []
        for region in all_regions:
            if st.checkbox(f"{region}", key=f"region_{region}", value=toggle_all):
                selected_subregions.append(region)

    st.markdown("---")
    st.markdown(f"🔎 **선택된 지역 수**: `{len(selected_subregions)}개`")


# -----------------------
# 필터 적용
# -----------------------
filtered_df = df[
    (df['범죄대분류'] == selected_main) &
    (df['지역'].isin(selected_subregions))
]

# -----------------------
# 중분류별 막대 그래프
# -----------------------
middle_summary = filtered_df.groupby('범죄중분류')['발생건수'].sum().sort_values(ascending=False)

st.subheader(f"✅ '{selected_main}' 대분류 내 중분류별 발생 건수")

if middle_summary.empty:
    st.warning("해당 대분류에 대한 중분류 데이터가 선택한 지역에서 존재하지 않습니다.")
elif len(middle_summary) == 1:
    label = middle_summary.index[0]
    value = middle_summary.iloc[0]
    st.info(f"🔹 중분류: **{label}** / 발생건수: **{value:,}건**")
else:
    fig = px.bar(
        middle_summary.reset_index(),
        x='발생건수',
        y='범죄중분류',
        orientation='h',
        color='범죄중분류',
        title=f"{selected_main} 중분류별 발생건수",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

# -----------------------
# 🚨 이상치 탐지
# -----------------------
if detect_outliers:
    if filtered_df.empty:
        st.warning("⚠️ 선택된 지역에 해당하는 데이터가 없습니다. 이상치 탐지를 실행할 수 없습니다.")
    else:
        st.subheader("🚨 이상치 탐지 결과 (중분류/지역 기준)")

        pivot = filtered_df.pivot_table(index='지역', columns='범죄중분류', values='발생건수', aggfunc='sum', fill_value=0)

        if len(pivot) < 5:
            st.info("ℹ️ 이상치 탐지를 위해선 최소 5개 이상의 지역 데이터가 필요합니다.")
        else:
            model = IsolationForest(contamination=0.1, random_state=42)
            pivot['이상치'] = model.fit_predict(pivot)

            outliers = pivot[pivot['이상치'] == -1].drop(columns='이상치')

            if outliers.empty:
                st.success("✅ 이상치로 탐지된 지역이 없습니다. 전체 데이터를 참고하세요.")
                st.dataframe(pivot.drop(columns='이상치').style.background_gradient(cmap='Greens'))
            else:
                st.warning(f"🚨 이상치로 탐지된 지역입니다. (총 {len(outliers)}곳)")
                st.dataframe(outliers.style.highlight_max(axis=1, color='salmon'))


# -----------------------
# 지역별 원형 차트
# -----------------------
st.subheader("📍 선택한 광역단체/지역의 상위 10개지 발생 비율")

if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 지역 데이터가 없습니다.")
else:
    if selected_do == '전체' or len(set(filtered_df['도'])) > 1:
        region_summary = filtered_df.groupby('도')['발생건수'].sum().reset_index()
        pie_title = f"{selected_main} 도별 발생 비율"
        name_col = '도'
    else:
        region_summary = filtered_df.groupby('지역')['발생건수'].sum().reset_index()
        pie_title = f"{selected_main} 지역(시/군/구)별 발생 비율"
        name_col = '지역'

    region_summary = region_summary.sort_values('발생건수', ascending=False).reset_index(drop=True)
    top_n = 10
    if len(region_summary) > top_n:
        top_regions = region_summary.iloc[:top_n]
        other_regions = region_summary.iloc[top_n:]
        other_sum = other_regions['발생건수'].sum()

        pie_data = pd.concat([
            top_regions,
            pd.DataFrame({name_col: ['기타'], '발생건수': [other_sum]})
        ], ignore_index=True)
    else:
        pie_data = region_summary.copy()

    pie_fig = px.pie(
        pie_data,
        values='발생건수',
        names=name_col,
        title=pie_title,
        height=600
    )
    st.plotly_chart(pie_fig, use_container_width=True)

    if '기타' in pie_data[name_col].values and len(region_summary) > top_n:
        with st.expander("📋 기타 항목 세부 정보 보기"):
            st.write(other_regions.rename(columns={name_col: '지역명'}).reset_index(drop=True))
