
import pandas as pd
import os
from IPython.display import display

empresas = ["ABEV3", "AZUL4", "BTOW3", "B3SA3", "BBSE3", "BRML3", "BBDC4", "BRAP4", "BBAS3", "BRKM5", "BRFS3", "BPAC11", "CRFB3", "CCRO3", "CMIG4", "HGTX3", "CIEL3", "COGN3", "CPLE6", "CSAN3", "CPFE3", "CVCB3", "CYRE3", "ECOR3", "ELET6", "EMBR3", "ENBR3", "ENGI11", "ENEV3", "EGIE3", "EQTL3", "EZTC3", "FLRY3", "GGBR4", "GOAU4", "GOLL4", "NTCO3", "HAPV3", "HYPE3", "IGTA3", "GNDI3", "ITSA4", "ITUB4", "JBSS3", "JHSF3", "KLBN11", "RENT3", "LCAM3", "LAME4", "LREN3", "MGLU3", "MRFG3", "BEEF3", "MRVE3", "MULT3", "PCAR3", "PETR4", "BRDT3", "PRIO3", "QUAL3", "RADL3", "RAIL3", "SBSP3", "SANB11", "CSNA3", "SULA11", "SUZB3", "TAEE11", "VIVT3", "TIMS3", "TOTS3", "UGPA3", "USIM5", "VALE3", "VVAR3", "WEGE3", "YDUQ3"]

#fundamentos = {
#Referencia = armazenar balaços dentro de um dicionario a chave é o código o valor é o dataFrame a tabela
#"ABEV3": balanco_dre_abev3,
#"MGLU3": balanco_dre_mgLu3
#}

fundamentos = {}
arquivos = os.listdir("Balancos")

for arquivo in arquivos:
    nome = arquivo[-9:-4]
    if "11" in nome:
        #ler o nome do arquivo
        nome = arquivo[-10:-4]
    if nome in empresas:
        print(nome)
        # pegar um arquivo do balanco
        balanco = pd.read_excel(f'Balancos/{arquivo}', sheet_name=0)
        # na primeira coluna colocar o titulo com o nome da empresa
        balanco.iloc[0, 0] = nome
        # pegar primeira linha e tornar cabeçalho
        balanco.columns = balanco.iloc[0]
        balanco = balanco[1:]
        # Tornar a primeira coluna que agora tem o nome da empresa indice da tabela
        balanco = balanco.set_index(nome)

        dre = pd.read_excel(f'Balancos/{arquivo}', sheet_name=1)
         # na primeira coluna colocar o titulo com o nome da empresa
        dre.iloc[0, 0] = nome
        # pegar primeira linha e tornar cabeçalho
        dre.columns = dre.iloc[0]
        dre = dre[1:]
        # Tornar a primeira coluna que agora tem o nome da empresa indice da tabela
        dre = dre.set_index(nome)
        fundamentos[nome] = pd.concat([balanco, dre], axis=0)


# ### Pegar Preços das Ações nas Datas Correspondentes

cotacoes_df = pd.read_excel('Cotacoes.xlsx')
cotacoes = {}
for empresa in cotacoes_df["Empresa"].unique():
    cotacoes[empresa] = cotacoes_df.loc[cotacoes_df["Empresa"]==empresa, :]

print(len(cotacoes))


# ### Remover empresas que tem cotações vazias da análise (mesmo após o tratamento que fizemos na hora de pegar as cotações)

for empresa in empresas:
    if cotacoes[empresa].isnull().values.any():
        cotacoes.pop(empresa)
        fundamentos.pop(empresa, None)
empresas = list(cotacoes.keys())
print(len(empresas))


# ### Juntar fundamentos com Preço da Ação

# no cotacoes: jogar as datas para índice
# no fundamnetos:
    # trocar linhas por colunas
    # tratar as datas para formato de data do python
    # juntar os fundamentos com a coluna Adj Close das cotacoes
for empresa in fundamentos:
    tabela = fundamentos[empresa].T
    tabela.index = pd.to_datetime(tabela.index, format="%d/%m/%Y")
    tabela_cotacao = cotacoes[empresa].set_index("Date")
    tabela_cotacao = tabela_cotacao[["Adj Close"]]
    
    tabela = tabela.merge(tabela_cotacao, right_index=True, left_index=True)
    tabela.index.name = empresa
    fundamentos[empresa] = tabela
display(fundamentos["ABEV3"])


# ### Tratar colunas
#     
# 1. Vamos pegar apenas empresas que possuem as mesmas colunas
# 2. Ajeitar colunas com nome repetido
# 3. Analisar valores vazios nas colunas

# #### 1. Remover da análise colunas que não existem em alguma tabela

colunas = list(fundamentos["ABEV3"].columns)

