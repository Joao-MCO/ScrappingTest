# main.py
import sys
import argparse
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from services.logging import configLog
from database.process import process_match
import services.scrapping as scrp
from database.connection import get_session 

configLog()
thread_local = threading.local()
active_drivers = []

def worker_tarefa(jogo):
    """
    Função executada por cada thread. 
    Garante que cada worker tenha o seu próprio navegador e sessão de BD.
    """
    if not hasattr(thread_local, "driver"):
        thread_local.driver = scrp.open_browser(headless=True)
        active_drivers.append(thread_local.driver)
        
    if not hasattr(thread_local, "session"):
        thread_local.session = get_session()
        
    driver = thread_local.driver
    session = thread_local.session
    
    try:
        process_match(session, jogo['id'], jogo['url'], driver, jogo.get('ui_round_name'))
    except Exception as e:
        logging.error(f"❌ Erro crítico na thread ao processar o jogo {jogo['id']}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Crawler de Torneios/Partidas do SofaScore")
    parser.add_argument("--file", required=True, help="Caminho para o arquivo .txt com as URLs (uma por linha)")
    parser.add_argument("--workers", type=int, default=3, help="Número de partidas processadas em simultâneo")
    args = parser.parse_args()

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            urls = [linha.strip() for linha in f if linha.strip()]
    except Exception as e:
        logging.error(f"❌ Erro ao ler arquivo {args.file}: {e}")
        return

    logging.info(f"📄 Arquivo carregado com {len(urls)} URLs para processar.")

    driver_main = scrp.open_browser(headless=False)
    
    for url in urls:
        if "tournament" in url:
            logging.info(f"🚀 Iniciando Crawler para o Torneio: {url}")
            driver_main.get(url)
            time.sleep(2)
            
            logging.info("📂 Mapeando todas as rodadas e partidas...")
            lista_jogos = scrp.get_all_rounds_and_matches(driver_main)
            logging.info(f"🎯 Total de {len(lista_jogos)} partidas encontradas.")

            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                executor.map(worker_tarefa, lista_jogos)
            
            logging.info(f"🏁 Processamento do torneio finalizado!")
            
        elif "match" in url:
            jogo = {'id': url.split("#id:")[1], 'url': url}
            worker_tarefa(jogo)

    scrp.close_browser(driver_main)
    for driver in active_drivers:
        try:
            scrp.close_browser(driver)
        except:
            pass
            
    logging.info("✅ Todas as URLs do arquivo foram processadas e os navegadores fechados!")

if __name__ == '__main__':
    main()