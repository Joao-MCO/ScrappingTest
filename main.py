import traceback
import time
from database.process import process_match
import services.scrapping as scrp
from database.connection import init_db, get_session


def main():
    try:
        url = input("Cole aqui o link do torneio: ")
        print("🚀 Iniciando Crawler de Torneio...")
        init_db()
        session = get_session()
        
        driver = scrp.open_browser(headless=False)
        driver.get(url)
        time.sleep(5) 
        
        print("📂 Mapeando todas as rodadas e partidas...")
        lista_jogos = scrp.get_all_rounds_and_matches(driver)
        scrp.close_browser(driver)
        
        print(f"🎯 Total de {len(lista_jogos)} partidas encontradas.")

        for i, jogo in enumerate(lista_jogos):
            process_match(session, jogo['id'], jogo['url'])
            
            time.sleep(2)

        session.close()
        print("\n🏁 Processamento de torneio finalizado!")

    except Exception as e:
        print(f"\n❌ Erro crítico na main: {e}\n")
        traceback.print_exc()

if __name__ == '__main__':
    main()