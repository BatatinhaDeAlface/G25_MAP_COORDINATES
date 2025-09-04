import asyncio
import pandas as pd
import os
from playwright.async_api import async_playwright

samples_file = r"C:/Users/ilhas/Downloads/MAPG25_SAMPLES.txt"
target_sample = os.getenv("TARGET_SAMPLE", "")
target_coords = os.getenv("TARGET_COORDS", "")
output_csv    = os.getenv("OUTPUT_CSV", "distancesG25.csv")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://vahaduo.github.io/vahaduo/")

        # 1️⃣ Upload do ficheiro Source
        await page.locator("input#localfiles").set_input_files(samples_file)
        await page.wait_for_timeout(1000)  # esperar o upload

        # 2️⃣ Clicar no botão do ficheiro carregado (MAPG25 SAMPLES)
        button_file = await page.wait_for_selector("button:has-text('MAPG25 SAMPLES')", timeout=60000)
        await button_file.click()
        await page.wait_for_timeout(500)

      # Criar o locator para todos os botões 'source'
        buttons_source = page.locator("button:has-text('source')")

        # Esperar o segundo botão estar visível e clicar
        await buttons_source.nth(1).wait_for(state="visible")
        await buttons_source.nth(1).click()


       # 1️⃣ Clicar no primeiro botão Target para abrir a aba
        button_target = page.locator("button:has-text('target')").nth(0)
        await button_target.click()

        # 2️⃣ Esperar o textarea Target estar visível
        target_textarea = await page.wait_for_selector("textarea#target", state="visible")

        # 3️⃣ Inserir os dados
        await target_textarea.fill(f"{target_sample},{target_coords}")


        # 1️⃣ Clicar no botão 'distance' para iniciar o cálculo
        button_distance = page.locator("button:has-text('distance')").nth(0)
        await button_distance.click()
        await page.wait_for_timeout(500)  # esperar o cálculo inicial ou ativação do input

        # 2️⃣ Definir o value do distmaxout para 400
        dist_input = page.locator("input#distmaxout")
        await dist_input.fill("400")
        await page.wait_for_timeout(200)

        # 3️⃣ Clicar no botão da amostra Target para iniciar a comparação
        # Localiza todos os botões com o texto do Target
        button_target_sample = page.locator(f"button:has-text('{target_sample}')").nth(0)

        # Espera ele ficar visível
        await button_target_sample.wait_for(state="visible")

        # Clica no botão
        await button_target_sample.click()

        # Esperar que os resultados estejam visíveis
        await page.wait_for_selector("#distanceoutput", state="visible", timeout=60000)

        # Depois capturar os <td> dentro da tabela
        cells = page.locator("#distanceoutput td")
        n = await cells.count()
        results = []

        # Percorrer de 2 em 2: [Distance, Population]
        for i in range(0, n, 2):
            dist = await cells.nth(i).inner_text()
            pop = await cells.nth(i+1).inner_text()
            results.append((dist, pop))

        # Salvar em CSV
        df = pd.DataFrame(results, columns=["Distance","Population"])
        df.to_csv(output_csv, index=False)
        print(f"Arquivo '{output_csv}' criado com sucesso!")

        await browser.close()

asyncio.run(main())


