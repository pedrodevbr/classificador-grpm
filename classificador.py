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
2. Se NENHUMA opção parecer correta para o item, responda com "NULL".
3. Responda estritamente no formato JSON.
4. Retorne APENAS o código numérico no campo "codigo_escolhido" (ou "NULL").

Formato Obrigatório:
{{
  "codigo_escolhido": "CÓDIGO_NUMÉRICO_OU_NULL"
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
        """Inicia a classificação recursiva com backtracking."""
        logger.info(f"Classificando: {descritivo[:40]}...")
        caminho_final = []
        
        # Gerador que delega para o método recursivo
        yield from self._navegar_recursivo(self.raiz, descritivo, caminho_final)
        
        if not caminho_final:
             # Se falhar desde a raiz (não deveria acontecer se houver opções)
             caminho_final = [] 

        # O último nó do caminho é o resultado
        if caminho_final:
            codigo_final, descricao_final = caminho_final[-1]
        else:
             # Fallback total
             codigo_final = self.raiz.codigo
             descricao_final = self.raiz.descricao

        yield {
            "type": "final", 
            "data": {
                'codigo_final': codigo_final,
                'descricao_final': descricao_final,
                'caminho': caminho_final
            }
        }

    def _navegar_recursivo(self, no_atual, descritivo, caminho_historico):
        """
        Método recursivo que tenta encontrar uma folha válida a partir de no_atual.
        Retorna True se encontrou um caminho válido até uma folha (ou aceitou o nó atual).
        Retorna False se este ramo falhou (backtracking).
        """
        
        # 1. Se é folha, sucesso
        if no_atual.eh_folha():
            return True

        opcoes = list(no_atual.filhos.values())
        if not opcoes:
            return True

        # Se só tem uma opção, descemos direto sem perguntar ao LLM (atalho)
        if len(opcoes) == 1:
            filho = opcoes[0]
            step_data = (filho.codigo, filho.descricao)
            caminho_historico.append(step_data)
            yield {"type": "step", "data": {"codigo": filho.codigo, "descricao": filho.descricao, "auto": True}}
            
            if (yield from self._navegar_recursivo(filho, descritivo, caminho_historico)):
                return True
            else:
                # Se o único filho falhar, então este nó também falha
                caminho_historico.pop()
                return False

        # Loop de tentativas para escolha entre múltiplos filhos
        opcoes_candidatas = opcoes.copy()
        
        while opcoes_candidatas:
            # Pergunta ao LLM qual o melhor entre os candidatos atuais
            prompt = self._construir_prompt(descritivo, opcoes_candidatas)
            codigo_escolhido = self._chamar_llm(prompt)
            
            # Se LLM não escolheu nada válido ou retornou nulo (opção de rejeição)
            if not codigo_escolhido:
                logger.info(f"LLM não escolheu nada em {no_atual.codigo} ou indicou rejeição.")
                yield {"type": "info", "data": {"msg": f"Nenhuma opção adequada em {no_atual.descricao}. Voltando..."}}
                return False # Backtrack para o pai escolher outro ramo (se houver)

            # Valida codigo retornado
            escolha = str(codigo_escolhido).strip()
            # Tenta limpar sufixos comuns
            if escolha not in [o.codigo for o in opcoes_candidatas]:
                 escolha_limpa = escolha.split(' ')[0].split(':')[0].strip()
                 if escolha_limpa in [o.codigo for o in opcoes_candidatas]:
                     escolha = escolha_limpa
            
            # Encontra o objeto nó correspondente
            no_escolhido = next((o for o in opcoes_candidatas if o.codigo == escolha), None)
            
            if no_escolhido:
                # Tenta descer neste ramo
                step_data = (no_escolhido.codigo, no_escolhido.descricao)
                caminho_historico.append(step_data)
                
                yield {"type": "step", "data": {"codigo": no_escolhido.codigo, "descricao": no_escolhido.descricao, "auto": False}}
                
                # RECURSÃO: Tenta descer a partir do escolhido
                if (yield from self._navegar_recursivo(no_escolhido, descritivo, caminho_historico)):
                    return True # Sucesso lá embaixo, propaga True pra cima
                else:
                    # FALHA LÁ EMBAIXO -> BACKTRACKING
                    # O ramo escolhido não deu certo (chegou num beco sem saída ou foi rejeitado)
                    logger.info(f"Backtracking: Ramo {no_escolhido.codigo} rejeitado, tentando outro irmão.")
                    caminho_historico.pop() # Remove do histórico
                    opcoes_candidatas.remove(no_escolhido) # Remove das opções pra não escolher de novo
                    yield {"type": "backtrack", "data": {"codigo": no_escolhido.codigo, "razao": "Ramo inválido, tentando outra opção..."}}
                    # O loop continua e o LLM será chamado de novo com menos opções
            else:
                logger.warning(f"Alucinação: {escolha} não está nas opções disponíveis.")
                # Se alucinou, removemos a "ideia" errada se possível ou apenas pedimos de novo? 
                # Melhor arriscar pedir de novo. Se for loop infinito, o while cuida (mas ideal ter contador)
                # Simplesmente ignoramos esse ciclo e tentamos de novo (mas se ele repetir, loop infinito)
                # Vamos remover 'nada' da lista não ajuda. Vamos forçar return False para segurança
                return False

        # Se saiu do while, esgotou todas as opções deste nó sem sucesso
        return False

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