for empresa in empresas:
    if set(colunas) != set(fundamentos[empresa].columns):
        fundamentos.pop(empresa)
print(len(fundamentos))


# ####  2. Ajeitando colunas com o mesmo nome

texto_colunas = ";".join(colunas)

colunas_modificadas = []
for coluna in colunas:
    if colunas.count(coluna) == 2 and coluna not in colunas_modificadas:
        texto_colunas = texto_colunas.replace(";" + coluna + ";", ";" + coluna + "_1;",1)
        colunas_modificadas.append(coluna)
colunas = texto_colunas.split(";")
print(colunas)

# implementar as colunas nas tabelas
for empresa in fundamentos:
    fundamentos[empresa].columns = colunas


# #### 3. Analisar valores vazios nas colunas

valores_vazios = dict.fromkeys(colunas,0)
total_linhas = 0

for empresa in fundamentos:
    tabela = fundamentos[empresa]
    total_linhas += tabela.shape[0]
    for coluna in colunas:
        qtd_vazio = pd.isnull(tabela[coluna]).sum()
        valores_vazios[coluna] += qtd_vazio
print(valores_vazios)
print(total_linhas)

remover_colunas = []

for coluna in valores_vazios:
    if valores_vazios[coluna] > 50:
        remover_colunas.append(coluna)
for empresa in fundamentos:
    fundamentos[empresa] = fundamentos[empresa].drop(remover_colunas,axis=1)
    fundamentos[empresa] = fundamentos[empresa].ffill()
       

fundamentos["ABEV3"].shape


# ### Criando os rótulos: Comprar, Não Comprar ou Vender?
# 
# Não queremos saber quando vender, mas inclui essa categoria para conseguir identificar quando que o nosso modelo vai sugerir uma compra quando na verdade o melhor momento era vender. Isso significa que o modelo errou "mais" do que quando sugeriu comprar e simplesmente o certo era não comprar
# 
# Regra: 
# 1. Subiu mais do que o Ibovespa (ou caiu menos) -> Comprar (Valor = 2)
# 2. Subiu menos do que o Ibovespa até Ibovespa - 2% (ou caiu mais do que Ibovespa até Ibovespa -2%) -> Não Comprar (Valor = 1)
# 3. Subiu menos do que o Ibovespa - 2% (ou caiu mais do que Ibovespa -2%) -> Vender (Valor = 0)

data_inicial = '2012-12-20'
data_final = '2021-04-20'

from pandas_datareader import data as pdr
import yfinance as yfin
yfin.pdr_override()

df_ibov = pdr.get_data_yahoo("^BVSP", start=data_inicial, end=data_final)

#df_ibov = web.DataReader('^BVSP', data_source='yahoo', start=data_inicial, end=data_final)

import numpy as np

datas = fundamentos["ABEV3"].index
for data in datas:
    if data not in df_ibov.index:
        df_ibov.loc[data] = np.nan
df_ibov = df_ibov.sort_index()
df_ibov = df_ibov.ffill()
df_ibov = df_ibov.rename(columns={"Adj Close": "IBOV"})
for empresa in fundamentos:
    fundamentos[empresa] = fundamentos[empresa].merge(df_ibov[["IBOV"]], left_index=True, right_index=True)
display(fundamentos["ABEV3"])
    

# tornar os nossos indicadores em percentuais 
# fundamentos%tri = fundamento tr / fundamento tri anterior
# cotacao%tri = cotacao tri seguinte / contacao tri

for empresa in fundamentos:
    fundamento = fundamentos[empresa]
    fundamento = fundamento.sort_index()
    for coluna in fundamento:
        if "Adj Close" in coluna or "IBOV" in coluna:
            pass
        else:
            # pegar cotação anterior
            condicoes = [
                (fundamento[coluna].shift(1) > 0) & (fundamento[coluna] < 0),
                (fundamento[coluna].shift(1) < 0) & (fundamento[coluna] > 0),
                (fundamento[coluna].shift(1) < 0) & (fundamento[coluna] < 0),
                (fundamento[coluna].shift(1) == 0) & (fundamento[coluna] > 0),
                (fundamento[coluna].shift(1) == 0) & (fundamento[coluna] < 0),
                (fundamento[coluna].shift(1) < 0) & (fundamento[coluna] == 0),
            ]
            valores = [
                -1,
                1,
                (abs(fundamento[coluna].shift(1)) - abs(fundamento[coluna])) / abs(fundamento[coluna].shift(1)),
                1,
                -1,
                1,          
            ]
            fundamento[coluna] = np.select(condicoes,valores, default=fundamento[coluna] / fundamento[coluna].shift(1))
    #Pegar cotação seguinte
    fundamento["Adj Close"] = fundamento["Adj Close"].shift(-1) / fundamento["Adj Close"] - 1
    fundamento["IBOV"] = fundamento["IBOV"].shift(-1) / fundamento["IBOV"] - 1
    fundamento["Resultado"] = fundamento["Adj Close"] - fundamento["IBOV"]
    condicoes = [
        (fundamento["Resultado"] > 0),
        (fundamento["Resultado"] < 0) & (fundamento["Resultado"] >= -0.02),
        (fundamento["Resultado"] < -0.02)
    ]
    valores= [2,1,0]
    fundamento["Decisao"] = np.select(condicoes,valores)
    
    fundamentos[empresa] = fundamento
