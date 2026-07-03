import os
import re
import pytesseract
from PIL import Image
from pathlib import Path

# ===================== CONFIGURAÇÕES =====================
# Caminho do Tesseract (ajuste se necessário no Windows)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Pasta com as imagens
PASTA_IMAGENS = "imagens_processadas"  # ou "." para pasta atual

# Padrão para encontrar o número da questão (ex: QUESTÃO 91, Questao 12, etc.)
PADRAO_QUESTAO = re.compile(r'QUEST[ÃA]O\s*(\d+)', re.IGNORECASE)

def extrair_numero_questao(imagem_path):
    try:
        # Abrir imagem
        img = Image.open(imagem_path)
        
        # Pré-processamento básico para melhorar OCR
        img = img.convert('L')  # Converter para escala de cinza
        
        # Extrair texto com pytesseract
        texto = pytesseract.image_to_string(img, lang='por')  # 'por' para português
        
        # Procurar o número da questão
        match = PADRAO_QUESTAO.search(texto)
        if match:
            return match.group(1).strip()
        
        # Backup: procurar qualquer número grande no começo do texto
        numeros = re.findall(r'\b\d{1,3}\b', texto)
        if numeros:
            return numeros[0]
            
        return None
    except Exception as e:
        print(f"Erro ao processar {imagem_path}: {e}")
        return None


def renomear_imagens():
    contador = 0
    for arquivo in os.listdir(PASTA_IMAGENS):
        if arquivo.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            caminho = os.path.join(PASTA_IMAGENS, arquivo)
            
            # Ignorar arquivos já renomeados
            if re.match(r'questao-\d+', arquivo.lower()):
                continue
                
            numero = extrair_numero_questao(caminho)
            
            if numero:
                novo_nome = f"questao-{numero}.jpg"
                novo_caminho = os.path.join(PASTA_IMAGENS, novo_nome)
                
                # Evitar sobrescrever
                if os.path.exists(novo_caminho):
                    base, ext = os.path.splitext(novo_nome)
                    novo_nome = f"{base}_{contador}{ext}"
                    novo_caminho = os.path.join(PASTA_IMAGENS, novo_nome)
                
                os.rename(caminho, novo_caminho)
                print(f"✅ Renomeado: {arquivo} → {novo_nome}")
                contador += 1
            else:
                print(f"⚠️  Não foi possível identificar número em: {arquivo}")

if __name__ == "__main__":
    print("🚀 Iniciando renomeação de questões...\n")
    renomear_imagens()
    print("\n✅ Processo finalizado!")