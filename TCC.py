import random
import string

# --- VARIÁVEIS DO SISTEMA ---
banco_de_usuarios = {
    "admin": "senha",
    "caio": "caio123"
}
registro_de_falhas = {}
LIMITE_DE_ERROS = 2
historico_logins = [] 

# FUNÇÃO GERADORA DE SENHA 
def gerar_senha_forte(tamanho=8):
    caracteres = string.ascii_letters + string.digits + string.punctuation
    senha_sorteada = random.choices(caracteres, k=tamanho)
    return "".join(senha_sorteada)

# PROGRAMA PRINCIPAL 
print("=== SISTEMA INTEGRADO DE SEGURANÇA ===")

while True:
    print("\nO que você deseja fazer?")
    print("[1] Fazer Login")
    print("[2] Criar Nova Conta")
    print("[3] Painel Admin (Histórico de Logins)")
    print("[4] Sair")
    
    opcao = input("Escolha uma opção (1, 2, 3 ou 4): ").strip()
    
    # OPÇÃO 1: FAZER LOGIN
    if opcao == '1':
        print("\n--- Painel de Login ---")
        usuario = input("Digite o Usuário: ").strip().lower()
        
        erros_atuais = registro_de_falhas.get(usuario, 0)
        
        if erros_atuais >= LIMITE_DE_ERROS:
            print(f" ALERTA: A conta '{usuario}' está BLOQUEADA por excesso de tentativas!")
            continue 
            
        senha = input("Digite a Senha: ")
        
        if usuario in banco_de_usuarios and banco_de_usuarios[usuario] == senha:
            print(f" Acesso Permitido. Bem-vindo(a), {usuario}!")
            registro_de_falhas[usuario] = 0 
            historico_logins.append(usuario)
            
        else:
            registro_de_falhas[usuario] = erros_atuais + 1
            tentativas_restantes = LIMITE_DE_ERROS - registro_de_falhas[usuario]
            
            print(" Acesso Negado: Usuário ou senha incorretos.")
            
            if tentativas_restantes > 0:
                print(f" Você tem apenas mais {tentativas_restantes} tentativa(s).")
            else:
                print(f" CONTA BLOQUEADA: Limite atingido para '{usuario}'.")

    # OPÇÃO 2: CRIAR NOVA CONTA
    elif opcao == '2':
        print("\n--- Cadastro de Novo Usuário ---")
        novo_usuario = input("Digite um nome de usuário: ").strip().lower()
        
        if novo_usuario in banco_de_usuarios:
            print("  Erro: Esse usuário já existe! Tente outro nome.")
        else:
            nova_senha = gerar_senha_forte(16)
            banco_de_usuarios[novo_usuario] = nova_senha
            print(f"  Conta criada com sucesso!")
            print(f"Sua senha gerada automaticamente é: {nova_senha}")
            print("Guarde-a em um local seguro!")

    
    # OPÇÃO 3: PAINEL ADMIN
    elif opcao == '3':
        print("\n--- Acesso Restrito: Painel Admin ---")
        senha_admin = input("Digite a senha do administrador: ")
        
        if banco_de_usuarios.get("admin") == senha_admin:
            print("\n=== Últimos Logins Bem-sucedidos ===")
            
            if len(historico_logins) == 0:
                print("Nenhum login registrado nesta sessão.")
            else:
                for i, nome in enumerate(historico_logins, 1):
                    print(f"{i}º - {nome}")
            print("====================================")
        else:
            print("  Acesso Negado: Senha de administrador incorreta!")

    
    # OPÇÃO 4: SAIR
    elif opcao == '4':
        print("Encerrando o sistema. Até mais!")
        break
                
    # OPÇÃO INVÁLIDA
    else:
        print("  Opção inválida. Por favor, digite 1, 2, 3 ou 4.")
