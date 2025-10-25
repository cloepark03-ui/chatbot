import streamlit as st
from openai import OpenAI

# ---------- 기본 페이지 설정 ----------
st.set_page_config(page_title="나의 첫번째 챗봇", page_icon="💬", layout="centered")

# ---------- 커스텀 스타일 ----------
st.markdown("""
<style>
/* 전체 폰트/라인 높이 살짝 정리 */
html, body, [class*="css"]  { font-family: -apple-system, Pretendard, 'Noto Sans KR', Inter, Segoe UI, Roboto, sans-serif; line-height: 1.5; }

/* 상단 제목 여백 줄이기 */
.block-container { padding-top: 2rem; }

/* 말풍선 스타일 */
.chat-bubble { padding: 0.9rem 1rem; border-radius: 14px; margin: 0.25rem 0 0.75rem 0; }
.assistant { background: rgba(240,242,246,0.9); border: 1px solid rgba(0,0,0,0.06); }
.user { background: #2563eb10; border: 1px solid rgba(37,99,235,0.25); }

/* 말풍선 폭 제한 + 가독 폭 */
.chat-bubble p { margin: 0; }

/* 입력창 상단 살짝 여백 */
.stChatInput { margin-top: 0.75rem; }

/* info/empty 카드 조금 더 미니멀하게 */
.stAlert { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# ---------- 사이드바 ----------
with st.sidebar:
    st.header("⚙️ 설정")
    st.caption("필요한 옵션을 선택하세요.")
    openai_api_key = st.text_input("🔐 OpenAI API Key", type="password", placeholder="sk-...")

    model = st.selectbox(
        "🤖 모델 선택",
        options=["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o"],
        index=0,
        help="원하는 모델을 선택하세요."
    )

    temperature = st.slider("🎛️ 창의성(temperature)", 0.0, 1.5, 0.7, 0.1)

    sys_prompt = st.text_area(
        "🧭 시스템 프롬프트(선택)",
        value="너는 친절하고 간결하게 답변하는 한국어 비서야. 핵심만 명확히 말해.",
        help="모델의 기본 말투/역할을 정의합니다."
    )

    col_a, col_b = st.columns(2)
    with col_a:
        clear_clicked = st.button("🧹 대화 초기화", use_container_width=True)
    with col_b:
        st.markdown(
            "[API 키 발급](https://platform.openai.com/account/api-keys)",
            help="OpenAI 콘솔에서 API 키를 발급받을 수 있습니다."
        )

# ---------- 타이틀/설명 ----------
st.title("💬 나의 첫번째 챗봇")
st.write(
    "이 앱은 OpenAI 모델을 활용한 간단한 챗봇입니다. "
    "API 키가 필요하며, 위 사이드바에서 모델과 옵션을 조절할 수 있어요. "
    "직접 만들어보고 싶다면 "
    "[튜토리얼](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)"
    "을 참고하세요."
)

# ---------- 세션 스테이트 ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if clear_clicked:
    st.session_state.messages = []

# ---------- API 키 안내 ----------
if not openai_api_key:
    st.info("좌측 사이드바에 OpenAI API 키를 입력하면 시작할 수 있어요.", icon="🗝️")
    st.stop()

# ---------- OpenAI 클라이언트 ----------
client = OpenAI(api_key=openai_api_key)

# ---------- 대화 시작 전 시스템 메시지 주입 ----------
#   - 사용자가 첫 입력하기 전 시스템 메시지를 1회만 삽입
if len(st.session_state.messages) == 0 and sys_prompt.strip():
    st.session_state.messages.append({"role": "system", "content": sys_prompt.strip()})

# ---------- 기존 메시지 렌더링 ----------
for message in st.session_state.messages:
    if message["role"] == "system":
        # 시스템 메시지는 UI에 직접 노출하지 않고 내부적으로만 유지
        continue
    role = message["role"]
    avatar = "🤖" if role == "assistant" else "🧑‍💻"
    bubble_class = "assistant" if role == "assistant" else "user"
    with st.chat_message(role, avatar=avatar):
        st.markdown(f'<div class="chat-bubble {bubble_class}">{message["content"]}</div>', unsafe_allow_html=True)

# ---------- 입력창 ----------
prompt = st.chat_input("무엇을 도와드릴까요?")
if prompt:
    # 사용자 메시지 저장/표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(f'<div class="chat-bubble user">{prompt}</div>', unsafe_allow_html=True)

    # 스트리밍 응답
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        temperature=temperature,
        stream=True,
    )

    with st.chat_message("assistant", avatar="🤖"):
        response_text = st.write_stream(stream)

    # 대화에 모델 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": response_text})
