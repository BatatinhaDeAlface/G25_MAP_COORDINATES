import asyncio
import pandas as pd
import os
from playwright.async_api import async_playwright

samples_file = "MAPG25_SAMPLES.txt"
target_sample = os.getenv("TARGET_SAMPLE", "")
target_coords = os.getenv("TARGET_COORDS", "")
output_csv = os.getenv("OUTPUT_CSV", "distancesG25.csv")

async def upload_file_safely(page, file_path):
    """Upload de arquivo com verificações de segurança e múltiplas tentativas"""
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        print(f"📁 Iniciando upload de: {file_path}")
        
        # Aguardar página carregar completamente
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)
        
        # MÉTODO 1: Tentativa padrão
        try:
            print("🔄 Tentativa 1: Upload padrão")
            locator = page.locator("input#localfiles")
            await locator.wait_for(state="attached", timeout=15000)
            
            # Forçar visibilidade via JavaScript ANTES de tentar
            await page.evaluate("""
                const input = document.querySelector('input#localfiles');
                if (input) {
                    input.style.display = 'block';
                    input.style.visibility = 'visible';
                    input.style.opacity = '1';
                    input.style.position = 'static';
                    input.removeAttribute('hidden');
                }
            """)
            
            await page.wait_for_timeout(1000)
            await locator.set_input_files(file_path, timeout=30000)
            print(f"✅ Upload realizado com sucesso (Método 1): {file_path}")
            return
            
        except Exception as e1:
            print(f"⚠️ Método 1 falhou: {e1}")
        
        # MÉTODO 2: Upload via JavaScript
        try:
            print("🔄 Tentativa 2: Upload via JavaScript")
            
            # Ler o arquivo
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Criar um blob e simular upload via JavaScript
            await page.evaluate(f"""
                const input = document.querySelector('input#localfiles');
                const file = new File([`{file_content}`], '{os.path.basename(file_path)}', {{
                    type: 'text/plain'
                }});
                
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                input.files = dataTransfer.files;
                
                // Disparar evento de mudança
                const event = new Event('change', {{ bubbles: true }});
                input.dispatchEvent(event);
            """)
            
            print(f"✅ Upload realizado com sucesso (Método 2): {file_path}")
            return
            
        except Exception as e2:
            print(f"⚠️ Método 2 falhou: {e2}")
        
        # MÉTODO 3: Forçar interação via coordenadas
        try:
            print("🔄 Tentativa 3: Upload por coordenadas")
            
            # Tornar elemento visível e obter posição
            await page.evaluate("""
                const input = document.querySelector('input#localfiles');
                input.style.position = 'fixed';
                input.style.top = '100px';
                input.style.left = '100px';
                input.style.width = '200px';
                input.style.height = '50px';
                input.style.display = 'block';
                input.style.visibility = 'visible';
                input.style.opacity = '1';
                input.style.zIndex = '9999';
            """)
            
            await page.wait_for_timeout(1000)
            
            # Usar set_input_files em coordenadas específicas
            await page.set_input_files("input#localfiles", file_path)
            print(f"✅ Upload realizado com sucesso (Método 3): {file_path}")
            return
            
        except Exception as e3:
            print(f"⚠️ Método 3 falhou: {e3}")
            
        # Se todos os métodos falharam
        raise Exception("Todos os métodos de upload falharam")
        
    except Exception as final_error:
        print(f"💥 ERRO CRÍTICO no upload: {final_error}")
        # Screenshot para debug
        await page.screenshot(path="upload_error.png")
        print("📸 Screenshot salvo como 'upload_error.png'")
        raise

