import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()


# --- Pydantic Schemas ---
class MCQItem(BaseModel):
  question: str = Field(description="The multiple-choice question.")
  options: list[str] = Field(description="Exactly 4 answer choices.")
  correct_answer: str = Field(
      description="The exact text of the correct option from the options list."
  )
  explanation: str = Field(
      description="Brief explanation of why this answer is correct."
  )


class FlashcardItem(BaseModel):
  term: str = Field(description="Key concept, formula, or term.")
  definition: str = Field(
      description="Clear, concise definition or explanation."
  )


class StudyMaterial(BaseModel):
  title: str = Field(description="A concise title for the study notes.")
  summary_points: list[str] = Field(
      description="5 to 7 key bullet points summarizing the core ideas."
  )
  flashcards: list[FlashcardItem] = Field(
      description="6 key term-definition flashcards."
  )
  quiz: list[MCQItem] = Field(
      description="Multiple-choice questions based strictly on the notes."
  )


# --- Resilient AI Generation Function ---
def generate_study_kit(
    notes_text: str, num_questions: int = 5, difficulty: str = "Medium"
) -> StudyMaterial:
  api_key = os.getenv("GEMINI_API_KEY")
  if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Please set it in your .env file."
    )

  client = genai.Client(api_key=api_key)

  prompt = f"""
    You are an expert academic tutor. Analyze the following student notes and generate a complete study kit.
    - Difficulty level for quiz questions: {difficulty}
    - Number of MCQ questions to generate: {num_questions}
    - Base all questions, options, and flashcards strictly on the provided text.

    STUDY NOTES:
    {notes_text[:25000]}
    """

  # Try primary model, then retry/fallback if 503 high demand occurs
  models_to_try = [
      "gemini-3.8-flash",
      "gemini-3.8-flash",
      "gemini-3.8-flash-lite",
  ]
  last_error = None

  for attempt, model_name in enumerate(models_to_try):
    try:
      response = client.models.generate_content(
          model=model_name,
          contents=prompt,
          config=types.GenerateContentConfig(
              response_mime_type="application/json",
              response_schema=StudyMaterial,
              temperature=0.3,
          ),
      )
      return response.parsed
    except Exception as e:
      last_error = e
      if "503" in str(e) or "UNAVAILABLE" in str(e):
        time.sleep(2 * (attempt + 1))  # Wait 2s, then 4s before retrying
        continue
      raise e  # Raise immediately for non-temporary errors (like invalid API key)

  raise RuntimeError(
      f"All model attempts busy due to server demand. Please try again: {last_error}"
  )