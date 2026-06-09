from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def sincronizar_hora_via_web(ip, usuario, senha):
    print(f"\n[*] Iniciando Robô Web para o IP {ip}...")
    
    # Configura o navegador (usando Chrome)
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # <- Descomente isso no futuro para o navegador rodar "invisível"
    options.add_argument('--ignore-certificate-errors') # Ignora erros de "Site não seguro"
    
    # Instala/Acha o ChromeDriver automaticamente
    servico = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servico, options=options)
    
    try:
        driver.get(f"http://{ip}")
        wait = WebDriverWait(driver, 10) # Tempo máximo de espera para a página carregar
        
        # =================================================================
        # ATENÇÃO: Os IDs ('id_do_usuario', 'id_da_senha', etc.) abaixo 
        # SÃO EXEMPLOS! Você precisa trocá-los pelos reais da sua câmera.
        # =================================================================
        
        # --- PASSO 1: FAZER LOGIN ---
        print("[*] Preenchendo login...")
        campo_usuario = wait.until(EC.presence_of_element_located((By.ID, "id_do_usuario")))
        campo_senha = driver.find_element(By.ID, "id_da_senha")
        botao_login = driver.find_element(By.ID, "id_do_botao_login")
        
        campo_usuario.send_keys(usuario)
        campo_senha.send_keys(senha)
        botao_login.click()
        
        # --- PASSO 2: NAVEGAR ATÉ A TELA DE HORÁRIO ---
        print("[*] Navegando até as configurações...")
        # Exemplo: Clicar na aba "Configurações"
        aba_config = wait.until(EC.element_to_be_clickable((By.ID, "id_aba_configuracoes")))
        aba_config.click()
        
        # Exemplo: Clicar no menu "Sistema" -> "Data e Hora"
        menu_hora = wait.until(EC.element_to_be_clickable((By.ID, "id_menu_data_hora")))
        menu_hora.click()
        
        # --- PASSO 3: CLICAR EM SINCRONIZAR E SALVAR ---
        print("[*] Sincronizando horário...")
        btn_sincronizar = wait.until(EC.element_to_be_clickable((By.ID, "id_btn_sincronizar_pc")))
        btn_sincronizar.click()
        
        btn_salvar = driver.find_element(By.ID, "id_btn_salvar")
        btn_salvar.click()
        
        print("[OK] Horário sincronizado com sucesso pelo Robô!")
        time.sleep(3) # Dá um tempinho para a câmera salvar antes de fechar
        return True
        
    except Exception as e:
        print(f"[!] Erro no Robô Web: {e}")
        return False
        
    finally:
        driver.quit() # Fecha o navegador sempre, mesmo se der erro