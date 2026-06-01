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

def analisar_estatisticas(fixture_id, home_team, away_team, minuto, gols_casa, gols_fora, nome_tempo):
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
        
        minuto_exibicao = minuto if nome_tempo == "1º Tempo" else (minuto - 45)

        msg = (
            f"🚨 **ALERTA DE ENTRADA: MAIS 2 CANTOS** 🚨\n\n"
            f"⚽ **{home_team}** x **{away_team}**\n"
            f"⏱️ Tempo: {minuto_exibicao}' do {nome_tempo} (Minuto Corrido: {minuto}')\n"
            f"🔢 Placar: {gols_casa} x {gols_fora}\n\n"
            f"📊 **Scout de Pressão:**\n"
            f"• Escanteios Totais: {escanteios_totais} (C {escanteios_casa} | F {escanteios_fora})\n"
            f"• Chutes Totais: {chutes_totais}\n"
            f"• Posse de Bola: {posse_casa} | {posse_fora}\n\n"
            f"🎯 *Estratégia:* Minuto ideal encontrado! Buscar +2 cantos no tempo atual."
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

    # --- MENSAGEM TESTE DE CONEXÃO ---
    print("Enviando mensagem de teste de conexão para o Telegram...")
    enviar_telegram("🤖 *Robô Atualizado com Sucesso!*\n\nA conexão está funcionando e o monitoramento inteligente por minutos corridos foi ativado.")

    url_live = "https://v3.football.api-sports.io/fixtures?live=all"
    try:
        response = requests.get(url_live, headers=HEADERS, timeout=15).json()
        jogos = response.get('response', [])
        for jogo in jogos:
            minuto = jogo['fixture']['status']['elapsed'] or 0
            
            valido = False
            nome_tempo = ""

            # Janela normal do seu método + Janela estendida (70 a 80) apenas para testar o jogo de agora!
            if 23 <= minuto <= 27:
                valido = True
                nome_tempo = "1º Tempo"
            elif 68 <= minuto <= 80: # Aumentei até 80 para pegar o seu jogo atual no teste
                valido = True
                nome_tempo = "2º Tempo"

            if valido:
                analisar_estatisticas(
                    jogo['fixture']['id'], 
                    jogo['teams']['home']['name'], 
                    jogo['teams']['away']['name'], 
                    minuto, 
                    jogo['goals']['home'] or 0, 
                    jogo['goals']['away'] or 0, 
                    nome_tempo
                )
    except Exception as e:
        print(f"Erro no monitoramento: {e}")

if __name__ == "__main__":
    monitorar_jogos_ao_vivo()
