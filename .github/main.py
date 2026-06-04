import requests
import time
import os
from datetime import datetime
import pytz

# --- CONFIGURAÇÕES DO SEU ROBÔ ---
API_KEY = "7238b0f8fc6dbc7a18c9d817c34abc53"
TELEGRAM_TOKEN = "8737473531:AAH5gpMkQbiNtm2Ms8ffePck9m_cNJbcE84"
CHAT_ID = "8048641809"

HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

# Arquivo para salvar os IDs dos jogos que já foram enviados
LOG_ENVIADOS = "jogos_enviados.txt"

def carregar_enviados():
    if os.path.exists(LOG_ENVIADOS):
        with open(LOG_ENVIADOS, "r") as f:
            return set(f.read().splitlines())
    return set()

def salvar_enviado(fixture_id):
    with open(LOG_ENVIADOS, "a") as f:
        f.write(f"{fixture_id}\n")

def buscar_odds_pre_jogo(fixture_id, total_gols_atual):
    """Busca as odds iniciais para a linha de gols acima da atual"""
    linha_alvo = f"Over {total_gols_atual + 0.5}"
    url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10).json()
        if response.get('response') and len(response['response']) > 0:
            bookmakers = response['response'][0].get('bookmakers', [])
            for book in bookmakers:
                for bet in book.get('bets', []):
                    if "Goals Over/Under" in bet.get('name', ''):
                        for value in bet.get('values', []):
                            if str(value.get('value')).strip().lower() == linha_alvo.lower():
                                return value.get('odd')
    except Exception as e:
        pass
    return "Disponível na sua casa de aposta"

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        pass

def analisar_estatisticas(fixture_id, home_team, away_team, minuto, gols_casa, gols_fora, enviados):
    if str(fixture_id) in enviados:
        return

    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10).json()
        if not response.get('response') or len(response['response']) < 2:
            return

        stats_casa = {item['type']: item['value'] for item in response['response'][0]['statistics'] if item['value'] is not None}
        stats_fora = {item['type']: item['value'] for item in response['response'][1]['statistics'] if item['value'] is not None}

        # --- CRITÉRIO DE FALTAS ---
        faltas_casa = int(stats_casa.get('Fouls', 0))
        faltas_fora = int(stats_fora.get('Fouls', 0))
        faltas_totais = faltas_casa + faltas_fora

        # FILTRO: Mínimo de 10 faltas no 1T
        if faltas_totais < 10:
            return

        chutes_no_gol_casa = int(stats_casa.get('Shots on Goal', 0))
        chutes_no_gol_fora = int(stats_fora.get('Shots on Goal', 0))
        chutes_fora_casa = int(stats_casa.get('Shots off Goal', 0))
        chutes_fora_fora = int(stats_fora.get('Shots off Goal', 0))
        chutes_totais = chutes_no_gol_casa + chutes_no_gol_fora + chutes_fora_casa + chutes_fora_fora

        posse_casa = stats_casa.get('Ball Possession', "0%")
        posse_fora = stats_fora.get('Ball Possession', "0%")

        # Define dinamicamente o mercado com base nos gols atuais do jogo
        gols_totais = gols_casa + gols_fora
        mercado_alvo = f"Over {gols_totais + 0.5} Gols HT"

        # Puxa a ODD de referência para a linha correta
        odd_referencia = buscar_odds_pre_jogo(fixture_id, gols_totais)

        msg = (
            f"🔥 **ALERTA DE ENTRADA: MAIS GOLS HT** 🔥\n\n"
            f"⚽ **{home_team}** x **{away_team}**\n"
            f"⏱️ Tempo: {minuto}' do 1º Tempo\n"
            f"🔢 Placar Atual: {gols_casa} x {gols_fora}\n\n"
            f"📊 **Scout de Faltas e Intensidade (1T):**\n"
            f"• 💥 **Faltas Totais: {faltas_totais}** (C {faltas_casa} | F {faltas_fora})\n"
            f"• 🎯 Finalizações Totais: {chutes_totais}\n"
            f"• ⏳ Posse de Bola: {posse_casa} | {posse_fora}\n\n"
            f"📈 **Mercado para Entrada:**\n"
            f"• **Entrada:** {mercado_alvo} (Sair mais um gol no 1T)\n"
            f"• **Odd de Referência:** {odd_referencia}\n\n"
            f"🎯 *Estratégia:* Jogo muito faltoso e movimentado no 1º Tempo. Ritmo forte ou alta quantidade de paradas indicam excelente valor para buscar mais um gol antes do intervalo!"
        )
        
        enviar_telegram(msg)
        salvar_enviado(fixture_id)
        time.sleep(2)
        
    except Exception as e:
        pass

def monitorar_jogos_ao_vivo():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hora_atual = datetime.now(fuso_br).hour
    
    if hora_atual < 10 or hora_atual >= 23:
        return

    enviados = carregar_enviados()
    url_live = "https://v3.football.api-sports.io/fixtures?live=all"
    try:
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()
        jogos = response.get('response', [])
        for jogo in jogos:
            minuto = jogo['fixture']['status']['elapsed'] or 0
            gols_casa = jogo['goals']['home'] if jogo['goals']['home'] is not None else 0
            gols_fora = jogo['goals']['away'] if jogo['goals']['away'] is not None else 0
            
            # Janela de análise: 1º Tempo entre 20 e 30 minutos (QUALQUER PLACAR)
            if 20 <= minuto <= 30:
                analisar_estatisticas(
                    jogo['fixture']['id'], 
                    jogo['teams']['home']['name'], 
                    jogo['teams']['away']['name'], 
                    minuto, 
                    gols_casa, 
                    gols_fora,
                    enviados
                )
    except Exception as e:
        pass

if __name__ == "__main__":
    monitorar_jogos_ao_vivo()