display(fundamentos["ABEV3"]).columns

# Remover os valores vazios
colunas = list(fundamentos["ABEV3"].columns)
valores_vazios = dict.fromkeys(colunas,0)
total_linhas = 0

for empresa in fundamentos:
    tabela = fundamentos[empresa]
    total_linhas += tabela.shape[0]
    for coluna in colunas:
        qtd_vazio = pd.isnull(tabela[coluna]).sum()
        valores_vazios[coluna] += qtd_vazio
print(valores_vazios)
print(total_linhas)

remover_colunas = []

for coluna in valores_vazios:
    if valores_vazios[coluna] > (total_linhas / 3):
        remover_colunas.append(coluna)
        
for empresa in fundamentos:
    fundamentos[empresa] = fundamentos[empresa].drop(remover_colunas,axis=1)
    fundamentos[empresa] = fundamentos[empresa].fillna(0)

for empresa in fundamentos:
    fundamentos[empresa] = fundamentos[empresa].drop(["Adj Close", "IBOV", "Resultado"], axis=1)
print(fundamentos["ABEV3"].shape)


# ### Hora de tornar tudo 1 dataframe só

copia_fundamentos = fundamentos.copy()


base_dados = pd.DataFrame()
for empresa in copia_fundamentos:
    copia_fundamentos[empresa] = copia_fundamentos[empresa][1:-1]
    copia_fundamentos[empresa] = copia_fundamentos[empresa].reset_index(drop=True)
    base_dados = base_dados.append(copia_fundamentos[empresa])
display(base_dados)


# ### Análise Exploratória

# #### 1. Quantidade de Respostas em cada Tipo de Decisão

import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

display(base_dados['Decisao'].value_counts(normalize=True).map("{:.1%}".format))
fig = px.histogram(base_dados, x="Decisao", color="Decisao")
fig.show()

# vou tirar a categoria 1 e transformar em 0
base_dados.loc[base_dados["Decisao"]==1, "Decisao"] = 0
display(base_dados['Decisao'].value_counts(normalize=True).map("{:.1%}".format))
fig = px.histogram(base_dados, x="Decisao", color="Decisao")
fig.show()


# #### 2. Correlação

# #### Vamos remover Todas as Colunas "já explicadas" pelo Ativo Total

correlacoes = base_dados.corr()

fig, ax = plt.subplots(figsize=(15, 10))
sns.heatmap(correlacoes, cmap="Wistia", ax=ax)
plt.show()
display(correlacoes)

correlacoes_encontradas = []
for coluna in correlacoes:
    for linha in correlacoes.index:
        if linha != coluna:
            valor = abs(correlacoes.loc[linha, coluna])
            if valor > 0.8 and (coluna, linha, valor) not in correlacoes_encontradas:
                correlacoes_encontradas.append((linha, coluna, valor))
                print(f"Correlação Encontrada: {linha} e {coluna}. Valor: {valor}")

remover = ['Ativo Circulante', 'Contas a Receber_1', 'Tributos a Recuperar', 'Passivo Total', 'Passivo Circulante', 'Patrimônio Líquido', 'Capital Social Realizado', 'Receita Líquida de Vendas e/ou Serviços', 'Resultado Bruto', 'Despesas Gerais e Administrativas']
base_dados = base_dados.drop(remover, axis=1)
print(base_dados.shape)


# ### Vamos partir para Feature Selection
# 
# Será que todas essas features são importantes mesmo para o nosso modelo? Muitas features nem sempre é bom, se pudermos reduzir sem perder eficiência do nosso modelo, melhor
# 
# Aqui temos 2 alternativas:
# 
# 1. Seguir com todas as features e depois tentar melhorar o nosso modelo
# 2. Usar algum critério para selecionar as melhores features para prever e criar o modelo a partir apenas dessa seleção menor de features
# 
# Vou seguir com a opção 2, porque é mais rápida e, caso dê certo, facilita a nossa vida. Se der errado, a gente volta aqui e refaz o processo

display(base_dados)

# vamos treinar uma arvore de decisao e pegar as caracteristicas mais importantes dela

