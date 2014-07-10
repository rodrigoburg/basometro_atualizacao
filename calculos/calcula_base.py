import csv
from pandas import DataFrame

def pega_arquivos():
    props = []
    votos = []
    with open("/Users/rodrigoburgarelli/Documents/Estadão Dados/Basômetro/proposicoes.csv", "r") as prop, open("/Users/rodrigoburgarelli/Documents/Estadão Dados/Basômetro/votos.csv", "r") as voto:
        
        arquivo_prop = csv.reader(prop,delimiter = ";")
        next(arquivo_prop, None)  # ignora o cabeçalho
        for row in arquivo_prop:
            proposicao = {}
            proposicao["codigo"] = row[0]
            proposicao["data"] = row[1]
            proposicao["hora"] = row[2]
            proposicao["orientacao"] = row[3]
            proposicao["tipo"] = row[4]
            proposicao["numero"] = row[5]
            proposicao["ano"] = row[6]
            proposicao["ementa"] = row[7]
            proposicao["resumo"] = row[8]
            props.append(proposicao)

        arquivo_voto = csv.reader(voto,delimiter = ";")
        next(arquivo_voto, None)  # ignora o cabeçalho
        for row in arquivo_voto:
            este_voto = {}
            este_voto["codigo"] = row[0]
            este_voto["politico"] = row[1]
            este_voto["voto"] = row[2]
            este_voto["partido"] = row[3]
            votos.append(este_voto)
    return props,votos

def media(lista):
    return sum(lista) / float(len(lista))
    
def calcula_governismo(props,votos):
    df_votos = DataFrame(votos)
    df_props = DataFrame(props)
    resultado = []
    deputados = []
    for p in props:
        g = 0
        subvotos = df_votos[df_votos["codigo"] == p["codigo"]]
        deputados.append(len(subvotos))
        for v in list(subvotos["voto"]):
            if v.lower() == p["orientacao"].lower():
                g +=1
        resultado.append(g/len(subvotos))

    governismo = media(resultado)
    
    print("Número de votações que bateram: "+str(len(resultado)))
    print("Média de deputados por sessão de votação: "+str(media(deputados)))
    print("Taxa de governismo: "+str(governismo))        

def calcula_deputados(props,votos):
    df_votos = DataFrame(votos)
    df_props = DataFrame(props)
    lista_deputados = []
    for v in votos:
        lista_deputados.append(v["politico"])
    
    lista_deputados = list(set(lista_deputados))
    
    deputados = {}
    
    for d in lista_deputados:
        vota_junto = 0
        vota_contra = 0
        subvotos = df_votos[df_votos["politico"] == d] 
        for v in list(subvotos["codigo"]):
            voto = subvotos[subvotos["codigo"] == v]["voto"].get_values()[0]
            orientacao = df_props[df_props["codigo"] == v]["orientacao"].get_values()[0]
            if voto.lower() == orientacao.lower():
                vota_junto += 1
            else:
                vota_contra += 1
        deputados[d] = {}
        deputados[d]["vota_junto"] = vota_junto 
        deputados[d]["voto_total"] = vota_junto + vota_contra
    
    mais_de_90 = 0
    entre_50_e_90 = 0
    menos_de_50 = 0
    
    for d in deputados.keys():
        deputado = deputados[d]
        governismo = deputado["vota_junto"]/deputado["voto_total"]
        if governismo > 0.9:
            mais_de_90 += 1
        elif governismo > 0.5:
            entre_50_e_90 += 1
        else:
            menos_de_50 +=1
        
    print("Número total de deputados: "+str(len(lista_deputados)))
    print("% que votou + de 90% com o governo: "+str(mais_de_90*100/len(lista_deputados)))
    print("% que votou entre 50% e 90% com o governo: "+str(entre_50_e_90*100/len(lista_deputados)))
    print("% que votou menos de 50% com o governo: "+str(menos_de_50*100/len(lista_deputados)))
    
def faz_analise():
    props,votos = pega_arquivos()
    calcula_governismo(props,votos)
    calcula_deputados(props,votos)
    
    lista_codigos = []
    for v in votos:
        lista_codigos.append(v["codigo"])
    
    lista_codigos_votos = list(set(lista_codigos))

    lista_codigos = []
    for p in props:
        lista_codigos.append(p["codigo"])
    
    lista_codigos_props = list(set(lista_codigos))
    
    for p in lista_codigos:
        if p not in lista_codigos_votos:
            print(p)
    print("******")
    for p in lista_codigos_votos:
        if p not in lista_codigos:
            print(p)
    
faz_analise()