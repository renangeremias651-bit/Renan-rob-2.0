import requests
import time
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

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar telegram: {e}")

def analisar_estatisticas(fixture_id, home_team, away_team, minuto, gols_casa, gols_fora):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10).json()
        if not response.get('response') or len(response['response']) < 2:
            return

        stats_casa = {item['type']: item['value'] for item in response['response'][0]['statistics']}
        stats_fora = {item['type']: item['value'] for item in response['response'][1]['statistics']}

        # --- CRITÉRIO DE FALTAS ---
        faltas_casa = stats_casa.get('Fouls') or 0
        faltas_fora = stats_fora.get('Fouls') or 0
        faltas_totais = faltas_casa + faltas_fora

        # FILTRO: Mínimo de 10 faltas no 1T para disparar o alerta
        if faltas_totais < 10:
            print(f"Jogo {home_team} x {away_team} ignorado. Poucas faltas ({faltas_totais}).")
            return

        chutes_no_gol_casa = stats_casa.get('Shots on Goal') or 0
        chutes_no_gol_fora = stats_fora.get('Shots on Goal') or 0
        chutes_fora_casa = stats_casa.get('Shots off Goal') or 0
        chutes_fora_fora = stats_fora.get('Shots off Goal') or 0
        chutes_totais = chutes_no_gol_casa + chutes_no_gol_fora + chutes_fora_casa + chutes_fora_fora

        posse_casa = stats_casa.get('Ball Possession') or "0%"
        posse_fora = stats_fora.get('Ball Possession') or "0%"

        msg = (
            f"🔥 **ALERTA DE ESTRATÉGIA: OVER 0.5 GOLS HT** 🔥\n\n"
            f"⚽ **{home_team}** x **{away_team}**\n"
            f"⏱️ Tempo: {minuto}' do 1º Tempo\n"
            f"🔢 Placar: {gols_casa} x {gols_fora}\n\n"
            f"📊 **Scout de Faltas e Intensidade (1T):**\n"
            f"• 💥 **Faltas Totais: {faltas_totais}** (C {faltas_casa} | F {faltas_fora})\n"
            f"• 🎯 Finalizações Totais: {chutes_totais}\n"
            f"• ⏳ Posse de Bola: {posse_casa} | {posse_fora}\n\n"
            f"🎯 *Estratégia:* Jogo muito faltoso no 1º Tempo com placar zerado. Buscar o **Over 0.5 Gols HT** aproveitando o cenário de bola parada e tendência de acréscimos longos!"
        )
        enviar_telegram(msg)
        time.sleep(2)
    except Exception as e:
        print(f"Erro na análise: {e}")

def monitorar_jogos_ao_vivo():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hora_atual = datetime.now(fuso_br).hour
    
    if hora_atual < 10 or hora_atual >= 23:
        print("Fora do horário comercial. Economizando API.")
        return

    url_live = "https://v3.football.api-sports.io/fixtures?live=all"
    try:
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()
        jogos = response.get('response', [])
        for jogo in jogos:
            minuto = jogo['fixture']['status']['elapsed'] or 0
            gols_casa = jogo['goals']['home'] or 0
            gols_fora = jogo['goals']['away'] or 0
            
            # Janela de análise: 1º Tempo entre 20 e 30 minutos e placar 0x0
            if 20 <= minuto <= 30 and gols_casa == 0 and gols_fora == 0:
                analisar_estatisticas(
                    jogo['fixture']['id'], 
                    jogo['teams']['home']['name'], 
                    jogo['teams']['away']['name'], 
                    minuto, 
                    gols_casa, 
                    gols_fora
                )
    except Exception as e:
        print(f"Erro no monitoramento: {e}")

if __name__ == "__main__":
    monitorar_jogos_ao_vivo()
