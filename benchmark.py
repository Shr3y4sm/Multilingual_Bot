"""
Benchmark Script for Multilingual Bot
Compares translation accuracy (BLEU), ASR accuracy (WER), and response time
against Google Translate and DeepL
"""

import time
import json
import os
from typing import List, Dict, Tuple
from datetime import datetime

# Core dependencies
try:
    from sacrebleu.metrics import BLEU
    BLEU_AVAILABLE = True
except ImportError:
    print("⚠️  Install sacrebleu: pip install sacrebleu")
    BLEU_AVAILABLE = False

try:
    from jiwer import wer
    WER_AVAILABLE = True
except ImportError:
    print("⚠️  Install jiwer: pip install jiwer")
    WER_AVAILABLE = False

# Your system
from offline_utils import offline_translate, initialize_offline_resources, is_offline_mode
from deep_translator import GoogleTranslator

# Optional: DeepL
try:
    import deepl
    DEEPL_AVAILABLE = True
except ImportError:
    print("⚠️  Install deepl: pip install deepl")
    DEEPL_AVAILABLE = False


class BenchmarkSuite:
    """Benchmark suite for translation and ASR systems"""
    
    def __init__(self, output_file: str = "benchmark_results.json"):
        self.output_file = output_file
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
        
        # Initialize offline resources
        print("🔧 Initializing offline resources...")
        initialize_offline_resources()
    
    def run_translation_benchmark(
        self,
        test_pairs: List[Dict[str, str]],
        language_pair: Tuple[str, str] = ("en", "hi")
    ):
        """
        Run translation benchmark
        
        Args:
            test_pairs: List of dicts with 'source', 'reference' keys
            language_pair: (source_lang, target_lang) tuple
        """
        src_lang, tgt_lang = language_pair
        print(f"\n📊 Translation Benchmark: {src_lang} → {tgt_lang}")
        print(f"Test cases: {len(test_pairs)}")
        
        systems = {
            "Our System (Offline)": self._translate_our_system_offline,
            "Google Translate": self._translate_google,
        }
        
        if DEEPL_AVAILABLE and os.getenv("DEEPL_API_KEY"):
            systems["DeepL"] = self._translate_deepl
        
        for system_name, translate_fn in systems.items():
            print(f"\n🧪 Testing: {system_name}")
            
            hypotheses = []
            references = []
            timings = []
            errors = 0
            
            for i, pair in enumerate(test_pairs):
                source = pair['source']
                reference = pair['reference']
                
                # Translate and time
                start = time.time()
                try:
                    hypothesis = translate_fn(source, src_lang, tgt_lang)
                    elapsed = time.time() - start
                    
                    if hypothesis:
                        hypotheses.append(hypothesis)
                        references.append([reference])  # BLEU expects list of references
                        timings.append(elapsed)
                    else:
                        errors += 1
                except Exception as e:
                    print(f"  ❌ Error on case {i+1}: {e}")
                    errors += 1
                    continue
            
            # Calculate metrics
            avg_time = sum(timings) / len(timings) if timings else 0
            
            bleu_score = 0
            if BLEU_AVAILABLE and hypotheses:
                bleu = BLEU()
                score = bleu.corpus_score(hypotheses, references)
                bleu_score = score.score / 100  # Convert to 0-1 range
            
            # Store results
            result = {
                "system": system_name,
                "language_pair": f"{src_lang}->{tgt_lang}",
                "test_cases": len(test_pairs),
                "successful": len(hypotheses),
                "errors": errors,
                "bleu_score": round(bleu_score, 2),
                "avg_time_seconds": round(avg_time, 2),
                "samples": [
                    {
                        "source": test_pairs[i]['source'],
                        "reference": test_pairs[i]['reference'],
                        "hypothesis": hypotheses[i] if i < len(hypotheses) else None
                    }
                    for i in range(min(3, len(test_pairs)))  # Show first 3
                ]
            }
            
            self.results["tests"].append(result)
            
            # Print summary
            print(f"  ✅ Successful: {len(hypotheses)}/{len(test_pairs)}")
            print(f"  📈 BLEU Score: {bleu_score:.2f}")
            print(f"  ⏱️  Avg Time: {avg_time:.2f}s")
    
    def run_asr_benchmark(
        self,
        test_pairs: List[Dict[str, str]]
    ):
        """
        Run ASR accuracy benchmark (Word Error Rate)
        
        Args:
            test_pairs: List of dicts with 'reference' and 'hypothesis' keys
        """
        print(f"\n📊 ASR Accuracy Benchmark (WER)")
        print(f"Test cases: {len(test_pairs)}")
        
        if not WER_AVAILABLE:
            print("⚠️  WER calculation unavailable. Install jiwer.")
            return
        
        total_wer = 0
        for pair in test_pairs:
            reference = pair['reference']
            hypothesis = pair['hypothesis']
            error = wer(reference, hypothesis)
            total_wer += error
        
        avg_wer = (total_wer / len(test_pairs)) * 100
        avg_accuracy = 100 - avg_wer
        
        result = {
            "test": "ASR Accuracy",
            "test_cases": len(test_pairs),
            "word_error_rate": round(avg_wer, 1),
            "accuracy": round(avg_accuracy, 1)
        }
        
        self.results["tests"].append(result)
        
        print(f"  📉 Word Error Rate: {avg_wer:.1f}%")
        print(f"  ✅ ASR Accuracy: {avg_accuracy:.1f}%")
    
    def _translate_our_system_offline(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Translate using our offline system"""
        result = offline_translate(text, src_lang=src_lang, tgt_lang=tgt_lang)
        return result if result else ""
    
    def _translate_google(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Translate using Google Translate"""
        try:
            translator = GoogleTranslator(source=src_lang, target=tgt_lang)
            return translator.translate(text)
        except Exception as e:
            print(f"  ⚠️  Google Translate error: {e}")
            return ""
    
    def _translate_deepl(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Translate using DeepL"""
        try:
            api_key = os.getenv("DEEPL_API_KEY")
            if not api_key:
                return ""
            
            translator = deepl.Translator(api_key)
            
            # DeepL uses different language codes
            deepl_target = tgt_lang.upper()
            if tgt_lang == "en":
                deepl_target = "EN-US"
            
            result = translator.translate_text(text, target_lang=deepl_target)
            return result.text
        except Exception as e:
            print(f"  ⚠️  DeepL error: {e}")
            return ""
    
    def save_results(self):
        """Save benchmark results to JSON file"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {self.output_file}")
    
    def print_summary(self):
        """Print formatted summary table"""
        print("\n" + "="*80)
        print("📊 BENCHMARK SUMMARY")
        print("="*80)
        
        # Translation results
        translation_tests = [t for t in self.results["tests"] if "bleu_score" in t]
        if translation_tests:
            print("\n🌐 Translation Quality (BLEU Score: 0-1, higher is better)")
            print("-" * 80)
            print(f"{'System':<30} {'Lang Pair':<12} {'BLEU':<8} {'Time(s)':<10} {'Success':<10}")
            print("-" * 80)
            
            for test in translation_tests:
                success_rate = f"{test['successful']}/{test['test_cases']}"
                print(f"{test['system']:<30} {test['language_pair']:<12} "
                      f"{test['bleu_score']:<8} {test['avg_time_seconds']:<10} {success_rate:<10}")
        
        # ASR results
        asr_tests = [t for t in self.results["tests"] if "word_error_rate" in t]
        if asr_tests:
            print("\n🎤 ASR Accuracy (WER: lower is better)")
            print("-" * 80)
            for test in asr_tests:
                print(f"Word Error Rate: {test['word_error_rate']:.1f}%")
                print(f"ASR Accuracy: {test['accuracy']:.1f}%")


# Sample test datasets
SAMPLE_EN_HI_PAIRS = [
    {
        "source": "Hello, how are you?",
        "reference": "नमस्ते, आप कैसे हैं?"
    },
    {
        "source": "What is your name?",
        "reference": "आपका नाम क्या है?"
    },
    {
        "source": "I am learning Hindi.",
        "reference": "मैं हिंदी सीख रहा हूं।"
    },
    {
        "source": "Thank you very much.",
        "reference": "बहुत बहुत धन्यवाद।"
    },
    {
        "source": "Where is the nearest hospital?",
        "reference": "निकटतम अस्पताल कहाँ है?"
    }
]

SAMPLE_EN_BN_PAIRS = [
    {
        "source": "Good morning",
        "reference": "সুপ্রভাত"
    },
    {
        "source": "How much does this cost?",
        "reference": "এটার দাম কত?"
    },
    {
        "source": "I need help",
        "reference": "আমার সাহায্য দরকার"
    }
]

SAMPLE_ASR_PAIRS = [
    {
        "reference": "hello world how are you",
        "hypothesis": "hello world how you are"
    },
    {
        "reference": "the quick brown fox",
        "hypothesis": "the quick brown fox"
    },
    {
        "reference": "artificial intelligence is amazing",
        "hypothesis": "artificial intelligence is amazing"
    }
]


def main():
    """Run comprehensive benchmark"""
    print("🚀 Multilingual Bot Benchmark Suite")
    print("=" * 80)
    
    # Create benchmark suite
    benchmark = BenchmarkSuite(output_file="benchmark_results.json")
    
    # Run translation benchmarks
    print("\n📝 Running translation benchmarks...")
    benchmark.run_translation_benchmark(SAMPLE_EN_HI_PAIRS, language_pair=("en", "hi"))
    benchmark.run_translation_benchmark(SAMPLE_EN_BN_PAIRS, language_pair=("en", "bn"))
    
    # Run ASR benchmark
    print("\n🎤 Running ASR accuracy benchmark...")
    benchmark.run_asr_benchmark(SAMPLE_ASR_PAIRS)
    
    # Save and print results
    benchmark.save_results()
    benchmark.print_summary()
    
    print("\n✅ Benchmark complete!")
    print(f"📄 Detailed results: benchmark_results.json")


if __name__ == "__main__":
    main()
