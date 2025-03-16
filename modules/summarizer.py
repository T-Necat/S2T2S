import subprocess
import logging
import re
import json
from typing import List, Dict
from config import SUMMARY_CHUNK_SIZE, SUMMARY_MODEL_PRIMARY, SUMMARY_MODEL_FALLBACK, SUMMARY_TIMEOUT, SUMMARY_FALLBACK_TIMEOUT

logger = logging.getLogger(__name__)

class Summarizer:
    SUMMARY_PARAMS = {
        "temperature": 0.3,
        "top_p": 0.9,
        "num_predict": 1800,
    }
    
    @staticmethod
    def detect_language(text: str) -> str:
        """Metindeki yaygın kelimelere bakarak dili tespit eder."""
        lang_markers = {
            'tr': ['ve', 'bu', 'bir', 'için', 'ile', 'olarak', 'çok', 'daha', 'ama', 'gibi'],
            'en': ['the', 'and', 'is', 'of', 'to', 'a', 'in', 'that', 'it', 'you'],
        }
        
        words = text.lower().split()
        word_count = min(200, len(words))
        
        lang_scores = {}
        for lang, markers in lang_markers.items():
            lang_scores[lang] = sum(1 for word in words[:word_count] if word in markers)
        
        max_lang = max(lang_scores.items(), key=lambda x: x[1])
        if max_lang[1] > 0:
            logger.info(f"Tespit edilen dil: {max_lang[0]} (skor: {max_lang[1]})")
            return max_lang[0]
        
        return 'tr'

    @staticmethod
    def run_ollama_command(prompt: str, model: str, timeout: int = 300) -> str:
        """Ollama modelini çalıştırır ve sonucu döndürür.
        
        Args:
            prompt: Modele gönderilecek istek metni
            model: Kullanılacak model adı
            timeout: Saniye cinsinden zaman aşımı süresi
            
        Returns:
            Model çıktısı veya hata mesajı
        """
        try:
            logger.info(f"'{model}' modeli çalıştırılıyor (zaman aşımı: {timeout}s)")
            
            process = subprocess.run(
                ["ollama", "run", model],
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
                check=False
            )
            
            if process.returncode != 0:
                error_msg = f"Model çalıştırma hatası (kod {process.returncode}): {process.stderr}"
                logger.error(error_msg)
                raise RuntimeError(f"Model çalıştırma hatası: {process.stderr}")
                
            output = process.stdout.strip()
            if not output:
                logger.warning(f"'{model}' modeli boş yanıt döndürdü")
                raise ValueError("Model boş yanıt döndürdü")
                
            return Summarizer.clean_output(output)
            
        except subprocess.TimeoutExpired:
            logger.error(f"'{model}' modeli {timeout} saniye sonra zaman aşımına uğradı")
            raise TimeoutError(f"İşlem {timeout} saniye içinde tamamlanamadı")
            
        except Exception as e:
            logger.error(f"'{model}' çalıştırma hatası: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def create_summary_with_key_concepts(text: str, timeout: int = SUMMARY_TIMEOUT) -> str:
        """Ana model ile özet oluşturur ve sonuna kavram listesi ekler.
        
        Args:
            text: Özetlenecek metin
            timeout: Zaman aşımı süresi (saniye)
            
        Returns:
            Kavram listesi eklenmiş özet
        """
        if len(text) > 10000:
            text = text[:10000]
        
        lang = Summarizer.detect_language(text)
        
        if (lang == 'tr'):
            prompt = f"""Aşağıdaki metni kapsamlı bir şekilde özetle:

{text}

Lütfen şu yapıda bir özet oluştur:

1. GENEL BAKIŞ - Metnin ana konusunu, bağlamını ve ne anlattığını kapsamlı bir şekilde açıkla (2-3 paragraf). Bu bölüm metnin tamamını iyi bir şekilde temsil etmeli, fazla kısa olmamalı, ancak aşırı uzun da olmamalı.

2. ANA KAVRAMLAR - Metinde açıklanan temel kavramlar nelerdir?

3. TEKNİK DETAYLAR - Önemli teknik bilgiler nelerdir?

4. İLİŞKİLER VE BAĞLANTILAR - Kavramlar arasındaki ilişkiler nelerdir?

5. SONUÇ VE ÇIKARIMLAR - Metinden çıkarılabilecek sonuçlar nelerdir?

Özetin sonunda "ÖNEMLİ KAVRAMLAR VE İLİŞKİLİ TERİMLER" başlığı altında metinde geçen tüm önemli kavramları ve terimleri listele.

NOT: Bu bir ders veya seminer transkripsiyonu olabilir, bu yüzden TÜM içeriği dikkate al ve kapsamlı bir özet oluştur.
"""
        else:
            prompt = f"""Please comprehensively summarize the following text:

{text}

Create a summary with the following structure:

1. OVERVIEW - Comprehensively explain the main topic, context, and what the text is about (2-3 paragraphs). This section should represent the entire text well, not being too short but also not excessively long.

2. MAIN CONCEPTS - What are the key concepts explained in the text?

3. TECHNICAL DETAILS - What are the important technical information?

4. RELATIONSHIPS AND CONNECTIONS - What are the relationships between concepts?

5. CONCLUSIONS AND IMPLICATIONS - What conclusions can be drawn from the text?

At the end of the summary, under the heading "KEY CONCEPTS AND RELATED TERMS", please list all important concepts and terms mentioned in the text.

NOTE: This might be a lecture or seminar transcription, so consider ALL content and create a comprehensive summary.
"""
        
        try:
            logger.info(f"Ana model ile özet oluşturuluyor (zaman aşımı: {timeout}s)...")
            summary = Summarizer.run_ollama_command(
                prompt=prompt,
                model=SUMMARY_MODEL_PRIMARY,
                timeout=timeout
            )
            
            if summary and len(summary) > 300:
                logger.info("Ana model başarıyla özet oluşturdu")
                return summary
            else:
                logger.warning("Ana model yetersiz yanıt verdi, yedek modele geçiliyor")
                raise ValueError("Yetersiz yanıt")
                
        except Exception as e:
            logger.error(f"Ana model hatası: {e}")
            
            try:
                logger.info(f"Yedek model ile özet oluşturuluyor (zaman aşımı: {SUMMARY_FALLBACK_TIMEOUT}s)...")
                
                if lang == 'tr':
                    fallback_prompt = f"""Aşağıdaki metni kapsamlı bir şekilde özetle:

{text[:6000]}

Lütfen şunları içeren bir özet oluştur:
1. GENEL BAKIŞ - Metnin ne hakkında olduğunu ve ana bağlamını açıkla
2. ÖNEMLİ NOKTALAR - Metindeki en önemli bilgiler
3. ÖNEMLİ KAVRAMLAR - Metinde geçen önemli terimler ve kavramlar

Bu bir ders kaydı transkripsiyonu olabilir, metindeki TÜM önemli bilgileri özete dahil et.
"""
                else:
                    fallback_prompt = f"""Comprehensively summarize the following text:

{text[:6000]}

Please create a summary that includes:
1. OVERVIEW - Explain what the text is about and its main context
2. IMPORTANT POINTS - The most important information in the text
3. KEY CONCEPTS - Important terms and concepts mentioned in the text

This might be a lecture transcript, include ALL important information from the text in your summary.
"""
                
                fallback_summary = Summarizer.run_ollama_command(
                    prompt=fallback_prompt,
                    model=SUMMARY_MODEL_FALLBACK,
                    timeout=SUMMARY_FALLBACK_TIMEOUT
                )
                
                if fallback_summary and len(fallback_summary) > 200:
                    logger.info("Yedek model başarıyla özet oluşturdu")
                    return fallback_summary
                else:
                    return "Özet oluşturulamadı. Teknik bir sorun oluştu."
                    
            except Exception as e:
                logger.error(f"Yedek model hatası: {e}")
                return f"Özet oluşturulamadı: {str(e)}"
    
    @staticmethod
    def chunk_text(text: str) -> List[str]:
        return [text[i:i+SUMMARY_CHUNK_SIZE] for i in range(0, len(text), SUMMARY_CHUNK_SIZE)]
    
    @staticmethod
    def extract_key_concepts(text: str, timeout: int = 60) -> List[str]:
        """Metinden önemli kavramları çıkarır.
        
        Args:
            text: Kavramları çıkarılacak metin
            timeout: İşlem zaman aşımı süresi
            
        Returns:
            Önemli kavramlar listesi
        """
        sample_text = text[:5000] if len(text) > 5000 else text
        
        lang = Summarizer.detect_language(sample_text)
        
        if lang == 'tr':
            prompt = f"""Aşağıdaki metinde geçen tüm önemli kavramları, teknik terimleri ve anahtar kelimeleri çıkar:

{sample_text}

Metindeki domain'e özgü tüm terim ve kavramları kapsamlı şekilde listele. Temel kavramların yanı sıra, ilişkili veya türetilmiş kavramları da dahil et.

SADECE terim listesi ver. Her terimi açıklama. Sadece virgülle ayrılmış kavramlar listesi döndür.
"""
        else:
            prompt = f"""Extract all important concepts, technical terms, and keywords from the following text:

{sample_text}

Comprehensively list all domain-specific terms and concepts in the text. Include related or derived concepts in addition to the basic concepts.

ONLY provide the list of terms. Don't explain each term. Just return a comma-separated list of concepts.
"""
        
        try:
            concepts_text = Summarizer.run_ollama_command(
                prompt=prompt,
                model=SUMMARY_MODEL_FALLBACK,
                timeout=timeout
            )
            
            concepts = [concept.strip() for concept in concepts_text.split(',') if concept.strip()]
            return concepts
            
        except Exception as e:
            logger.error(f"Kavram çıkarma hatası: {e}")
            return ["Kavramlar çıkarılamadı"]
    
    @staticmethod
    def clean_output(text: str) -> str:
        patterns = [
            r'<think>.*?</think>',
            r'<userExamples>.*?</userExamples>',
            r'<userStyle>.*?</userStyle>',
            r'düşünme süreçleri:.*?\n',
            r'düşüncelerim:.*?\n',
            r'```json\s*', r'\s*```'
        ]
        
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        return cleaned.strip()
    
    @staticmethod
    def summarize_text(transcription: str) -> str:
        """Tam transkripsiyon metnini özetler.
        
        Args:
            transcription: Özetlenecek transkripsiyon metni
            
        Returns:
            Oluşturulan özet
        """
        if not transcription or transcription.strip() == "":
            logger.warning("Özetlenecek transkripsiyon boş! Özet oluşturulamıyor.")
            return "Özet oluşturulamadı çünkü transkripsiyon boş veya işleme başarısız oldu."
        
        logger.info("Kavramlar içeren özet oluşturuluyor...")
        summary = Summarizer.create_summary_with_key_concepts(transcription, timeout=SUMMARY_TIMEOUT)
        
        if "ÖNEMLİ KAVRAMLAR" not in summary and "KEY CONCEPTS" not in summary:
            try:
                concepts = Summarizer.extract_key_concepts(transcription)
                
                lang = Summarizer.detect_language(transcription)
                
                if lang == 'tr':
                    concepts_header = "\n\nÖNEMLİ KAVRAMLAR VE İLİŞKİLİ TERİMLER:\n"
                else:
                    concepts_header = "\n\nKEY CONCEPTS AND RELATED TERMS:\n"
                
                concepts_text = ", ".join(concepts)
                summary += f"{concepts_header}{concepts_text}"
                
            except Exception as e:
                logger.error(f"Kavram ekleme hatası: {e}")
        
        return summary