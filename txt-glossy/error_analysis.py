import json
import os
import sacrebleu
from rouge_score import rouge_scorer
from translator import GlossTranslator

def run_analysis():
    translator = GlossTranslator()
    data_path = os.path.join(os.path.dirname(__file__), "benchmark_data_full.json")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = [item["text"] for item in data]
    glosses = [item["gloss"] for item in data]
    
    scorer = rouge_scorer.RougeScorer(['rouge1'], use_stemmer=True)
    results = []

    for t, g in zip(texts, glosses):
        try:
            pred = translator.text_to_gloss(t)
            rouge1 = scorer.score(g, pred)['rouge1'].fmeasure
            results.append({
                "text": t,
                "expected": g,
                "predicted": pred,
                "rouge1": round(rouge1, 3)
            })
        except Exception as e:
            print(f"Error on {t}: {e}")
            
    results.sort(key=lambda x: x["rouge1"])
    
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Analysis saved to analysis_results.json")

if __name__ == "__main__":
    run_analysis()
