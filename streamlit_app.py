# app.py
# -----------------------------------------------
# 마케터용 자동 제안서 도우미 (PPT 내보내기 없음)
# -----------------------------------------------
import streamlit as st
from openai import OpenAI
from datetime import datetime

# ------------------ 페이지 설정 ------------------
st.set_page_config(
    page_title="마케터용 자동 제안서 도우미",
    page_icon="📊",
    layout="wide"
)

# ------------------ 사이드바: 설정 ------------------
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("🔐 OpenAI API Key", type="password", placeholder="sk-...")

    st.subheader("🎯 캠페인 기본 정보")
    brand = st.text_input("브랜드명", value="데모브랜드")
    objective = st.multiselect(
        "목표",
        ["인지도", "트래픽", "회원가입/리드", "구매전환", "재구매/CRM"],
        default=["구매전환"]
    )
    industry = st.selectbox(
        "업종",
        ["뷰티/스킨케어", "패션/의류", "F&B/외식", "헬스/의료", "교육/학원", "앱/서비스", "클리닉/병원", "전자/리빙"],
        index=0
    )
    age_range = st.selectbox("핵심 연령대", ["10대", "20대", "30대", "40대", "50대 이상"], index=1)
    gender = st.selectbox("성별", ["전체", "여성", "남성"], index=0)

    st.subheader("🧩 톤 & 매체 프리셋")
    tone = st.selectbox(
        "카피 톤",
        ["데이터 중심/전문적", "감성/스토리텔링", "프리미엄/럭셔리", "경쾌/발랄", "신뢰/권위"],
        index=0
    )
    channels = st.multiselect(
        "매체(프리셋)",
        ["Meta(Instagram/Facebook)", "Naver(검색/GFA)", "Google(Search/Display)", "TikTok", "Kakao Moment"],
        default=["Meta(Instagram/Facebook)", "Naver(검색/GFA)", "Google(Search/Display)"]
    )
    cta_style = st.selectbox("CTA 스타일", ["즉시 행동 유도", "부드러운 제안", "한정/희소성"], index=0)

    st.divider()
    model = st.selectbox("🤖 모델", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    temperature = st.slider("창의성(temperature)", 0.0, 1.5, 0.7, 0.1)
    max_tokens = st.slider("Max tokens", 512, 4096, 1800, 64)

# ------------------ 세션 상태 ------------------
if "outputs" not in st.session_state:
    st.session_state.outputs = None

# ------------------ 프롬프트 빌더 ------------------
def build_prompt(role, brand, industry, age_range, gender, tone, channels, objective, cta_style):
    base = f"""
너는 상업용 마케팅 제안서를 작성하는 시니어 플래너다. 표/불릿 중심으로 간결하게 한국어로 출력하라.

[브랜드] {brand}
[업종] {industry}
[핵심 타깃] {age_range} / {gender}
[목표] {", ".join(objective)}
[톤] {tone}
[매체] {", ".join(channels)}
[CTA 스타일] {cta_style}
"""
    if role == "stp":
        task = """
STP를 작성하라.
- Segmentation: 3~5개
- Targeting: 우선순위 타깃 1~2개 + 선정 근거
- Positioning: 1문장 + USP/RTB 3개
- 마지막에 요약 표 1개
"""
    elif role == "persona":
        task = """
페르소나 1~2명을 작성하라.
- 이름/나이/직업/라이프스타일
- Pain points, Needs, Trigger
- 구매 여정별(인지→관심→고려→전환→재방문) 메시지 포인트
- 마지막에 요약 표 1개
"""
    elif role == "copy":
        task = """
카피/슬로건을 작성하라.
- 인스타그램 광고 주 카피 3개(헤드라인+서브라인+CTA)
- 20대 여성 타깃 슬로건 3개(업종/톤 반영)
- 리마케팅용 짧은 헤드라인 5개(12자 내외)
- 해시태그 10개
"""
    else:  # media
        task = """
매체 전략을 작성하라.
- 채널별 역할(퍼널 상/중/하)
- 초기 4주 예산 배분(%) 가이드
- 캠페인 구조 예시(캠페인/광고세트/소재)
- KPI 및 이벤트(CTR, CPC, CPA/ROAS 등)
- 4주 실행 타임라인(주차별 액션)
- 마지막에 요약 표 1개
"""
    return base + "\n" + task

# ------------------ 생성기 ------------------
def generate_all(client, model, temperature, max_tokens, **kwargs):
    system_msg = "상업용 마케팅 제안서 보조 도구. 불필요한 수사는 배제하고 핵심만 표/불릿으로 제시한다."
    outputs = {}
    for role in ["stp", "persona", "copy", "media"]:
        prompt = build_prompt(role, **kwargs)
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        outputs[role] = resp.choices[0].message.content.strip()
    return outputs

# ------------------ Markdown 내보내기 ------------------
def to_markdown(brand, industry, objective, outputs):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = []
    md.append(f"# {brand} 마케팅 제안서\n")
    md.append(f"- 업종: **{industry}**  \n- 목표: **{', '.join(objective)}**  \n- 생성시각: {now}\n")
    md.append("## 1) STP\n" + outputs["stp"] + "\n")
    md.append("## 2) 페르소나\n" + outputs["persona"] + "\n")
    md.append("## 3) 광고 카피 & 슬로건\n" + outputs["copy"] + "\n")
    md.append("## 4) 매체 전략 & KPI\n" + outputs["media"] + "\n")
    return "\n".join(md)

# ------------------ 메인 UI ------------------
st.title("📊 마케터용 자동 제안서 도우미")
st.caption("업종·타깃·톤·매체 프리셋을 고르면 STP/페르소나/카피/매체전략을 한 번에 생성합니다. (PPT 내보내기 없음)")

col_left, col_right = st.columns([1, 1])
with col_left:
    btn_disabled = not api_key
    generate_btn = st.button("🚀 제안 생성하기", use_container_width=True, disabled=btn_disabled)
with col_right:
    if st.session_state.outputs:
        md_text = to_markdown(brand, industry, objective, st.session_state.outputs)
        st.download_button(
            label="📝 Markdown로 저장(.md)",
            data=md_text.encode("utf-8"),
            file_name=f"{brand}_proposal.md",
            mime="text/markdown",
            use_container_width=True
        )
    else:
        st.button("📝 Markdown로 저장(.md)", disabled=True, use_container_width=True)

st.divider()

# ------------------ 생성 실행 ------------------
if generate_btn:
    client = OpenAI(api_key=api_key)
    kwargs = dict(
        brand=brand,
        industry=industry,
        age_range=age_range,
        gender=gender,
        tone=tone,
        channels=channels,
        objective=objective,
        cta_style=cta_style
    )
    st.session_state.outputs = generate_all(
        client,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
    st.success("생성이 완료되었어. 아래 탭에서 확인해봐!")

# ------------------ 결과 미리보기 ------------------
if st.session_state.outputs:
    tabs = st.tabs(["STP", "페르소나", "카피 & 슬로건", "매체 전략/KPI"])
    st.markdown("각 탭의 내용을 복사하거나 상단에서 Markdown로 저장해 활용해줘.")
    with tabs[0]:
        st.code(st.session_state.outputs["stp"], language="markdown")
    with tabs[1]:
        st.code(st.session_state.outputs["persona"], language="markdown")
    with tabs[2]:
        st.code(st.session_state.outputs["copy"], language="markdown")
    with tabs[3]:
        st.code(st.session_state.outputs["media"], language="markdown")
else:
    st.info("좌측에서 설정을 입력하고 **제안 생성하기**를 눌러 시작하자.", icon="✨")

