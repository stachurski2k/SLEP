import json
import os
import sacrebleu
from rouge_score import rouge_scorer
from translator import GlossTranslator

def run_benchmark(translator: GlossTranslator):
    data_path = os.path.join(os.path.dirname(__file__), "benchmark_data_full.json")
    if not os.path.exists(data_path):
        return {"error": "Benchmark data not found."}
        
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if not data:
        return {"error": "Benchmark data is empty."}

    texts = [item["text"] for item in data]
    glosses = [item["gloss"] for item in data]
    
    # Run text to gloss
    pred_glosses = []
    for t in texts:
        try:
            pred_glosses.append(translator.text_to_gloss(t))
        except Exception as e:
            pred_glosses.append(f"ERROR: {e}")
            
    # Run gloss to text
    pred_texts = []
    for g in glosses:
        try:
            pred_texts.append(translator.gloss_to_text(g))
        except Exception as e:
            pred_texts.append(f"ERROR: {e}")
            
    # Calculate metrics
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    
    # Metrics for Text -> Gloss
    bleu_t2g = sacrebleu.corpus_bleu(pred_glosses, [[g for g in glosses]]).score
    rouge1_t2g = sum(scorer.score(ref, pred)['rouge1'].fmeasure for ref, pred in zip(glosses, pred_glosses)) / len(glosses)
    
    # Metrics for Gloss -> Text
    bleu_g2t = sacrebleu.corpus_bleu(pred_texts, [[t for t in texts]]).score
    rouge1_g2t = sum(scorer.score(ref, pred)['rouge1'].fmeasure for ref, pred in zip(texts, pred_texts)) / len(texts)
    
    return {
        "text_to_gloss": {
            "bleu": round(bleu_t2g, 2),
            "rouge1": round(rouge1_t2g * 100, 2)
        },
        "gloss_to_text": {
            "bleu": round(bleu_g2t, 2),
            "rouge1": round(rouge1_g2t * 100, 2)
        },
        "sample_count": len(data)
    }

if __name__ == "__main__":
    t = GlossTranslator()
    results = run_benchmark(t)
    print(json.dumps(results, indent=2))
