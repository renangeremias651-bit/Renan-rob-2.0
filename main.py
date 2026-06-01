import requests
import time

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

def analisar_estatisticas(fixture_id, home_team, away_team, minuto, gols_casa, gols_fora, tempo):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10).json()
        if not response.get('response') or len(response['response']) < 2:
            return

        stats_casa = {item['type']: item['value'] for item in response['response'][0]['statistics']}
        stats_fora = {item['type']: item['value'] for item in response['response'][1]['statistics']}

        escanteios_casa = stats_casa.get('Corner Kicks') or 0
        escanteios_fora = stats_fora.get('Corner Kicks') or 0
        escanteios_totais = escanteios_casa + escanteios_fora
        
        chutes_no_gol_casa = stats_casa.get('Shots on Goal') or 0
        chutes_no_gol_fora = stats_fora.get('Shots on Goal') or 0
        chutes_fora_casa = stats_casa.get('Shots off Goal') or 0
        chutes_fora_fora = stats_fora.get('Shots off Goal') or 0
        chutes_totais = chutes_no_gol_casa + chutes_no_gol_fora + chutes_fora_casa + chutes_fora_fora

        posse_casa = stats_casa.get('Ball Possession') or "0%"
        posse_fora = stats_fora.get('Ball Possession') or "0%"
        
        nome_tempo = "1º Tempo" if tempo == "1H" else "2º Tempo"

        msg = (
            f"🚨 **ALERTA DE ENTRADA: MAIS 2 CANTOS** 🚨\n\n"
            f"⚽ **{home_team}** x **{away_team}**\n"
            f"⏱️ Tempo: {minuto}' do {nome_tempo}\n"
            f"🔢 Placar: {gols_casa} x {gols_fora}\n\n"
            f"📊 **Scout:**\n"
            f"• Escanteios Totais: {escanteios_totais} (Casa {escanteios_casa} | Fora {escanteios_fora})\n"
            f"• Chutes Totais: {chutes_totais}\n"
            f"• Posse de Bola: {posse_casa} | {posse_fora}\n\n"
            f"🎯 *Estratégia:* Minuto ideal, buscar +2 cantos no tempo atual!"
        )
        enviar_telegram(msg)
        time.sleep(2)
    except Exception as e:
        print(f"Erro na análise: {e}")

def monitorar_jogos_ao_vivo():
    url_live = "https://v3.football.api-sports.io/fixtures?live=all"
    try:
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()
        jogos = response.get('response', [])
        for jogo in jogos:
            status = jogo['fixture']['status']['short']
            minuto = jogo['fixture']['status']['elapsed'] or 0
            # Filtro: 1H ou 2H, minuto entre 23 e 27
            if status in ["1H", "2H"] and (23 <= minuto <= 27):
                analisar_estatisticas(
                    jogo['fixture']['id'], 
                    jogo['teams']['home']['name'], 
                    jogo['teams']['away']['name'], 
                    minuto, 
                    jogo['goals']['home'] or 0, 
                    jogo['goals']['away'] or 0, 
                    status
                )
    except Exception as e:
        print(f"Erro no monitoramento: {e}")

if __name__ == "__main__":
    monitorar_jogos_ao_vivo()
