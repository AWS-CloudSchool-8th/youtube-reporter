import re
from collections import Counter
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RougeService:
    def __init__(self):
        pass
    
    def _tokenize(self, text: str) -> List[str]:
        text = re.sub( ' ', text.lower())
        tokens = text.split()
        return [token for token in tokens if len(token) > 1]
    
    def _get_ngrams(self, tokens: List[str], n: int) -> List[tuple]:
        if len(tokens) < n:
            return []
        return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
    
    def _calculate_rouge_n(self, reference_tokens: List[str], summary_tokens: List[str], n: int) -> Dict[str, float]:
        ref_ngrams = self._get_ngrams(reference_tokens, n)
        sum_ngrams = self._get_ngrams(summary_tokens, n)
        
        if not ref_ngrams or not sum_ngrams:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        ref_counter = Counter(ref_ngrams)
        sum_counter = Counter(sum_ngrams)
        
        overlap = sum((ref_counter & sum_counter).values())
        
        precision = overlap / len(sum_ngrams) if sum_ngrams else 0.0
        recall = overlap / len(ref_ngrams) if ref_ngrams else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4)
        }
    
    def _calculate_rouge_l(self, reference_tokens: List[str], summary_tokens: List[str]) -> Dict[str, float]:
        def lcs_length(x, y):
            m, n = len(x), len(y)
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if x[i-1] == y[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            
            return dp[m][n]
        
        if not reference_tokens or not summary_tokens:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        lcs_len = lcs_length(reference_tokens, summary_tokens)
        
        precision = lcs_len / len(summary_tokens) if summary_tokens else 0.0
        recall = lcs_len / len(reference_tokens) if reference_tokens else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4)
        }
    
    def calculate_rouge_scores(self, reference_text: str, summary_text: str) -> Dict[str, Any]:
        try:
            ref_tokens = self._tokenize(reference_text)
            sum_tokens = self._tokenize(summary_text)
            
            logger.info(f"Reference tokens count: {len(ref_tokens)}")
            logger.info(f"Summary tokens count: {len(sum_tokens)}")
            
            rouge_1 = self._calculate_rouge_n(ref_tokens, sum_tokens, 1)
            rouge_2 = self._calculate_rouge_n(ref_tokens, sum_tokens, 2)
            rouge_l = self._calculate_rouge_l(ref_tokens, sum_tokens)
            
            scores = {
                "ROUGE-1": rouge_1,
                "ROUGE-2": rouge_2,
                "ROUGE-L": rouge_l,
                "metadata": {
                    "reference_length": len(ref_tokens),
                    "summary_length": len(sum_tokens),
                    "compression_ratio": round(len(sum_tokens) / len(ref_tokens), 4) if ref_tokens else 0.0
                }
            }
            
            # 콘솔에 출력
            print("\n" + "="*50)
            print("?? ROUGE Result")
            print("="*50)
            print(f"original length: {len(ref_tokens)} token")
            print(f"summary length: {len(sum_tokens)} token")
            print(f"compression rate: {scores['metadata']['compression_ratio']:.2%}")
            print("-"*50)
            print(f"?? ROUGE-1 (word override)")
            print(f"   Precision: {rouge_1['precision']:.4f}")
            print(f"   Recall:    {rouge_1['recall']:.4f}")
            print(f"   F1-Score:  {rouge_1['f1']:.4f}")
            print(f"?? ROUGE-2 (2-gram override)")
            print(f"   Precision: {rouge_2['precision']:.4f}")
            print(f"   Recall:    {rouge_2['recall']:.4f}")
            print(f"   F1-Score:  {rouge_2['f1']:.4f}")
            print(f"?? ROUGE-L (maximum common sub)")
            print(f"   Precision: {rouge_l['precision']:.4f}")
            print(f"   Recall:    {rouge_l['recall']:.4f}")
            print(f"   F1-Score:  {rouge_l['f1']:.4f}")
            print("="*50)
            
            return scores
            
        except Exception as e:
            logger.error(f"ROUGE error: {e}")
            return {
                "ROUGE-1": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
                "ROUGE-2": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
                "ROUGE-L": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
                "error": str(e)
            }

# 싱글톤 인스턴스
rouge_service = RougeService()