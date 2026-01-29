import pandas as pd
import json
import os
import logging
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class ClassificationResponse(BaseModel):
    codigo_escolhido: str = Field(..., description="O código numérico da opção escolhida")

class NoHierarquico:
    """Representa um nó na árvore de hierarquia de mercadorias."""
    def __init__(self, codigo, descricao, nivel):
        self.codigo = codigo
        self.descricao = descricao
        self.nivel = nivel
        self.filhos = {}  # Dicionário {codigo_filho: NoHierarquico}

    def adicionar_filho(self, no_filho):
        self.filhos[no_filho.codigo] = no_filho
        
    def eh_folha(self):
        return len(self.filhos) == 0

    def __repr__(self):
        return f"[{self.codigo}] {self.descricao}"

class ClassificadorHierarquicoOpenRouter:
    def __init__(self, api_key, model="openai/gpt-4o-mini", site_url="http://localhost", app_name="ClassificadorHierarquico"):
        self.raiz = NoHierarquico("ROOT", "Raiz", 0)
        self.mapa_nos = {} 
        self.model = model
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": site_url,
                "X-Title": app_name,
            }
        )
        
        self.col_map = {
            'GrpMercads.': 'codigo_grupo',
            'Descrição GrpMercadoria': 'descricao_grupo',
            'Material': 'codigo_material',
            'Texto - pt': 'descritivo',
            'Texto': 'descritivo',
            'Grupo de mercadorias': 'codigo_grupo',
            'GRMP': 'codigo_grupo'
        }

    def carregar_hierarquia(self, arquivo_grupos):
        logger.info(f"Carregando hierarquia de {arquivo_grupos}...")
        try:
            df = pd.read_excel(arquivo_grupos).dropna()
            df.rename(columns=self.col_map, inplace=True)
            
            df['codigo_grupo'] = df['codigo_grupo'].astype(str).apply(
                lambda x: '0' + x if len(x) % 2 != 0 else x
            )
            
            df['len'] = df['codigo_grupo'].apply(len)
            df = df.sort_values('len')
            
            for _, row in df.iterrows():
                codigo = row['codigo_grupo']
                descricao = row['descricao_grupo']
                nivel = len(codigo)
                
                novo_no = NoHierarquico(codigo, descricao, nivel)
                self.mapa_nos[codigo] = novo_no
                
                if nivel == 2:
                    self.raiz.adicionar_filho(novo_no)
                else:
                    codigo_pai = codigo[:-2]
                    if codigo_pai in self.mapa_nos:
                        pai = self.mapa_nos[codigo_pai]
                        pai.adicionar_filho(novo_no)
                        
            logger.info(f"Hierarquia montada. Total de nós: {len(self.mapa_nos)}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar hierarquia: {e}")
            raise

    def _construir_prompt(self, descritivo, opcoes):
        lista_opcoes = "\n".join([f"- {no.codigo}: {no.descricao}" for no in opcoes])
        
        prompt = f"""
Você é um classificador especialista de materiais industriais.
Analise o ITEM abaixo e escolha a categoria que melhor o descreve dentre as OPÇÕES fornecidas.

ITEM: "{descritivo}"

OPÇÕES DO NÍVEL ATUAL:
{lista_opcoes}

INSTRUÇÕES:
1. Escolha apenas UMA opção da lista acima.
2. Responda estritamente no formato JSON.
3. Retorne APENAS o código numérico no campo "codigo_escolhido".

Formato Obrigatório:
{{
  "codigo_escolhido": "CÓDIGO_NUMÉRICO"
}}
"""
        return prompt

    def _chamar_llm(self, prompt):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Responda sempre em JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"} # Tentativa de JSON mode
            )
            content = response.choices[0].message.content
            
            if "```" in content:
                content = content.replace("```json", "").replace("```", "").strip()
            
            # Validação Pydantic
            try:
                dados = json.loads(content)
                modelo = ClassificationResponse(**dados)
                return modelo.codigo_escolhido
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Erro de validação Pydantic: {e}")
                # Tentativa de fallback/limpeza manual se pydantic falhar (ex: string suja)
                return None
                
        except Exception as e:
            logger.error(f"Erro na chamada OpenRouter: {e}")
            return None

    def classificar_item(self, descritivo):
        """Navega na árvore usando o LLM para decidir cada passo (Generator)."""
        no_atual = self.raiz
        caminho = []
        
        logger.info(f"Classificando: {descritivo[:40]}...")
        
        while not no_atual.eh_folha():
            opcoes = list(no_atual.filhos.values())
            
            if not opcoes:
                break

            if len(opcoes) == 1:
                no_atual = opcoes[0]
                step_data = (no_atual.codigo, no_atual.descricao)
                caminho.append(step_data)
                yield {"type": "step", "data": {"codigo": no_atual.codigo, "descricao": no_atual.descricao, "auto": True}}
                continue
            
            prompt = self._construir_prompt(descritivo, opcoes)
            codigo_escolhido = self._chamar_llm(prompt)
            
            if not codigo_escolhido:
                logger.warning(f"Falha na decisão do nível {no_atual.codigo}")
                break
                
            # Limpeza extra se necessário
            escolha = str(codigo_escolhido).strip()
            if escolha not in no_atual.filhos:
                 escolha_limpa = escolha.split(' ')[0].split(':')[0].strip()
                 if escolha_limpa in no_atual.filhos:
                     escolha = escolha_limpa
            
            if escolha in no_atual.filhos:
                no_escolhido = no_atual.filhos[escolha]
                step_data = (no_escolhido.codigo, no_escolhido.descricao)
                caminho.append(step_data)
                
                yield {"type": "step", "data": {"codigo": no_escolhido.codigo, "descricao": no_escolhido.descricao, "auto": False}}
                
                no_atual = no_escolhido
            else:
                logger.warning(f"Alucinação: Código '{escolha}' inválido para nó pai {no_atual.codigo}")
                break
                
        final_result = {
            'codigo_final': no_atual.codigo,
            'descricao_final': no_atual.descricao,
            'caminho': caminho
        }
        
        yield {"type": "final", "data": final_result}

if __name__ == "__main__":
    # Teste rápido se executado diretamente
    # Obtenha sua chave em: [https://openrouter.ai/keys](https://openrouter.ai/keys)
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or "insira-sua-chave-aqui"
    
    clf = ClassificadorHierarquicoOpenRouter(
        api_key=OPENROUTER_API_KEY,
        model="x-ai/grok-4.1-fast" 
    )
    
    arquivo_grp = "data/grpms.xlsx"
    if os.path.exists(arquivo_grp):
        clf.carregar_hierarquia(arquivo_grp)
        item_teste = "Luva de segurança de vaqueta"
        print(f"Classificando: {item_teste}")
        
        # Iterar sobre o gerador
        for evento in clf.classificar_item(item_teste):
            if evento["type"] == "step":
                dados = evento["data"]
                print(f"⬇ [{dados['codigo']}] {dados['descricao']}")
            elif evento["type"] == "final":
                res = evento["data"]
                print(f"\nResultado Final: {res['codigo_final']} - {res['descricao_final']}")
    else:
        print("Arquivo de dados não encontrado")