async def wait_for_button_and_click(page, selector, description="", timeout=30000):
    """Aguardar botão estar disponível e clicar com logs"""
    try:
        print(f"🔍 Procurando por: {description or selector}")
        button = await page.wait_for_selector(selector, state="visible", timeout=timeout)
        await button.scroll_into_view_if_needed()
        await button.click()
        print(f"✅ Clicado: {description or selector}")
        return button
    except Exception as e:
        print(f"❌ Erro ao clicar em {description or selector}: {e}")
        raise

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("🌐 Navegando para vahaduo...")
            await page.goto("https://vahaduo.github.io/vahaduo/", wait_until="networkidle")
            
            # 1️⃣ Upload do ficheiro Source com verificações
            print("📁 Fazendo upload do arquivo...")
            await upload_file_safely(page, samples_file)
            await page.wait_for_timeout(2000)  # Tempo para processar o upload
            
            # 2️⃣ Clicar no botão do ficheiro carregado
            print("🔘 Clicando no arquivo carregado...")
            await wait_for_button_and_click(
                page, 
                "button:has-text('MAPG25 SAMPLES')", 
                "Arquivo MAPG25 SAMPLES",
                timeout=60000
            )
            await page.wait_for_timeout(1000)
            
            # 3️⃣ Clicar no segundo botão 'source'
            print("🔘 Selecionando source...")
            buttons_source = page.locator("button:has-text('source')")
            await buttons_source.nth(1).wait_for(state="visible", timeout=30000)
            await buttons_source.nth(1).scroll_into_view_if_needed()
            await buttons_source.nth(1).click()
            print("✅ Source selecionado")
            await page.wait_for_timeout(500)
            
            # 4️⃣ Clicar no primeiro botão Target
            print("🎯 Abrindo aba Target...")
            button_target = page.locator("button:has-text('target')").nth(0)
            await button_target.wait_for(state="visible", timeout=30000)
            await button_target.click()
            print("✅ Aba Target aberta")
            
            # 5️⃣ Preencher textarea Target
            print("✏️ Preenchendo dados do target...")
            target_textarea = await page.wait_for_selector("textarea#target", state="visible", timeout=30000)
            target_data = f"{target_sample},{target_coords}"
            await target_textarea.fill(target_data)
            print(f"✅ Target preenchido: {target_data}")
            
            # 6️⃣ Clicar no botão 'distance'
            print("📏 Iniciando cálculo de distância...")
            button_distance = page.locator("button:has-text('distance')").nth(0)
            await button_distance.wait_for(state="visible", timeout=30000)
            await button_distance.click()
            print("✅ Cálculo iniciado")
            await page.wait_for_timeout(1000)
            
            # 7️⃣ Definir valor do distmaxout
            print("⚙️ Configurando distância máxima...")
            dist_input = page.locator("input#distmaxout")
            await dist_input.wait_for(state="visible", timeout=30000)
            await dist_input.fill("400")
            print("✅ Distância máxima definida: 400")
            await page.wait_for_timeout(500)
            
            # 8️⃣ Clicar no botão da amostra Target
            print(f"🎯 Clicando na amostra target: {target_sample}")
            button_target_sample = page.locator(f"button:has-text('{target_sample}')").nth(0)
            await button_target_sample.wait_for(state="visible", timeout=30000)
            await button_target_sample.scroll_into_view_if_needed()
            await button_target_sample.click()
            print("✅ Comparação iniciada")
            
            # 9️⃣ Aguardar resultados e extrair dados
            print("⏳ Aguardando resultados...")
            await page.wait_for_selector("#distanceoutput", state="visible", timeout=120000)
            
            print("📊 Extraindo dados da tabela...")
            cells = page.locator("#distanceoutput td")
            n = await cells.count()
            results = []
            
            # Percorrer de 2 em 2: [Distance, Population]
            for i in range(0, n, 2):
                dist = await cells.nth(i).inner_text()
                pop = await cells.nth(i+1).inner_text()
                results.append((dist, pop))
            
            print(f"✅ {len(results)} resultados extraídos")
            
            # 🔟 Salvar em CSV
            print("💾 Salvando resultados...")
            df = pd.DataFrame(results, columns=["Distance", "Population"])
            df.to_csv(output_csv, index=False)
            print(f"✅ Arquivo '{output_csv}' criado com sucesso!")
            print(f"📈 Total de registros: {len(df)}")
            
        except Exception as e:
            print(f"💥 Erro durante execução: {e}")
            # Tirar screenshot para debug
            await page.screenshot(path="error_screenshot.png")
            print("📸 Screenshot salvo como 'error_screenshot.png'")
            raise
            
        finally:
            await browser.close()
            print("🔚 Navegador fechado")

if __name__ == "__main__":
    # Verificações iniciais
    if not target_sample:
        print("⚠️  Aviso: TARGET_SAMPLE não definido")
    if not target_coords:
        print("⚠️  Aviso: TARGET_COORDS não definido")
    
    print("🚀 Iniciando processo...")
    asyncio.run(main())
