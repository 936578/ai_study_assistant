from ai_engine import generate_study_kit
from pdf_utils import extract_text_from_pdf
import streamlit as st

st.set_page_config(
    page_title="AI Notes-to-Quiz Generator", page_icon="🎓", layout="wide"
)

# --- Session State Initialization ---
if "study_kit" not in st.session_state:
  st.session_state.study_kit = None
if "quiz_submitted" not in st.session_state:
  st.session_state.quiz_submitted = False

# --- Header ---
st.title("🎓 AI Notes-to-Quiz & Flashcard Generator")
st.caption(
    "Upload lecture PDFs or paste study notes to generate instant summaries,"
    " flashcards, and self-graded quizzes."
)

# --- Sidebar Controls ---
with st.sidebar:
  st.header("⚙️ Study Settings")
  input_mode = st.radio("Input Source:", ["Upload PDF", "Paste Text"])
  num_questions = st.slider(
      "Number of Quiz Questions", min_value=3, max_value=10, value=5
  )
  difficulty = st.selectbox("Quiz Difficulty", ["Easy", "Medium", "Hard"])

  st.divider()
  st.markdown(
      "**Tech Stack:** Python • Streamlit • Google Gemini API • Pydantic"
  )

# --- Input Section ---
notes_content = ""
if input_mode == "Upload PDF":
  uploaded_pdf = st.file_uploader("Upload your lecture notes (PDF)", type=["pdf"])
  if uploaded_pdf:
    with st.spinner("Extracting text from PDF..."):
      notes_content = extract_text_from_pdf(uploaded_pdf)
    st.success(f"Extracted {len(notes_content):,} characters from PDF.")
else:
  notes_content = st.text_area(
      "Paste your notes or textbook paragraph here:", height=200
  )

if st.button("✨ Generate Study Kit", type="primary", use_container_width=True):
  if len(notes_content.strip()) < 100:
    st.warning("Please provide at least 100 characters of study material.")
  else:
    with st.spinner("AI is analyzing your notes and crafting your quiz..."):
      try:
        st.session_state.study_kit = generate_study_kit(
            notes_text=notes_content,
            num_questions=num_questions,
            difficulty=difficulty,
        )
        st.session_state.quiz_submitted = False
      except Exception as e:
        st.error(f"Error generating study kit: {e}")

# --- Display Generated Study Kit ---
if st.session_state.study_kit:
  kit = st.session_state.study_kit
  st.divider()
  st.subheader(f"📘 {kit.title}")

  tab_summary, tab_cards, tab_quiz = st.tabs(
      ["📝 Key Summary", "🗂️ Flashcards", "🧠 Practice Quiz"]
  )

  # TAB 1: Summary
  with tab_summary:
    st.markdown("### Core Takeaways")
    for point in kit.summary_points:
      st.markdown(f"- {point}")

  # TAB 2: Interactive Flashcards
  with tab_cards:
    st.markdown("### Click any card to reveal the definition")
    cols = st.columns(2)
    for idx, card in enumerate(kit.flashcards):
      with cols[idx % 2]:
        with st.expander(f"📌 **{card.term}**"):
          st.write(card.definition)

  # TAB 3: Auto-Graded MCQ Quiz
  with tab_quiz:
    with st.form("quiz_form"):
      user_answers = {}
      for i, q in enumerate(kit.quiz):
        st.markdown(f"**Q{i+1}. {q.question}**")
        user_answers[i] = st.radio(
            label=f"Select answer for Q{i+1}:",
            options=q.options,
            key=f"q_{i}",
            index=None,
            label_visibility="collapsed",
        )
        st.write("")

      submitted = st.form_submit_button(
          "Submit & Grade Quiz", type="primary"
      )
      if submitted:
        st.session_state.quiz_submitted = True

    if st.session_state.quiz_submitted:
      score = 0
      st.divider()
      st.markdown("### 📊 Quiz Results")

      for i, q in enumerate(kit.quiz):
        chosen = user_answers.get(i)
        if chosen == q.correct_answer:
          score += 1
          st.success(f"**Q{i+1}: Correct!** ({chosen})")
        else:
          st.error(
              f"**Q{i+1}: Incorrect.** You chose: `{chosen}` | Correct:"
              f" `{q.correct_answer}`"
          )
        st.info(f"💡 **Explanation:** {q.explanation}")

      percentage = (score / len(kit.quiz)) * 100
      st.metric(
          label="Final Score",
          value=f"{score} / {len(kit.quiz)}",
          delta=f"{percentage:.0f}%",
      )