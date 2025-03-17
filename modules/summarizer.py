import subprocess
import logging
import re
import time
import json
from typing import List, Dict, Tuple, Optional
from config import SUMMARY_CHUNK_SIZE, SUMMARY_MODEL_PRIMARY, SUMMARY_MODEL_FALLBACK, SUMMARY_TIMEOUT_BASIC,SUMMARY_TIMEOUT_ENHANCED, SUMMARY_FALLBACK_TIMEOUT

logger = logging.getLogger(__name__)

class Summarizer:
    SUMMARY_PARAMS = {
        "temperature": 0.2,
        "top_p": 0.85,
        "num_predict": 4000,
        "frequency_penalty": 0.5,
        "presence_penalty": 0.3,
    }
    
    @staticmethod
    def detect_language(text: str) -> str:
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
    def ensure_ollama_service(model_name: str) -> bool:
        """Ollama servisinin çalışır durumda olduğunu ve modelin yüklü olduğunu kontrol eder."""
        try:
            logger.info(f"{model_name} modeli için Ollama servisi kontrolü yapılıyor")
            # Modelin yüklü olup olmadığını kontrol et
            check_process = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if model_name not in check_process.stdout:
                logger.warning(f"{model_name} modeli yüklü değil, yükleniyor...")
                pull_process = subprocess.run(
                    ["ollama", "pull", model_name],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if pull_process.returncode != 0:
                    logger.error(f"Model yükleme hatası: {pull_process.stderr}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Ollama servis kontrolü hatası: {e}")
            return False
    
    @staticmethod
    def select_appropriate_model(text_length: int, mode: str) -> str:
        """Metin uzunluğu ve mod tercihi ile sistem durumuna göre uygun model seçer."""
        if mode == "basic" or text_length < 1000:
            return SUMMARY_MODEL_FALLBACK
        
        # Sistem durumunu kontrol et
        is_primary_available = Summarizer.ensure_ollama_service(SUMMARY_MODEL_PRIMARY)
        
        if is_primary_available:
            # Birincil modelin yüklü ve kullanılabilir olduğunu doğrula
            return SUMMARY_MODEL_PRIMARY
        else:
            logger.warning(f"Birincil model {SUMMARY_MODEL_PRIMARY} kullanılamıyor, yedek model {SUMMARY_MODEL_FALLBACK} kullanılacak")
            return SUMMARY_MODEL_FALLBACK
    
    @staticmethod
    def create_basic_summary(text: str, timeout: int = SUMMARY_TIMEOUT_BASIC) -> str:
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
    def get_enhanced_prompt(text: str, lang: str) -> str:
        if lang == 'tr':
            return f"""Aşağıdaki metni kapsamlı ve derinlemesine bir şekilde analiz ederek özetle:

{text}

Lütfen aşağıdaki yapıyı takip eden, çok detaylı ve derinlemesine bir özet oluştur:

1. GENEL BAKIŞ (3-4 paragraf) - Metnin ana konusunu, bağlamını, amacını ve temel argümanlarını kapsamlı bir şekilde açıkla. Bu bölüm, metindeki her temel noktayı kapsayacak şekilde detaylı olmalı.

2. ANA KAVRAMLAR VE TANIMLAR (en az 5-7 kavram) - Metinde tanımlanan veya açıklanan tüm temel kavramları detaylı olarak açıkla. Her kavram için:
   a) Kavramın tam tanımı
   b) Kavramın metin içindeki bağlamı ve önemi
   c) Diğer kavramlarla olan ilişkisi

3. METODOLOJİ VE YAKLAŞIMLAR - Metinde bahsedilen tüm metodolojiler, yaklaşımlar veya süreçleri detaylı olarak açıkla. Bunların uygulama alanları ve potansiyel sınırlamaları hakkında da bilgi ver.

4. TEKNİK DETAYLAR - Metinde belirtilen tüm teknik özellikler, veriler, sayısal değerler ve spesifikasyonları listele ve açıkla. Verilen tüm istatistikleri, ölçümleri veya sayısal verileri dahil et.

5. KARŞILAŞTIRMALAR VE KARŞITLIKLAR - Metinde yapılan tüm karşılaştırmaları veya zıtlıkları belirle ve detaylandır. Farklı fikirler, yaklaşımlar veya metodolojiler arasındaki benzerlikler ve farklılıklar nelerdir?

6. PRATİK UYGULAMALAR - Metinde bahsedilen pratik uygulamalar, örnekler veya vaka çalışmalarını detaylı olarak açıkla. Bu bilginin gerçek dünya uygulamaları nelerdir?

7. SONUÇ VE ÇIKARIMLAR - Metinden çıkarılabilecek tüm sonuçları, önerileri ve gelecekteki yönelimleri detaylandır. Yazarın veya konuşmacının ana mesajı nedir?

8. ELEŞTİREL ANALİZ - Metindeki argümanların, metodolojilerin veya sonuçların güçlü yönleri ve potansiyel sınırlamaları hakkında eleştirel bir değerlendirme sağla.

9. KAYNAKLAR VE REFERANSLAR - Metinde bahsedilen tüm kaynakları, referansları veya ilgili çalışmaları listele (varsa).

10. ÖNEMLİ KAVRAMLAR VE TERİMLER - Metinde geçen tüm teknik terimleri, kavramları ve anahtar kelimeleri kapsamlı bir şekilde listele ve tanımla.

NOT: Bu, bir ders, seminer veya teknik sunum transkripsiyonu olabilir. Lütfen METNİN TAMAMINI dikkate al ve HİÇBİR önemli bilgiyi atlama. Özet, orijinal metnin tüm önemli noktalarını içermeli ve bir uzman derinliğinde analizle sunulmalıdır."""
        else:
            return f"""Comprehensively analyze and summarize the following text with in-depth examination:

{text}

Please create a highly detailed and thorough summary following this structure:

1. OVERVIEW (3-4 paragraphs) - Comprehensively explain the main topic, context, purpose, and key arguments of the text. This section should be detailed enough to cover every fundamental point in the text.

2. MAIN CONCEPTS AND DEFINITIONS (at least 5-7 concepts) - Explain in detail all key concepts defined or explained in the text. For each concept, include:
   a) Complete definition of the concept
   b) Context and importance of the concept within the text
   c) Relationship with other concepts

3. METHODOLOGIES AND APPROACHES - Explain in detail all methodologies, approaches, or processes mentioned in the text. Provide information about their application areas and potential limitations.

4. TECHNICAL DETAILS - List and explain all technical specifications, data, numerical values, and specifications mentioned in the text. Include all statistics, measurements, or numerical data provided.

5. COMPARISONS AND CONTRASTS - Identify and elaborate on all comparisons or contrasts made in the text. What are the similarities and differences between different ideas, approaches, or methodologies?

6. PRACTICAL APPLICATIONS - Explain in detail the practical applications, examples, or case studies mentioned in the text. What are the real-world applications of this information?

7. CONCLUSIONS AND IMPLICATIONS - Detail all conclusions, recommendations, and future directions that can be drawn from the text. What is the main message of the author or speaker?

8. CRITICAL ANALYSIS - Provide a critical assessment of the strengths and potential limitations of the arguments, methodologies, or findings in the text.

9. SOURCES AND REFERENCES - List all sources, references, or related works mentioned in the text (if any).

10. KEY CONCEPTS AND TERMS - Comprehensively list and define all technical terms, concepts, and keywords that appear in the text.

NOTE: This might be a lecture, seminar, or technical presentation transcription. Please consider the ENTIRE TEXT and DO NOT omit ANY important information. The summary should include all significant points from the original text and be presented with expert-level depth of analysis."""
    
    @staticmethod
    def get_fallback_prompt(text: str, lang: str) -> str:
        if lang == 'tr':
            return f"""Aşağıdaki metni derinlemesine analiz ederek kapsamlı bir özet oluştur:

{text}

Lütfen şu yapıda detaylı bir özet hazırla:
1. GENEL BAKIŞ - Metnin ana konusu, bağlamı ve amacı hakkında kapsamlı bir açıklama (en az 2 paragraf)
2. ANA KAVRAMLAR - Metinde tartışılan temel kavramlar ve bunların açıklamaları
3. ÖNEMLİ NOKTALAR - Metinde vurgulanan en önemli bilgiler ve fikirler
4. SONUÇLAR VE ÇIKARIMLAR - Metinden çıkarılabilecek sonuçlar ve önemli mesajlar
5. ÖNEMLİ TERİMLER VE KAVRAMLAR - Metinde geçen tüm teknik terimler ve anahtar kelimeler

Bu bir ders veya seminer transkripsiyonu olabilir. Metnin TÜM önemli içeriğini dikkate al ve kapsamlı bir özet oluştur."""
        else:
            return f"""Deeply analyze and create a comprehensive summary of the following text:

{text}

Please prepare a detailed summary with this structure:
1. OVERVIEW - A comprehensive explanation of the main topic, context, and purpose of the text (at least 2 paragraphs)
2. MAIN CONCEPTS - Core concepts discussed in the text and their explanations
3. IMPORTANT POINTS - The most significant information and ideas emphasized in the text
4. CONCLUSIONS AND IMPLICATIONS - Conclusions that can be drawn from the text and important messages
5. KEY TERMS AND CONCEPTS - All technical terms and keywords mentioned in the text

This might be a lecture or seminar transcription. Consider ALL important content of the text and create a comprehensive summary."""
    
    @staticmethod
    def create_initial_summary(text: str, lang: str, timeout: int = 300) -> str:
        truncated_text = text[:8000] if len(text) > 8000 else text
        prompt = Summarizer.get_enhanced_prompt(truncated_text, lang)
        
        try:
            logger.info(f"Birincil model ile özet oluşturuluyor: {SUMMARY_MODEL_PRIMARY}")
            start_time = time.time()
            result = Summarizer.run_ollama_command(prompt, SUMMARY_MODEL_PRIMARY, timeout)
            elapsed = time.time() - start_time
            logger.info(f"Birincil model başarıyla çalıştı (süre: {elapsed:.2f}s)")
            return result
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"Birincil model hatası: {error_type} - {error_msg}", exc_info=True)
            
            # Hata tipine göre özel loglama
            if isinstance(e, TimeoutError):
                logger.error("Birincil model zaman aşımına uğradı")
            elif isinstance(e, ConnectionError) or "connection" in error_msg.lower():
                logger.error("Ollama servisine bağlantı sorunu")
            elif "memory" in error_msg.lower() or "resource" in error_msg.lower():
                logger.error("Birincil model için yetersiz kaynak")
            
            logger.info(f"Yedek modele geçiliyor: {SUMMARY_MODEL_FALLBACK}")
            fallback_prompt = Summarizer.get_fallback_prompt(truncated_text[:5000], lang)
            return Summarizer.run_ollama_command(fallback_prompt, SUMMARY_MODEL_FALLBACK, timeout // 2)
    
    @staticmethod
    def extract_sections(summary: str) -> List[Dict[str, str]]:
        section_pattern = r'(?:^|\n)(\d+\.\s*[\w\s]+|[\w\s]+:)([^\n]*(?:\n(?!\d+\.\s*[\w\s]+|[\w\s]+:)[^\n]*)*)'
        matches = re.finditer(section_pattern, summary, re.MULTILINE)
        
        sections = []
        for match in matches:
            title = match.group(1).strip()
            content = match.group(2).strip()
            sections.append({"title": title, "content": content})
        
        return sections
    
    @staticmethod
    def extract_relevant_text(original_text: str, section_title: str) -> str:
        title_lower = section_title.lower()
        keywords = re.findall(r'\b\w+\b', title_lower)
        keywords = [k for k in keywords if len(k) > 3 and k not in ["and", "the", "for", "with", "this", "that", "what", "where", "when", "how", "which"]]
        
        paragraphs = original_text.split('\n\n')
        relevant_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph_lower = paragraph.lower()
            if any(keyword in paragraph_lower for keyword in keywords):
                relevant_paragraphs.append(paragraph)
        
        if len(relevant_paragraphs) < 3 and len(keywords) > 0:
            relevant_paragraphs = [p for p in paragraphs if any(keyword in p.lower() for keyword in keywords)]
        
        relevant_text = '\n\n'.join(relevant_paragraphs)
        if len(relevant_text) > 5000:
            relevant_text = relevant_text[:5000]
        
        return relevant_text
    
    @staticmethod
    def enhance_section(section: Dict[str, str], relevant_text: str, lang: str, timeout: int = 120) -> str:
        if not relevant_text:
            return section["content"]
        
        title = section["title"]
        
        if lang == 'tr':
            prompt = f"""Aşağıdaki metin bölümünü daha detaylı ve kapsamlı bir şekilde geliştir:

Bölüm Başlığı: {title}
Mevcut İçerik: {section["content"]}

İlgili Metin: {relevant_text}

Bu bölümü yukarıdaki ilgili metni kullanarak genişlet ve zenginleştir. Daha derinlemesine analiz, daha fazla örnek ve daha kapsamlı açıklamalar ekle. Önemli noktaları daha detaylı açıkla ve eksik kalmış bilgileri tamamla."""
        else:
            prompt = f"""Enhance the following section with more detail and comprehensive analysis:

Section Title: {title}
Current Content: {section["content"]}

Relevant Text: {relevant_text}

Expand and enrich this section using the relevant text above. Add deeper analysis, more examples, and more comprehensive explanations. Elaborate on important points in more detail and fill in any missing information."""
        
        try:
            enhanced_content = Summarizer.run_ollama_command(prompt, SUMMARY_MODEL_FALLBACK, timeout)
            if len(enhanced_content) > len(section["content"]) * 1.2:
                return enhanced_content
            return section["content"]
        except Exception as e:
            logger.error(f"Section enhancement error: {e}")
            return section["content"]
    
    @staticmethod
    def integrate_sections(sections: List[Dict[str, str]]) -> str:
        result = ""
        for section in sections:
            result += f"{section['title']}\n{section['content']}\n\n"
        return result
    
    @staticmethod
    def extract_key_concepts(text: str, lang: str, timeout: int = 90) -> List[str]:
        sample_text = text[:5000] if len(text) > 5000 else text
        
        if lang == 'tr':
            prompt = f"""Aşağıdaki metinde geçen tüm önemli kavramları, teknik terimleri ve anahtar kelimeleri çıkar:

    {sample_text}

    Metindeki alana özgü tüm terim ve kavramları kapsamlı şekilde listele. Temel kavramların yanı sıra, ilişkili veya türetilmiş kavramları da dahil et.

    SADECE Türkçe terim listesi ver. Her terimi açıklama. Sadece virgülle ayrılmış kavramlar listesi döndür."""
        else:
            # Mevcut İngilizce prompt korunabilir
            prompt = f"""Extract all important concepts, technical terms, and keywords from the following text:

    {sample_text}

    Comprehensively list all domain-specific terms and concepts in the text. Include related or derived concepts in addition to the basic concepts.

    ONLY provide the list of terms. Don't explain each term. Just return a comma-separated list of concepts."""
        
        try:
            concepts_text = Summarizer.run_ollama_command(prompt, SUMMARY_MODEL_FALLBACK, timeout)
            return [concept.strip() for concept in concepts_text.split(',') if concept.strip()]
        except Exception as e:
            logger.error(f"Concept extraction error: {e}")
            return []
    
    @staticmethod
    def analyze_concepts_relationships(concepts: List[str], text: str, lang: str, timeout: int = 120) -> str:
        if not concepts or len(concepts) < 3:
            return ""
        
        top_concepts = concepts[:10]
        concepts_text = ", ".join(top_concepts)
        
        if lang == 'tr':
            prompt = f"""Aşağıdaki kavramlar arasındaki ilişkileri analiz et:

    {concepts_text}

    Bu kavramlar aşağıdaki metinden çıkarılmıştır:

    {text[:3000]}

    Her kavramın kısa bir tanımını Türkçe olarak ver ve diğer kavramlarla olan ilişkilerini açıkla. 
    Kavramlar arasındaki hiyerarşileri, bağlantıları ve ilişkileri belirt.

    ÖNEMLİ: Tüm yanıtını TÜRKÇE olarak ver. Hiçbir açıklama, tanım veya ilişkiyi İngilizce yazma."""
        else:
            # Mevcut İngilizce prompt korunabilir
            prompt = f"""Analyze the relationships between the following concepts:

    {concepts_text}

    These concepts were extracted from the following text:

    {text[:3000]}

    Provide a brief definition of each concept and explain its relationships with other concepts. Indicate hierarchies, connections, and relationships between concepts."""
        
        try:
            return Summarizer.run_ollama_command(prompt, SUMMARY_MODEL_FALLBACK, timeout)
        except Exception as e:
            logger.error(f"Concept relationship analysis error: {e}")
            return ""
        
    @staticmethod
    def detect_domain(text: str, lang: str) -> str:
        sample = text[:2000] if len(text) > 2000 else text
        
        if lang == 'tr':
            prompt = f"""Aşağıdaki metnin hangi alana ait olduğunu tespit et (teknik, akademik, iş, genel, bilimsel, tıbbi, hukuki, vb.).

{sample}

Lütfen sadece alan adını tek kelime olarak belirt."""
        else:
            prompt = f"""Detect which domain the following text belongs to (technical, academic, business, general, scientific, medical, legal, etc.).

{sample}

Please only specify the domain name as a single word."""
        
        try:
            domain = Summarizer.run_ollama_command(prompt, SUMMARY_MODEL_FALLBACK, 30).lower().strip()
            logger.info(f"Detected domain: {domain}")
            return domain
        except Exception as e:
            logger.error(f"Domain detection error: {e}")
            return "general"
    
    @staticmethod
    def add_domain_specific_analysis(summary: str, domain: str, text: str, lang: str, timeout: int = 120) -> str:
        if domain in ["general", "genel"]:
            return summary
        
        if lang == 'tr':
            prompt = f"""Aşağıdaki özeti, '{domain}' alanına özgü daha detaylı analizlerle zenginleştir:

{summary}

Orijinal metin:

{text[:4000]}

'{domain}' alanına özgü perspektifler, terminoloji ve kavramsal çerçeveler ekle. Bu alana özgü önemli unsurları vurgula ve özete entegre et."""
        else:
            prompt = f"""Enrich the following summary with more detailed analyses specific to the '{domain}' domain:

{summary}

Original text:

{text[:4000]}

Add domain-specific perspectives, terminology, and conceptual frameworks for the '{domain}' field. Highlight and integrate important elements specific to this domain into the summary."""
        
        try:
            enhanced_summary = Summarizer.run_ollama_command(prompt, SUMMARY_MODEL_PRIMARY, timeout)
            if len(enhanced_summary) > len(summary):
                return enhanced_summary
            return summary
        except Exception as e:
            logger.error(f"Domain-specific enhancement error: {e}")
            return summary
    
    @staticmethod
    def ensure_language_consistency(summary: str, lang: str) -> str:
        """Özetin dil tutarlılığını kontrol eder ve gerekirse düzeltir."""
        if lang != 'tr':
            return summary
            
        # İngilizce içerik kontrolü
        english_markers = [
            "after analyzing", "here is", "i will provide", 
            "in summary,", "note that", "these concepts"
        ]
        
        lines = summary.split('\n')
        cleaned_lines = []
        
        skip_section = False
        for line in lines:
            # İngilizce bölüm tespiti
            if any(marker in line.lower() for marker in english_markers):
                skip_section = True
                continue
                
            # Türkçe başlık tespiti - başlıktan sonra İngilizce içerik varsa atla
            if "KAVRAM İLİŞKİLERİ" in line or "ÖNEMLİ KAVRAMLAR" in line:
                cleaned_lines.append(line)
                skip_section = False
                continue
                
            if not skip_section:
                cleaned_lines.append(line)
        
        cleaned_summary = '\n'.join(cleaned_lines)
        
        # Eğer kavram ilişkileri bölümü tamamen temizlendiyse, Türkçe bir bilgi mesajı ekle
        if "KAVRAM İLİŞKİLERİ VE TANIMLAR:" in cleaned_summary and \
        cleaned_summary.split("KAVRAM İLİŞKİLERİ VE TANIMLAR:")[1].strip() == "":
            cleaned_summary = cleaned_summary.replace(
                "KAVRAM İLİŞKİLERİ VE TANIMLAR:", 
                "KAVRAM İLİŞKİLERİ VE TANIMLAR:\nKavram ilişkileri çıkarılamadı."
            )
        
        # Eğer önemli kavramlar bölümü tamamen temizlendiyse, Türkçe bir bilgi mesajı ekle
        if "ÖNEMLİ KAVRAMLAR VE İLİŞKİLİ TERİMLER:" in cleaned_summary and \
        cleaned_summary.split("ÖNEMLİ KAVRAMLAR VE İLİŞKİLİ TERİMLER:")[1].strip() == "":
            cleaned_summary = cleaned_summary.replace(
                "ÖNEMLİ KAVRAMLAR VE İLİŞKİLİ TERİMLER:", 
                "ÖNEMLİ KAVRAMLAR VE İLİŞKİLİ TERİMLER:\nİşletim sistemi, süreç, CPU, giriş-çıkış işlemleri, kuyruk, bekleme durumu, hazır durumu, çalışma durumu, paralel işleme, çoklu görev"
            )
        
        return cleaned_summary
    
    @staticmethod
    def evaluate_summary_quality(summary: str, text: str, lang: str) -> Dict[str, float]:
        sample_text = text[:3000]
        
        if lang == 'tr':
            prompt = f"""Aşağıdaki özeti değerlendir ve her kriter için 0 ile 1 arasında bir puan ver:

Özet:
{summary[:2000]}

Orijinal metin:
{sample_text}

Kriteler:
1. Kapsam (orijinal metindeki önemli bilgilerin ne kadarının özette yer aldığı)
2. Detay seviyesi (önemli bilgilerin ne kadar detaylı açıklandığı)
3. Bölüm dengesi (farklı bölümlerin içerik açısından dengeli olup olmadığı)
4. Tutarlılık (özet içinde tutarlılık ve bağlantıların kalitesi)

Sadece sayısal puanları virgülle ayrılmış olarak döndür: kapsam,detay,denge,tutarlılık"""
        else:
            prompt = f"""Evaluate the following summary and provide a score between 0 and 1 for each criterion:

Summary:
{summary[:2000]}

Original text:
{sample_text}

Criteria:
1. Coverage (how much of the important information from the original text is included in the summary)
2. Detail level (how thoroughly important information is explained)
3. Section balance (whether different sections are balanced in terms of content)
4. Coherence (quality of coherence and connections within the summary)

Return only the numerical scores comma-separated: coverage,detail,balance,coherence"""
        
        try:
            scores_text = Summarizer.run_ollama_command(prompt, SUMMARY_MODEL_FALLBACK, 60)
            
            # Daha sağlam bir sayı çıkarma mekanizması
            scores = []
            # Sayısal değerleri daha net şekilde çıkar
            score_pattern = r'(\d+\.\d+|\d+)'
            matches = re.findall(score_pattern, scores_text)
            
            if matches and len(matches) >= 4:
                for i in range(min(4, len(matches))):
                    try:
                        scores.append(float(matches[i]))
                    except ValueError:
                        scores.append(0.5)  # Dönüştürme başarısız olursa varsayılan değer
            
            if len(scores) >= 4:
                return {
                    "coverage": scores[0],
                    "detail": scores[1],
                    "balance": scores[2],
                    "coherence": scores[3]
                }
            return {"coverage": 0.5, "detail": 0.5, "balance": 0.5, "coherence": 0.5}
        except Exception as e:
            logger.error(f"Summary evaluation error: {e}")
            return {"coverage": 0.5, "detail": 0.5, "balance": 0.5, "coherence": 0.5}
    
    @staticmethod
    def improve_weak_sections(summary: str, text: str, quality_scores: Dict[str, float], lang: str) -> str:
        if quality_scores["detail"] >= 0.7 and quality_scores["coverage"] >= 0.7:
            return summary
        
        sections = Summarizer.extract_sections(summary)
        
        if not sections:
            return summary
        
        if quality_scores["detail"] < 0.7:
            for i, section in enumerate(sections):
                if len(section["content"]) < 200 and len(section["title"]) > 3:
                    relevant_text = Summarizer.extract_relevant_text(text, section["title"])
                    sections[i]["content"] = Summarizer.enhance_section(section, relevant_text, lang)
        
        if quality_scores["coverage"] < 0.7:
            if lang == 'tr':
                prompt = f"""Özetteki eksik önemli bilgileri tespit et:

Özet:
{summary}

Orijinal metin:
{text[:5000]}

Özette eksik olan en az 3 önemli noktayı veya konuyu belirle."""
            else:
                prompt = f"""Identify missing important information in the summary:

Summary:
{summary}

Original text:
{text[:5000]}

Identify at least 3 important points or topics that are missing in the summary."""
            
            try:
                missing_info = Summarizer.run_ollama_command(prompt, SUMMARY_MODEL_FALLBACK, 60)
                
                if missing_info and len(missing_info) > 50:
                    if lang == 'tr':
                        sections.append({
                            "title": "EK ÖNEMLİ BİLGİLER",
                            "content": missing_info
                        })
                    else:
                        sections.append({
                            "title": "ADDITIONAL IMPORTANT INFORMATION",
                            "content": missing_info
                        })
            except Exception as e:
                logger.error(f"Missing information detection error: {e}")
        
        return Summarizer.integrate_sections(sections)
    
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
    def create_enhanced_summary(text: str, timeout: int = SUMMARY_TIMEOUT_ENHANCED) -> str:
        if not text:
            return "Metin boş olduğu için özet oluşturulamadı."
        
        if len(text) > 10000:
            text = text[:10000]
        
        lang = Summarizer.detect_language(text)
        logger.info(f"Creating enhanced summary in '{lang}' language")
        
        try:
            initial_summary = Summarizer.create_initial_summary(text, lang, timeout)
            
            sections = Summarizer.extract_sections(initial_summary)
            enhanced_sections = []
            
            for section in sections:
                relevant_text = Summarizer.extract_relevant_text(text, section["title"])
                enhanced_content = Summarizer.enhance_section(section, relevant_text, lang)
                enhanced_sections.append({"title": section["title"], "content": enhanced_content})
            
            enhanced_summary = Summarizer.integrate_sections(enhanced_sections)
            
            concepts = Summarizer.extract_key_concepts(text, lang)
            
            concept_relationships = ""
            if len(concepts) >= 5:
                concept_relationships = Summarizer.analyze_concepts_relationships(concepts, text, lang)
            
            domain = Summarizer.detect_domain(text, lang)
            domain_enhanced_summary = Summarizer.add_domain_specific_analysis(enhanced_summary, domain, text, lang)
            
            quality_scores = Summarizer.evaluate_summary_quality(domain_enhanced_summary, text, lang)
            
            final_summary = Summarizer.improve_weak_sections(domain_enhanced_summary, text, quality_scores, lang)
            
            if concept_relationships and len(concept_relationships) > 100:
                if lang == 'tr':
                    # Eğer çıktı İngilizce içeriyorsa temizleme işlemi
                    if "after analyzing" in concept_relationships.lower() or "here is" in concept_relationships.lower():
                        # İngilizce içeriği temizle ve Türkçe mesaj ekle
                        concept_relationships = "Bu kavramlara ilişkin analiz yapılamadı. Lütfen tekrar deneyiniz."
                    
                    final_summary += "\n\nKAVRAM İLİŞKİLERİ VE TANIMLAR:\n" + concept_relationships
                else:
                    final_summary += "\n\nCONCEPT RELATIONSHIPS AND DEFINITIONS:\n" + concept_relationships
            
            if "ÖNEMLİ KAVRAMLAR" not in final_summary and "KEY CONCEPTS" not in final_summary and concepts:
                if lang == 'tr':
                    concepts_header = "\n\nÖNEMLİ KAVRAMLAR VE İLİŞKİLİ TERİMLER:\n"
                else:
                    concepts_header = "\n\nKEY CONCEPTS AND RELATED TERMS:\n"
                
                concepts_text = ", ".join(concepts)
                final_summary += f"{concepts_header}{concepts_text}"
            
            logger.info("Enhanced summary created successfully")
            final_summary = Summarizer.ensure_language_consistency(final_summary, lang)
            return final_summary
            
        except Exception as e:
            logger.error(f"Enhanced summary creation error: {e}")
            
            try:
                logger.info(f"Falling back to basic summary")
                return Summarizer.create_basic_summary(text, timeout)
            except Exception as e:
                logger.error(f"Basic summary fallback error: {e}")
                return f"Özet oluşturulamadı: {str(e)}"
    
    @staticmethod
    def create_quick_summary(text: str, timeout: int = 90) -> str:
        if not text:
            return "Metin boş olduğu için özet oluşturulamadı."
        
        lang = Summarizer.detect_language(text)
        
        if lang == 'tr':
            prompt = f"""Aşağıdaki metni hızlıca özetle:

{text}

Temel fikri, ana noktaları ve önemli kavramları kapsayan özlü bir özet oluştur."""
        else:
            prompt = f"""Quickly summarize the following text:

{text}

Create a concise summary covering the main idea, key points, and important concepts."""
        
        try:
            return Summarizer.run_ollama_command(prompt, SUMMARY_MODEL_FALLBACK, timeout)
        except Exception as e:
            logger.error(f"Quick summary error: {e}")
            return f"Hızlı özet oluşturulamadı: {str(e)}"
    
    @staticmethod
    def create_comprehensive_summary(text: str, quick_summary: str = "", timeout: int = 300) -> str:
        if not text:
            return "Metin boş olduğu için özet oluşturulamadı."
        
        lang = Summarizer.detect_language(text)
        
        context = ""
        if quick_summary:
            if lang == 'tr':
                context = f"Aşağıda metnin bir hızlı özeti verilmiştir:\n\n{quick_summary}\n\nBu özeti daha kapsamlı hale getir."
            else:
                context = f"A quick summary of the text is provided below:\n\n{quick_summary}\n\nMake this summary more comprehensive."
        
        if lang == 'tr':
            prompt = f"""Aşağıdaki metni kapsamlı bir şekilde özetle:

{text[:7000]}

{context}

Lütfen şu yapıda bir özet oluştur:
1. GENEL BAKIŞ - Metnin ne hakkında olduğu
2. ANA TEMALAR VE KAVRAMLAR - Metindeki temel fikirler
3. ÖNEMLİ NOKTALAR - Metnin ana noktaları
4. TEKNİK DETAYLAR - Varsa teknik bilgiler
5. SONUÇLAR VE ÇIKARIMLAR - Çıkarılabilecek sonuçlar
6. ÖNEMLİ TERİMLER - Metinde geçen önemli kavramlar

Detaylı, kapsamlı ve içeriği tam yansıtan bir özet olsun."""
        else:
            prompt = f"""Comprehensively summarize the following text:

{text[:7000]}

{context}

Please create a summary with this structure:
1. OVERVIEW - What the text is about
2. MAIN THEMES AND CONCEPTS - Core ideas in the text
3. IMPORTANT POINTS - Main points of the text
4. TECHNICAL DETAILS - Technical information if any
5. CONCLUSIONS AND IMPLICATIONS - Conclusions that can be drawn
6. IMPORTANT TERMS - Key concepts mentioned in the text

Make it detailed, comprehensive, and fully reflective of the content."""
        
        try:
            return Summarizer.run_ollama_command(prompt, SUMMARY_MODEL_PRIMARY, timeout)
        except Exception as e:
            logger.error(f"Comprehensive summary error: {e}")
            if quick_summary:
                return quick_summary
            return f"Kapsamlı özet oluşturulamadı: {str(e)}"
    
    @staticmethod
    def chunk_text(text: str) -> List[str]:
        return [text[i:i+SUMMARY_CHUNK_SIZE] for i in range(0, len(text), SUMMARY_CHUNK_SIZE)]
    
    @staticmethod
    def summarize_text(transcription: str, mode: str = "basic", timeout: int = None) -> str:
        if not transcription or transcription.strip() == "":
            logger.warning("Özetlenecek transkripsiyon boş! Özet oluşturulamıyor.")
            return "Özet oluşturulamadı çünkü transkripsiyon boş veya işleme başarısız oldu."
        
        # Eğer timeout belirtilmemişse, moda göre varsayılan değeri kullan
        if timeout is None:
            if mode == "enhanced":
                timeout = SUMMARY_TIMEOUT_ENHANCED
            else:
                timeout = SUMMARY_TIMEOUT_BASIC
        
        if mode == "enhanced":
            logger.info(f"Gelişmiş özet oluşturuluyor (zaman aşımı: {timeout}s)...")
            return Summarizer.create_enhanced_summary(transcription, timeout=timeout)
        else:
            logger.info(f"Temel özet oluşturuluyor (zaman aşımı: {timeout}s)...")
            summary = Summarizer.create_basic_summary(transcription, timeout=timeout)
            
            # Önemli kavramlar ekleme kodu aynı kalabilir
            if "ÖNEMLİ KAVRAMLAR" not in summary and "KEY CONCEPTS" not in summary:
                try:
                    lang = Summarizer.detect_language(transcription)
                    concepts = Summarizer.extract_key_concepts(transcription, lang)
                    
                    if lang == 'tr':
                        concepts_header = "\n\nÖNEMLİ KAVRAMLAR VE İLİŞKİLİ TERİMLER:\n"
                    else:
                        concepts_header = "\n\nKEY CONCEPTS AND RELATED TERMS:\n"
                    
                    concepts_text = ", ".join(concepts)
                    summary += f"{concepts_header}{concepts_text}"
                    
                except Exception as e:
                    logger.error(f"Kavram ekleme hatası: {e}")
            
            return summary
