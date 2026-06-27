import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class GlossTranslator:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2)

        # System prompt for Text -> Glossy
        self.text_to_gloss_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in American Sign Language (ASL).
Your task is to translate standard English text into ASL glosses.
Follow the standard ASL glossing conventions:
1. Glosses should be in UPPERCASE.
2. ASL has its own grammar (often TIME-TOPIC-COMMENT or OSV/SVO), different from spoken English.
3. Skip grammatical words that don't exist in ASL (e.g., articles like "a", "an", "the", forms of the "to be" verb like "is", "are", "am").
4. Do not use inflection on glosses (no -ed, -ing, -s). Use the base form of the word.
5. Provide ONLY the final gloss sequence, without any additional explanations or text.
"""),
            ("user", "Translate the following English text to ASL glosses: {text}")
        ])

        # System prompt for Glossy -> Text
        self.gloss_to_text_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert translator from American Sign Language (ASL) glosses into natural spoken/written English.
Your task is to take a sequence of ASL glosses (usually written in uppercase) and produce a natural-sounding, grammatically correct English translation.
Infer the correct tense, person, and context from the given glosses.
Provide ONLY the final English translation, without any additional explanations or text.
"""),
            ("user", "Translate the following ASL glosses to natural English text: {gloss}")
        ])

        self.text_to_gloss_chain = self.text_to_gloss_prompt | self.llm
        self.gloss_to_text_chain = self.gloss_to_text_prompt | self.llm

    def text_to_gloss(self, text: str) -> str:
        """Translates natural English text to ASL glosses."""
        response = self.text_to_gloss_chain.invoke({"text": text})
        return response.content.strip()

    def gloss_to_text(self, gloss: str) -> str:
        """Translates ASL glosses to natural English text."""
        response = self.gloss_to_text_chain.invoke({"gloss": gloss})
        return response.content.strip()

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