from sklearn.ensemble import ExtraTreesClassifier

modelo = ExtraTreesClassifier(random_state=1)
x = base_dados.drop("Decisao", axis=1)
y = base_dados["Decisao"]
modelo.fit(x, y)

caracteristicas_importantes = pd.DataFrame(modelo.feature_importances_, x.columns).sort_values(by=0, ascending=False)
display(caracteristicas_importantes)
top10 = list(caracteristicas_importantes.index)[:10]
print(top10)

# ### Aplicação do StandardScaler para melhorar nossos modelos de MachineLearning

from sklearn.preprocessing import StandardScaler

def ajustar_scaler(tabela_original):
    scaler = StandardScaler()
    tabela_auxiliar = tabela_original.drop("Decisao", axis=1)
    
    tabela_auxiliar = pd.DataFrame(scaler.fit_transform(tabela_auxiliar),tabela_auxiliar.index,tabela_auxiliar.columns)
    tabela_auxiliar["Decisao"] = tabela_original["Decisao"]
    return tabela_auxiliar

nova_base_dados = ajustar_scaler(base_dados)
top10.append("Decisao")
nova_base_dados = nova_base_dados[top10].reset_index(drop=True)
display(nova_base_dados)


# ### Separação dos dados em treino e teste

from sklearn.model_selection import train_test_split

x = nova_base_dados.drop("Decisao", axis=1)
y = nova_base_dados["Decisao"]

x_treino, x_teste, y_treino,y_teste = train_test_split(x,y,random_state=1)


# ### Criação de um Dummy Classifier (Uma baseline para ver se os nossos modelos são melhores do que puro chute)

from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report,confusion_matrix

dummy = DummyClassifier(strategy="stratified",random_state=2)
dummy.fit(x_treino,y_treino)
previsao_dummy = dummy.predict(x_teste)


# ### Métricas de Avaliação
# 
# - Precisão vai ser nossa métrica principal
# - Recall pode ser útil, mas precisão no caso de ações é mt mais importante.
# 
# Explicação: Foto dos Gatos e Cachorros na Wikipedia: https://en.wikipedia.org/wiki/Precision_and_recall


def avaliar(y_teste, previsoes, nome_modelo):
    print(nome_modelo)
    report = classification_report(y_teste,previsoes)
    print(report)
    cf_matrix = pd.DataFrame(confusion_matrix(y_teste,previsoes), index=["Vender","Comprar"] , columns=["Vender","Comprar"])
    sns.heatmap(cf_matrix, annot=True, cmap="Blues", fmt=",")
    plt.show()
    print("#" * 50)
avaliar(y_teste,previsao_dummy, "Dummy")


# ### Modelos que vamos testar
# - AdaBoost
# - Decision Tree
# - Random Forest
# - ExtraTree
# - Gradient Boost
# - K Nearest Neighbors (KNN)
# - Logistic Regression
# - Naive Bayes
# - Support Vector Machine (SVM)
# - Rede Neural

# In[59]:


from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier

modelos = {
    
"AdaBoost": AdaBoostClassifier(random_state=1),
"DecisionTree": DecisionTreeClassifier(random_state=1),
"RandomForest": RandomForestClassifier(random_state=1),
"ExtraTree": ExtraTreesClassifier(random_state=1),
"GradientBoost": GradientBoostingClassifier(random_state=1),
"KNN": KNeighborsClassifier(),
"LogisticRegression": LogisticRegression(random_state=1),
"NaiveBayes": GaussianNB(),
"SVM": SVC(random_state=1),
"RedeNeural": MLPClassifier(random_state=1, max_iter=400),
}

for nome_modelo in modelos:
    modelo = modelos[nome_modelo]
    modelo.fit(x_treino,y_treino)
    previsoes = modelo.predict(x_teste)
    avaliar(y_teste,previsoes,nome_modelo)
    modelos[nome_modelo] = modelo


# ### Agora vamos ao tunning do modelo
# 
# - é bom sempre incluir no tuning os parâmetros "padrões" do modelo, se não poder ser que vc só encontre resultados piores

from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer, precision_score

modelo_final = modelos["RandomForest"]

n_estimators = range(10, 251, 30)
max_features = list(range(2,11,2))
max_features.append('auto')
min_samples_split = range(2,11,2)

precision2_score = make_scorer(precision_score,labels=[2], avarege='macro')
grid = GridSearchCV(
            estimator=RandomForestClassifier(),
            param_grid={
                'n_estimators': n_estimators,
                'max_features': max_features,
                'min_samples_split': min_samples_split,
                'random_state': [1],
            },
            scoring=precision2_score,
)

resultado_grid = grid.fit(x_treino, y_treino)
print("Ajuste Feito")

