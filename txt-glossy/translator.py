import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class GlossTranslator:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        llm_provider = os.getenv("LLM_PROVIDER", "google").lower()
        
        if llm_provider == "ollama":
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.llm = ChatOllama(model=ollama_model, base_url=ollama_base_url, temperature=0.2)
        else:
            self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2)

        # System prompt for Text -> Glossy
        self.text_to_gloss_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in American Sign Language (ASL).
Your task is to translate standard English text into ASL glosses.
Follow these strict ASL glossing conventions:
1. Glosses MUST be in UPPERCASE.
2. Grammar: Use Subject-Verb-Object (SVO) for simple sentences. Place time signs at the beginning. Place question words (WHAT, WHERE, WHY) at the very end. Do not use prepositions (in, on, at) unless necessary.
3. Omissions: REMOVE English 'to be' verbs (am, is, are, was, were), articles (a, an, the), and auxiliary verbs (do, does, did).
4. Morphology: Remove inflections (plural -s, past tense -ed). Use base forms (e.g. "dogs" -> "DOG").
5. Pronouns: Translate "I/me" as PRO-1. "you" as YOU. "my" as MY. "he/she" as HE/SHE.
6. Fingerspelling: Spell proper nouns with hyphens (e.g., M-A-R-Y, A-L-E-X).
7. Output: Provide ONLY the gloss sequence. Retain periods (.) and question marks (?).

Examples:
Input: "My name is Mary."
Output: PRO-1 NAME M-A-R-Y.

Input: "She is my sister."
Output: SHE MY SISTER.

Input: "What time is the meeting?"
Output: MEETING TIME WHAT?

Input: "I have two dogs."
Output: PRO-1 HAVE DOG TWO.

Input: "I live in California."
Output: PRO-1 CALIFORNIA LIVE.

Input: "The children are playing in the park."
Output: CHILDREN PARK PLAY.

Input: "Next week I will visit my grandmother."
Output: NEXT-WEEK GRANDMOTHER VISIT PRO-1.

Input: "Why are you late?"
Output: YOU LATE WHY?

Input: "I don't want that."
Output: THAT PRO-1 WANT NOT.

Input: "As for my car, it is old."
Output: MY CAR, OLD.
"""),
            ("user", "Translate the following English text to ASL glosses: {text}")
        ])

        # System prompt for Glossy -> Text
        self.gloss_to_text_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert translator from American Sign Language (ASL) glosses into natural spoken/written English.
Your task is to take a sequence of ASL glosses (usually written in uppercase) and produce a natural-sounding, grammatically correct English translation.
Infer the correct tense, person, and context from the given glosses.
Provide ONLY the final English translation, without any additional explanations, conversational filler, or text.

Examples:
Input: "NEXT-WEEK GRANDMOTHER VISIT PRO-1."
Output: Next week I will visit my grandmother.

Input: "YOU LATE WHY?"
Output: Why are you late?

Input: "PRO-1 NAME J-O-H-N PRO-1 HAVE CAT THREE."
Output: My name is John and I have three cats.

Input: "THAT PRO-1 WANT NOT."
Output: I don't want that.

Input: "MY CAR, OLD."
Output: As for my car, it is old.
"""),
            ("user", "Translate the following ASL glosses to natural English text: {gloss}")
        ])

        self.text_to_gloss_chain = self.text_to_gloss_prompt | self.llm
        self.gloss_to_text_chain = self.gloss_to_text_prompt | self.llm

    def text_to_gloss(self, text: str) -> str:
        """Translates natural English text to ASL glosses."""
        response = self.text_to_gloss_chain.invoke({"text": text})
        content = response.content.strip()
        if content.startswith("Output:"):
            content = content[7:].strip()
        return content

    def gloss_to_text(self, gloss: str) -> str:
        """Translates ASL glosses to natural English text."""
        response = self.gloss_to_text_chain.invoke({"gloss": gloss})
        content = response.content.strip()
        if content.startswith("Output:"):
            content = content[7:].strip()
        return content

if __name__ == "__main__":
    # A simple test block
    translator = GlossTranslator()
    
    text_input = "My name is John and I like programming."
    print(f"Text: {text_input}")
    gloss_output = translator.text_to_gloss(text_input)
    print(f"Gloss: {gloss_output}")
    
    print("-" * 20)
    
    gloss_input = "ME NAME JOHN ME LIKE PROGRAMMING"
    print(f"Gloss: {gloss_input}")
    text_output = translator.gloss_to_text(gloss_input)
    print(f"Text: {text_output}")
