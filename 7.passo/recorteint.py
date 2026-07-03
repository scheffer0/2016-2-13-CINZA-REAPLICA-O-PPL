import cv2
import pytesseract
import re
import os

arquivo = "colunas_concatenadas_verticalmente.png"

print("Pasta atual:", os.getcwd())
print("Arquivo existe?", os.path.exists(arquivo))
print("Arquivos na pasta:")
for f in os.listdir():
    print("-", f)

# Caso o tesseract não esteja no PATH do sistema, descomente e ajuste a linha abaixo:
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def recortar_imagem_gigante(caminho_imagem_grande="colunas_concatenadas_verticalmente.png", pasta_saida="imagens_processadas"):
    """
    Processa imagens extremamente longas fatiando-as em blocos menores para o OCR,
    evitando o estouro de limite de pixels do Tesseract.
    """
    os.makedirs(pasta_saida, exist_ok=True)
    
    print(f"[*] Carregando a imagem gigante ({caminho_imagem_grande})...")
    img = cv2.imread(caminho_imagem_grande)
    if img is None:
        print(f"[ERRO] Não foi possível carregar o arquivo: {caminho_imagem_grande}")
        return
        
    h_img, w_img, _ = img.shape
    print(f"[OK] Imagem carregada! Dimensões: {w_img}x{h_img} pixels.")
    
    # Lista global para guardar as coordenadas Y reais na imagem original
    linhas_questoes = []
    
    # Configurações de fatiamento para o OCR
    tamanho_fatia = 20000  # Altura de cada pedaço para o OCR processar por vez
    sobreposicao = 2000    # Margem para garantir que nenhuma palavra fique dividida no corte
    
    y_atual = 0
    print("[*] Iniciando varredura por fatias verticais para contornar o limite do Tesseract...")
    
    while y_atual < h_img:
        y_fim_fatia = min(y_atual + tamanho_fatia, h_img)
        print(f" -> Analisando faixa vertical: de {y_atual} até {y_fim_fatia} px...")
        
        # Recorta uma fatia temporária apenas para passar pelo OCR
        fatia = img[y_atual:y_fim_fatia, 0:w_img]
        gray_fatia = cv2.cvtColor(fatia, cv2.COLOR_BGR2GRAY)
        
        try:
            dados_ocr = pytesseract.image_to_data(gray_fatia, lang='por', output_type=pytesseract.Output.DICT)
            n_boxes = len(dados_ocr['text'])
            
            for i in range(n_boxes):
                texto = dados_ocr['text'][i].strip().upper()
                if "QUEST" in texto:
                    linha_texto = " ".join([dados_ocr['text'][j] for j in range(max(0, i-1), min(n_boxes, i+3))]).upper()
                    
                    if re.search(r'QUESTÃO\s*\d+|QUESTAO\s*\d+|\d+\s*QUESTÃO', linha_texto):
                        # y_topo_fatia é a posição dentro do pedaço menor
                        y_topo_fatia = dados_ocr['top'][i]
                        # global_y é a posição real convertida para a imagem de 157k pixels
                        global_y = y_atual + y_topo_fatia
                        
                        # Evita duplicados por conta das regiões de sobreposição
                        if not any(abs(global_y - y) < 150 for y in linhas_questoes):
                            linhas_questoes.append(global_y)
        except Exception as e:
            print(f"[AVISO] Falha ao escanear a faixa {y_atual}-{y_fim_fatia}: {e}")
        
        # Avança o ponteiro vertical descontando a área de sobreposição
        if y_fim_fatia == h_img:
            break
        y_atual += (tamanho_fatia - sobreposicao)

    # Ordena todas as coordenadas globais encontradas
    linhas_questoes.sort()
    
    if not linhas_questoes:
        print("[AVISO] Nenhuma marcação de 'Questão' foi identificada no documento.")
        return

    total_questoes = len(linhas_questoes)
    print(f"[OK] Mapeamento concluído! Encontradas {total_questoes} questões no total.")

    # Margens de segurança para o recorte final
    margem_superior = 40
    margem_inferior = 30
    folga_fim_questao = 15

    # Realiza os recortes físicos na imagem original usando o mapa de coordenadas globais
    for index, y_marcado in enumerate(linhas_questoes):
        y_start = max(0, y_marcado - margem_superior)
        
        if index < total_questoes - 1:
            y_end = linhas_questoes[index + 1] - folga_fim_questao
        else:
            y_end = min(h_img, h_img - margem_inferior)
            
        if y_end > y_start:
            recorte = img[y_start:y_end, 0:w_img]
            nome_saida = f"questao_extraida_{index + 1}.jpg"
            caminho_salvamento = os.path.join(pasta_saida, nome_saida)
            
            cv2.imwrite(caminho_salvamento, recorte)
            print(f"  -> [{index + 1}/{total_questoes}] Recorte salvo: {caminho_salvamento}")

    print(f"\n=== Sucesso! Todos os recortes foram salvos em '{pasta_saida}/' ===")


# --- EXECUÇÃO ---
ARQUIVO_CONCATENADO = "colunas_concatenadas_verticalmente.png"
recortar_imagem_gigante(ARQUIVO_CONCATENADO)